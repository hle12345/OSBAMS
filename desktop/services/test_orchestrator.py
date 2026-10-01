"""
services/test_orchestrator.py — the Rev.2 test orchestrator.

Capacity test:
    PROFILE -> OCV -> READY -> controlled CC DISCHARGE (live V/I/P/T, Ah/Wh)
            -> profile CUTOFF -> LOAD OFF (verified) -> RECOVERY -> COMPLETE
DCIR test (separate, controlled current steps):
    PROFILE -> OCV -> READY -> STEP(I1) -> STEP(I2) ... -> LOAD OFF -> RECOVERY -> COMPLETE

Push-based: feed `Sample`s from any source (STM32/INA228 serial frames,
Simulator6060B, a manual bench) into `on_sample()`. All timing comes from
sample timestamps, so runs are deterministic and fast in simulation.

Invariants (hard — breach => load OFF + FAULT):
  * commanded_current x conservative_pack_voltage <= 300 W
  * conservative voltage = max(OCV, highest voltage seen); it NEVER decreases,
    so sagging loaded voltage cannot be used to raise current mid-test
  * commanded current is fixed at READY and never raised during the run
  * commanded <= min(profile, OSBAMS ceiling, 60 A, 300 W / V, component limits)
  * load-off is confirmed from measured current, never assumed
A manual 6060B cannot be commanded: the orchestrator prompts the operator and
verifies from measurements. This module does not claim BENCH_TESTED.
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from equipment import capability as cap
from services.battery_profiles import BatteryProfile


class Phase(str, Enum):
    IDLE = "IDLE"
    PROFILE = "PROFILE"
    OCV = "OCV"
    READY = "READY"
    DISCHARGE = "DISCHARGE"
    DCIR_STEP = "DCIR_STEP"
    LOAD_OFF = "LOAD_OFF"
    RECOVERY = "RECOVERY"
    COMPLETE = "COMPLETE"
    FAULT = "FAULT"
    ABORTED = "ABORTED"


TERMINAL = (Phase.COMPLETE, Phase.FAULT, Phase.ABORTED)


@dataclass
class Sample:
    t_s: float
    voltage_v: float
    current_a: float
    temp_c: Optional[float] = None
    fault: bool = False                 # sensor/firmware fault flag

    @property
    def power_w(self) -> float:
        return self.voltage_v * self.current_a


@dataclass
class RunConfig:
    idle_current_a: float = 0.05        # |I| below this counts as "no load"
    ocv_window_s: float = 10.0          # rest window averaged into OCV
    ocv_min_samples: int = 5
    ocv_stable_v: float = 0.05          # max V spread inside the window
    ocv_timeout_s: float = 600.0
    current_tol_frac: float = 0.10      # measured vs commanded
    current_tol_abs_a: float = 0.05
    start_timeout_s: float = 120.0      # load must appear after confirm()
    settle_s: float = 5.0               # ignore regulation errors this long
    cutoff_debounce: int = 3            # consecutive samples <= cutoff
    sample_gap_s: float = 10.0          # comm-loss fault while load is on
    off_current_a: float = 0.10         # load-off verification threshold
    off_samples: int = 3
    off_timeout_s: float = 30.0
    recovery_s: float = 300.0
    recovery_marks_s: tuple = (30.0, 120.0)   # V recorded at these times
    max_duration_s: Optional[float] = None    # default: 8 h
    # DCIR
    dcir_steps_a: Optional[tuple] = None      # default: 50 % and 100 % of recommended
    dcir_step_s: float = 10.0
    dcir_avg_s: float = 2.0
    dcir_rest_between_s: float = 0.0


@dataclass
class Results:
    kind: str
    phase: str
    stop_reason: str = ""
    ocv_v: Optional[float] = None
    conservative_voltage_v: Optional[float] = None
    commanded_current_a: Optional[float] = None
    permitted_current_a: Optional[float] = None
    limiting_factor: str = ""
    capacity_ah: float = 0.0
    energy_wh: float = 0.0
    duration_s: float = 0.0
    avg_current_a: float = 0.0
    avg_power_w: float = 0.0
    v_min: Optional[float] = None
    v_end: Optional[float] = None
    max_temp_c: Optional[float] = None
    initial_sag_v: Optional[float] = None
    recovery_v: dict = field(default_factory=dict)      # {seconds: volts}
    soh_capacity: Optional[float] = None
    dcir_steps: list = field(default_factory=list)      # dicts
    dcir_mohm: Optional[float] = None
    n_samples: int = 0
    events: list = field(default_factory=list)


class _Run:
    kind = "base"

    def __init__(self, profile: BatteryProfile, load, config: Optional[RunConfig] = None,
                 prompt: Optional[Callable[[str], None]] = None,
                 requested_current_a: Optional[float] = None):
        self.profile, self.load = profile, load
        self.cfg = config or RunConfig()
        self.prompt = prompt or (lambda msg: None)
        self.requested_current_a = requested_current_a
        self.phase = Phase.IDLE
        self.events: list = []
        self.samples: list = []              # (t, v, i, temp, phase)
        self.vcons = cap.ConservativeVoltage()
        self.ocv_v: Optional[float] = None
        self.commanded_a: Optional[float] = None
        self.permitted: Optional[cap.CurrentLimit] = None
        self.stop_reason = ""
        self._ocv_buf: list = []
        self._ocv_t0: Optional[float] = None
        self._last_t: Optional[float] = None
        self._load_enabled = False
        self._off_ok = 0
        self._off_t0: Optional[float] = None
        self._after_off = Phase.RECOVERY
        self._rec_t0: Optional[float] = None
        self._rec: dict = {}
        self._t0: Optional[float] = None     # start of loaded phase
        self._ah = self._wh = 0.0
        self._prev: Optional[Sample] = None
        self._v_min: Optional[float] = None
        self._t_max: Optional[float] = None
        self._first_loaded_v: Optional[float] = None
        self._duration = 0.0
        self._confirm_t: Optional[float] = None

    # ── public API ──────────────────────────────────────────────────────
    @property
    def done(self) -> bool:
        return self.phase in TERMINAL

    def log(self, msg: str) -> None:
        self.events.append((self._last_t, self.phase.value, msg))

    def start(self) -> Phase:
        self.phase = Phase.PROFILE
        problems = self.profile.validate()
        if problems:
            return self._fault("profile invalid: " + "; ".join(problems))
        if not self.load.connect():
            return self._fault("load connect failed")
        self.log(f"profile {self.profile.key} OK; load {self.load.name}")
        self.phase = Phase.OCV
        return self.phase

    def abort(self, reason: str = "operator abort") -> Phase:
        if self.done:
            return self.phase
        self.stop_reason = reason
        self._off_sequence(Phase.ABORTED)
        return self.phase

    def confirm(self) -> Phase:
        """Operator/UI go-ahead in READY."""
        if self.phase is not Phase.READY:
            return self.phase
        self._confirm_t = self._last_t
        self._begin_load()
        return self.phase

    def tick(self, now_s: float) -> Phase:
        """Heartbeat for comm-loss detection when no samples are arriving."""
        if self.phase in (Phase.DISCHARGE, Phase.DCIR_STEP) and self._last_t is not None \
                and now_s - self._last_t > self.cfg.sample_gap_s:
            self._fault(f"no samples for {now_s - self._last_t:.0f} s (communication loss)")
        return self.phase

    def on_sample(self, s: Sample) -> Phase:
        if self.done or self.phase in (Phase.IDLE, Phase.PROFILE):
            return self.phase
        gap = None if self._last_t is None else s.t_s - self._last_t
        if gap is not None and gap < 0:
            return self._fault("sample time went backwards")
        self._last_t = s.t_s
        if gap is not None and gap > self.cfg.sample_gap_s and \
                self.phase in (Phase.DISCHARGE, Phase.DCIR_STEP):
            return self._fault(f"sample gap {gap:.0f} s while loaded")
        self.samples.append((s.t_s, s.voltage_v, s.current_a, s.temp_c, self.phase.value))
        if s.temp_c is not None:
            self._t_max = s.temp_c if self._t_max is None else max(self._t_max, s.temp_c)

        if self.phase not in (Phase.LOAD_OFF, Phase.RECOVERY):
            reason = self._safety(s)        # load is off in the last two phases
            if reason:
                return self._fault(reason)
        h = {Phase.OCV: self._on_ocv, Phase.READY: self._on_ready,
             Phase.DISCHARGE: self._on_loaded, Phase.DCIR_STEP: self._on_loaded,
             Phase.LOAD_OFF: self._on_off, Phase.RECOVERY: self._on_recovery}[self.phase]
        h(s)
        return self.phase

    # ── safety ──────────────────────────────────────────────────────────
    def _loaded(self) -> bool:
        return self.phase in (Phase.DISCHARGE, Phase.DCIR_STEP)

    def _safety(self, s: Sample) -> Optional[str]:
        import config
        if s.fault:
            return "sensor/firmware fault flag"
        t_lim = min(self.profile.temp_max_c, config.SAFETY_MAX_TEMP_C)
        if s.temp_c is not None and s.temp_c >= t_lim:
            return f"over-temperature {s.temp_c:.1f} C >= {t_lim:.0f} C"
        if s.voltage_v > self.profile.maximum_voltage_v + 1.0:
            return f"over-voltage {s.voltage_v:.2f} V (profile max {self.profile.maximum_voltage_v} V)"
        if self.phase is not Phase.LOAD_OFF:
            self.vcons.update(s.voltage_v)           # monotone: sag never lowers it
        if self._loaded() and self.commanded_a is not None:
            peak = self._commanded_peak()
            try:
                cap.assert_power_invariant(peak, self.vcons.volts)
            except cap.InvariantViolation as e:
                return f"power invariant: {e}"
            if abs(s.current_a) > peak * 1.15 + 0.1:
                return f"measured {s.current_a:.2f} A above commanded {peak:.2f} A"
            if s.voltage_v * abs(s.current_a) > cap.INSTRUMENT_POWER_MAX_W:
                return f"measured power {s.voltage_v * abs(s.current_a):.0f} W > 300 W"
        return None

    def _commanded_peak(self) -> float:
        return self.commanded_a or 0.0

    # ── OCV / READY ─────────────────────────────────────────────────────
    def _on_ocv(self, s: Sample) -> None:
        if abs(s.current_a) > self.cfg.idle_current_a:
            self._ocv_buf.clear(); self._ocv_t0 = None
            if abs(s.current_a) > 0.5:
                self._fault(f"{s.current_a:.2f} A flowing before test start")
            return
        if self._ocv_t0 is None:
            self._ocv_t0 = s.t_s
        self._ocv_buf.append((s.t_s, s.voltage_v))
        self._ocv_buf = [(t, v) for t, v in self._ocv_buf if s.t_s - t <= self.cfg.ocv_window_s]
        span = self._ocv_buf[-1][0] - self._ocv_buf[0][0]
        vs = [v for _, v in self._ocv_buf]
        if span >= self.cfg.ocv_window_s * 0.9 and len(vs) >= self.cfg.ocv_min_samples \
                and max(vs) - min(vs) <= self.cfg.ocv_stable_v:
            self.ocv_v = sum(vs) / len(vs)
            self._plan()
        elif s.t_s - self._ocv_t0 > self.cfg.ocv_timeout_s:
            self._fault("OCV did not stabilise")

    def _plan(self) -> None:
        p, ocv = self.profile, self.ocv_v
        self.log(f"OCV = {ocv:.3f} V")
        if ocv <= p.cutoff_voltage_v:
            self._fault(f"OCV {ocv:.2f} V at/below profile cutoff {p.cutoff_voltage_v} V — charge first")
            return
        if ocv > p.maximum_voltage_v + 0.5:
            self._fault(f"OCV {ocv:.2f} V above profile maximum {p.maximum_voltage_v} V")
            return
        self.vcons.update(ocv)
        self.permitted = cap.compute_permitted_current(
            self.vcons.volts, p.maximum_osbams_test_current_a)
        self.log("permitted: " + " | ".join(f"{k}: {v}" for k, v in self.permitted.rows()[:6]))
        self.load.set_pack_voltage(self.vcons.volts)   # before any load command
        try:
            self._plan_current()
        except cap.EnvelopeViolation as e:
            self._fault(f"refused by envelope: {e}")
            return
        self.phase = Phase.READY
        self.log(f"READY — commanded {self.commanded_a:.3f} A at <= {self.vcons.volts:.2f} V "
                 f"({self.commanded_a * self.vcons.volts:.1f} W)")
        self.prompt(f"READY: {self.commanded_a:.2f} A CC. Confirm to enable the load.")

    def _plan_current(self) -> None:
        raise NotImplementedError

    def _check_current(self, amps: float) -> None:
        """Hard gate for any current this run will ever command."""
        cap.assert_power_invariant(amps, self.vcons.volts)
        cap.check_load_command(self.vcons.volts, amps, None,
                               self.profile.maximum_osbams_test_current_a)

    def _on_ready(self, s: Sample) -> None:
        if not self.load.is_controllable and abs(s.current_a) > 0.25 * self.commanded_a:
            self.log("operator enabled the load before confirm()")
            self._confirm_t = s.t_s
            self._enter_loaded(s)

    def _begin_load(self) -> None:
        raise NotImplementedError

    def _enter_loaded(self, s: Optional[Sample] = None) -> None:
        raise NotImplementedError

    def _on_loaded(self, s: Sample) -> None:
        raise NotImplementedError

    # ── load off (verified from measurement) ────────────────────────────
    def _off_sequence(self, after: Phase) -> None:
        self._after_off = after
        self._off_ok, self._off_t0 = 0, self._last_t
        ok = False
        try:
            ok = self.load.input_off()
        except Exception as e:                       # blocked remote op etc.
            self.log(f"input_off raised: {e}")
        if not ok:
            self.prompt("*** DISABLE THE LOAD INPUT NOW ***")
        self.log("load OFF commanded; verifying from measured current")
        self.phase = Phase.LOAD_OFF

    def _on_off(self, s: Sample) -> None:
        if abs(s.current_a) <= self.cfg.off_current_a:
            self._off_ok += 1
        else:
            self._off_ok = 0
        if self._off_ok >= self.cfg.off_samples:
            self._load_enabled = False
            self._off_t0 = None
            self.log("load OFF confirmed by measurement")
            if self._after_off is Phase.RECOVERY:
                self.phase, self._rec_t0 = Phase.RECOVERY, s.t_s
                self.log(f"recovery rest started ({self.cfg.recovery_s:.0f} s)")
            else:
                self.phase = self._after_off
        elif self._off_t0 is not None and s.t_s - self._off_t0 > self.cfg.off_timeout_s:
            self.stop_reason += " | LOAD-OFF NOT CONFIRMED"
            self.phase = Phase.FAULT
            self.prompt("LOAD STILL DRAWING CURRENT — use E-stop / disconnect")

    def _on_recovery(self, s: Sample) -> None:
        dt = s.t_s - self._rec_t0
        for m in self.cfg.recovery_marks_s:
            if dt >= m and m not in self._rec and m < self.cfg.recovery_s:
                self._rec[m] = s.voltage_v
        if dt >= self.cfg.recovery_s:
            self._rec[self.cfg.recovery_s] = s.voltage_v
            self.phase = Phase.COMPLETE
            self.log("COMPLETE")

    def _fault(self, reason: str) -> Phase:
        if self.done or self.phase is Phase.LOAD_OFF:
            return self.phase
        self.stop_reason = reason
        self.log(f"FAULT: {reason}")
        if self._load_enabled or self.phase in (Phase.DISCHARGE, Phase.DCIR_STEP, Phase.READY):
            self._off_sequence(Phase.FAULT)
        else:
            self.phase = Phase.FAULT
        return self.phase

    # ── integration helper ──────────────────────────────────────────────
    def _integrate(self, s: Sample) -> None:
        if self._prev is not None:
            dt = s.t_s - self._prev.t_s
            self._ah += 0.5 * (abs(s.current_a) + abs(self._prev.current_a)) * dt / 3600.0
            self._wh += 0.5 * (abs(s.power_w) + abs(self._prev.power_w)) * dt / 3600.0
        self._prev = s
        self._v_min = s.voltage_v if self._v_min is None else min(self._v_min, s.voltage_v)

    def _results(self) -> Results:
        d = self._duration
        r = Results(kind=self.kind, phase=self.phase.value, stop_reason=self.stop_reason,
                    ocv_v=self.ocv_v, conservative_voltage_v=self.vcons.volts,
                    commanded_current_a=self.commanded_a,
                    permitted_current_a=None if self.permitted is None else self.permitted.final_a,
                    limiting_factor="" if self.permitted is None else self.permitted.limiting_factor,
                    capacity_ah=self._ah, energy_wh=self._wh, duration_s=d,
                    avg_current_a=(self._ah * 3600 / d) if d > 0 else 0.0,
                    avg_power_w=(self._wh * 3600 / d) if d > 0 else 0.0,
                    v_min=self._v_min, v_end=self._prev.voltage_v if self._prev else None,
                    max_temp_c=self._t_max, recovery_v=dict(self._rec),
                    n_samples=len(self.samples), events=list(self.events))
        if self.ocv_v is not None and self._first_loaded_v is not None:
            r.initial_sag_v = self.ocv_v - self._first_loaded_v
        return r

    def results(self) -> Results:
        return self._results()


class CapacityTest(_Run):
    """Controlled constant-current discharge to the profile cutoff."""
    kind = "capacity"

    def _plan_current(self) -> None:
        p = self.profile
        i = self.requested_current_a if self.requested_current_a is not None else \
            min(p.recommended_test_current_a, self.permitted.final_a)
        self._check_current(i)                       # refuses, never silently clamps an explicit request
        self.commanded_a = i
        self.load.set_cc(i)

    def _begin_load(self) -> None:
        if self.load.is_controllable:
            if not self.load.input_on():
                return self._fault("load input_on failed")
            self._load_enabled = True
            self.phase = Phase.DISCHARGE
            self.log("load ON (CC)")
        else:
            self.prompt(f"Enable the load input now ({self.commanded_a:.2f} A CC).")
            self.phase = Phase.DISCHARGE         # waits for current to appear
            self._load_enabled = True            # assume live until proven off

    def _enter_loaded(self, s=None) -> None:
        self._load_enabled = True
        self.phase = Phase.DISCHARGE

    def _on_loaded(self, s: Sample) -> None:
        c = self.cfg
        if self._t0 is None:                          # waiting for current to appear
            if abs(s.current_a) >= 0.5 * self.commanded_a:
                self._t0 = s.t_s
                self._first_loaded_v = s.voltage_v
                self._prev = None
                self._low = 0
                self._integrate(s)
                self.log(f"load detected: {s.current_a:.2f} A")
            elif self._confirm_t is not None and s.t_s - self._confirm_t > c.start_timeout_s:
                self._fault("load current never appeared after confirm")
            return
        self._duration = s.t_s - self._t0
        self._integrate(s)
        if s.t_s - self._t0 > c.settle_s:
            tol = max(c.current_tol_abs_a, c.current_tol_frac * self.commanded_a)
            if abs(abs(s.current_a) - self.commanded_a) > tol:
                self._fault(f"current {s.current_a:.2f} A off setpoint {self.commanded_a:.2f} A")
                return
        self._low = getattr(self, "_low", 0) + 1 if s.voltage_v <= self.profile.cutoff_voltage_v else 0
        if self._low >= c.cutoff_debounce:
            self.stop_reason = f"profile cutoff {self.profile.cutoff_voltage_v} V"
            self.log(self.stop_reason)
            self._off_sequence(Phase.RECOVERY)
            return
        limit = c.max_duration_s or 8 * 3600.0
        if self._duration > limit:
            self.stop_reason = "max duration"
            self._off_sequence(Phase.RECOVERY)

    def results(self) -> Results:
        r = self._results()
        r.soh_capacity = r.capacity_ah / self.profile.rated_ah if self.profile.rated_ah else None
        return r


class DcirTest(_Run):
    """Controlled current steps; R_DC = dV / dI between successive steady points."""
    kind = "dcir"

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._plan_steps: list = []
        self._step_idx = -1
        self._step_t0: Optional[float] = None
        self._step_buf: list = []
        self._ref_v: Optional[float] = None       # voltage at previous steady point
        self._ref_i = 0.0
        self.steps: list = []
        self._arm_t: Optional[float] = None

    def _plan_current(self) -> None:
        p = self.profile
        steps = self.cfg.dcir_steps_a
        if steps is None:
            base = min(p.recommended_test_current_a, self.permitted.final_a)
            steps = (round(base * 0.5, 3), round(base, 3))
        steps = tuple(float(x) for x in steps)
        if any(b <= a for a, b in zip(steps, steps[1:])) or steps[0] <= 0:
            raise cap.EnvelopeViolation("DCIR steps must be positive and increasing")
        for i in steps:
            self._check_current(i)                   # every step gated up front
        self._plan_steps = list(steps)
        self.commanded_a = max(steps)                # peak — used by invariant

    def _commanded_peak(self) -> float:
        return self.commanded_a or 0.0

    def _begin_load(self) -> None:
        self._load_enabled = True
        self._enter_step(0)
        if self.load.is_controllable:
            if not self.load.input_on():
                return self._fault("load input_on failed")
        else:
            self.prompt(f"Enable the load input ({self._plan_steps[0]:.2f} A CC).")

    def _enter_loaded(self, s=None) -> None:
        self._load_enabled = True
        if self._step_idx < 0:
            self._enter_step(0)

    def _enter_step(self, k: int) -> None:
        i = self._plan_steps[k]
        self._check_current(i)
        self.load.set_pack_voltage(self.vcons.volts)
        self.load.set_cc(i)
        if k > 0 and not self.load.is_controllable:
            self.prompt(f"Set the load to {i:.2f} A CC.")
        self._step_idx, self._step_t0, self._step_buf, self._arm_t = k, None, [], self._last_t
        self.phase = Phase.DCIR_STEP
        self.log(f"DCIR step {k + 1}/{len(self._plan_steps)}: {i:.3f} A")

    def _on_loaded(self, s: Sample) -> None:
        c, k = self.cfg, self._step_idx
        target = self._plan_steps[k]
        tol = max(c.current_tol_abs_a, c.current_tol_frac * target)
        in_tol = abs(abs(s.current_a) - target) <= tol
        if self._step_t0 is None:
            if in_tol:
                self._step_t0 = s.t_s
                if self._t0 is None:
                    self._t0 = s.t_s
                if self._ref_v is None:
                    # pre-step rest voltage: mean of the OCV window
                    self._ref_v, self._ref_i = self.ocv_v, 0.0
                    self._first_loaded_v = s.voltage_v
            elif self._arm_t is not None and s.t_s - self._arm_t > c.start_timeout_s:
                self._fault(f"step {k + 1} current never reached {target:.2f} A")
            return
        self._duration = s.t_s - self._t0
        self._integrate(s)
        if not in_tol and s.t_s - self._step_t0 > c.settle_s:
            self._fault(f"current {s.current_a:.2f} A off step setpoint {target:.2f} A")
            return
        self._step_buf = [(t, v, i) for t, v, i in self._step_buf if s.t_s - t <= c.dcir_avg_s]
        self._step_buf.append((s.t_s, s.voltage_v, s.current_a))
        if s.voltage_v <= self.profile.cutoff_voltage_v:
            self.stop_reason = "profile cutoff during DCIR"
            self._off_sequence(Phase.RECOVERY)
            return
        if s.t_s - self._step_t0 >= c.dcir_step_s:
            v = sum(b[1] for b in self._step_buf) / len(self._step_buf)
            i = sum(abs(b[2]) for b in self._step_buf) / len(self._step_buf)
            di = i - self._ref_i
            r_mohm = (self._ref_v - v) / di * 1000.0 if di > 1e-6 else None
            self.steps.append(dict(step=k + 1, current_a=i, voltage_v=v, d_current_a=di,
                                   d_voltage_v=self._ref_v - v, r_mohm=r_mohm,
                                   from_a=self._ref_i, hold_s=c.dcir_step_s))
            self.log(f"step {k + 1}: I={i:.3f} A V={v:.3f} V R={r_mohm:.1f} mOhm")
            self._ref_v, self._ref_i = v, i
            if k + 1 < len(self._plan_steps):
                self._enter_step(k + 1)
            else:
                self.stop_reason = "DCIR steps complete"
                self._off_sequence(Phase.RECOVERY)

    def results(self) -> Results:
        r = self._results()
        r.dcir_steps = list(self.steps)
        vals = [x["r_mohm"] for x in self.steps if x["r_mohm"] is not None]
        r.dcir_mohm = sum(vals) / len(vals) if vals else None
        return r


# ── simulation harness ──────────────────────────────────────────────────────
def run_simulated(run: _Run, sim, dt_s: float = 1.0, max_steps: int = 2_000_000,
                  auto_confirm: bool = True) -> Results:
    """Drive a run from a Simulator6060B (the sim's load IS the measurement source)."""
    sim.connect()
    run.start()
    t = 0.0
    for _ in range(max_steps):
        if run.done:
            break
        st = sim.step(dt_s) if t > 0 else sim.read_status()
        t += dt_s
        run.on_sample(Sample(t, st.voltage_v, st.current_a, sim.temperature_c()))
        if run.phase is Phase.READY and auto_confirm:
            run.confirm()
    return run.results()
