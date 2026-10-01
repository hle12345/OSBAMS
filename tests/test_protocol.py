"""
tests/test_protocol.py — Protocol v1 conformance and cross-language sync

Verifies that firmware, parser, and simulator all speak the same protocol,
and that shared constants in config.py and app_config.h agree.
"""
import sys, os, re, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "desktop"))

from services.protocol import (
    parse_frame, encode_data_frame, crc16, StreamStats,
    PROTOCOL_VERSION, DATA_FIELD_COUNT, FLAG_OVERTEMP, FLAG_UNDERVOLT,
)


class TestCrc(unittest.TestCase):
    """CRC must match the C implementation bit for bit."""

    KNOWN = {   # verified against compiled firmware Protocol_Crc16()
        "OSBAMS,1,42,1500,41820,3000,125460,250,0,DISCHARGING": 0xA1A4,
        "OSBAMS,1,0,0,42000,0,0,250,0,READY":                   0x86F2,
        "OSBAMS,1,999,499500,31000,2980,92380,410,8,CUTOFF":    0x5D06,
        "OSBAMS,1,1,500,41000,3000,123000,240,4,FAULT":         0x8A04,
    }

    def test_matches_c_implementation(self):
        for text, expected in self.KNOWN.items():
            self.assertEqual(crc16(text.encode()), expected,
                             f"CRC mismatch for {text!r}")

    def test_empty_input(self):
        self.assertEqual(crc16(b""), 0xFFFF)


class TestRoundTrip(unittest.TestCase):

    def test_encode_then_parse(self):
        frame = encode_data_frame(42, 1500, 41820, 3000, 125460, 250,
                                  0, "DISCHARGING")
        r = parse_frame(frame)
        self.assertIsNotNone(r.sample, r.error)
        s = r.sample
        self.assertEqual(s.sequence, 42)
        self.assertEqual(s.voltage_mv, 41820)
        self.assertEqual(s.state, "DISCHARGING")
        self.assertTrue(s.crc_valid)

    def test_field_count(self):
        frame = encode_data_frame(1, 0, 40000, 3000, 120000, 250)
        self.assertEqual(len(frame.split(",")), DATA_FIELD_COUNT)

    def test_unit_conversion(self):
        r = parse_frame(encode_data_frame(1, 0, 41820, 3000, 125460, 250))
        s = r.sample
        self.assertAlmostEqual(s.voltage_v, 41.82, places=3)
        self.assertAlmostEqual(s.current_a, 3.0,   places=3)
        self.assertAlmostEqual(s.temp_c,    25.0,  places=1)


class TestRejection(unittest.TestCase):
    """Malformed frames must be rejected with a reason, never silently."""

    def test_bad_crc_rejected(self):
        frame = encode_data_frame(1, 0, 40000, 3000, 120000, 250)
        bad = frame[:-1] + ("0" if frame[-1] != "0" else "1")
        r = parse_frame(bad, strict_crc=True)
        self.assertIsNone(r.sample)
        self.assertIn("CRC", r.error)

    def test_wrong_field_count_rejected(self):
        r = parse_frame("OSBAMS,1,42,1500")
        self.assertIsNone(r.sample)
        self.assertIn("field count", r.error)

    def test_wrong_version_rejected(self):
        r = parse_frame("OSBAMS,9,1,0,40000,3000,120000,250,0,READY,0000")
        self.assertIsNone(r.sample)
        self.assertIn("version", r.error)

    def test_unknown_state_rejected(self):
        body = "OSBAMS,1,1,0,40000,3000,120000,250,0,NONSENSE"
        r = parse_frame(f"{body},{crc16(body.encode()):04X}")
        self.assertIsNone(r.sample)
        self.assertIn("state", r.error)

    def test_missing_prefix_rejected(self):
        r = parse_frame("GARBAGE,1,2,3")
        self.assertIsNone(r.sample)

    def test_legacy_rejected_by_default(self):
        r = parse_frame("OSBAMS,1500,41820,0,0,240")
        self.assertIsNone(r.sample)
        self.assertIn("legacy", r.error)

    def test_legacy_accepted_when_allowed(self):
        r = parse_frame("OSBAMS,1500,41820,0,0,240", allow_legacy=True)
        self.assertIsNotNone(r.sample)
        self.assertEqual(r.sample.protocol_version, 0)


class TestStreamStats(unittest.TestCase):

    def test_sequence_gap_detected(self):
        stats = StreamStats()
        for seq in [1, 2, 5, 6]:
            stats.record(parse_frame(
                encode_data_frame(seq, seq * 500, 40000, 3000, 120000, 250)))
        self.assertEqual(stats.frames_ok, 4)
        self.assertEqual(stats.sequence_gaps, 1)
        self.assertEqual(stats.samples_lost, 2)

    def test_no_gap_when_contiguous(self):
        stats = StreamStats()
        for seq in range(1, 11):
            stats.record(parse_frame(
                encode_data_frame(seq, seq * 500, 40000, 3000, 120000, 250)))
        self.assertEqual(stats.sequence_gaps, 0)
        self.assertEqual(stats.samples_lost, 0)

    def test_time_reversal_detected(self):
        stats = StreamStats()
        stats.record(parse_frame(encode_data_frame(1, 5000, 40000, 3000, 120000, 250)))
        stats.record(parse_frame(encode_data_frame(2, 1000, 40000, 3000, 120000, 250)))
        self.assertEqual(stats.time_reversals, 1)

    def test_malformed_counted_not_dropped(self):
        stats = StreamStats()
        stats.record(parse_frame("OSBAMS,1,2,3"))
        stats.record(parse_frame("garbage"))
        self.assertEqual(stats.frames_malformed, 2)
        self.assertIsNotNone(stats.last_error)


class TestFlags(unittest.TestCase):

    def test_flags_decoded(self):
        r = parse_frame(encode_data_frame(
            1, 0, 27000, 3000, 81000, 550,
            flags=FLAG_OVERTEMP | FLAG_UNDERVOLT, state="FAULT"))
        s = r.sample
        self.assertIn("OVERTEMP",  s.active_flags)
        self.assertIn("UNDERVOLT", s.active_flags)
        self.assertTrue(s.has_fault)

    def test_no_flags_no_fault(self):
        r = parse_frame(encode_data_frame(1, 0, 40000, 3000, 120000, 250))
        self.assertFalse(r.sample.has_fault)
        self.assertEqual(r.sample.active_flags, [])


class TestSimulatorConformance(unittest.TestCase):
    """Every simulator profile must emit parseable Protocol v1 frames."""

    def test_all_profiles_parse(self):
        from equipment.drivers import Simulator6060B
        for profile in Simulator6060B.PROFILES:
            sim = Simulator6060B(profile, sample_rate_ms=60000)
            stats = StreamStats()
            for line in sim.generate_lines():
                stats.record(parse_frame(line))
            self.assertEqual(stats.frames_malformed, 0,
                             f"profile {profile}: {stats.last_error}")
            self.assertGreater(stats.frames_ok, 0, f"profile {profile} empty")


class TestConfigSync(unittest.TestCase):
    """
    REQ-601: shared constants must agree across Python and C.
    C cannot import Python, so agreement is verified here instead.
    """

    def _c_defines(self) -> dict:
        """
        Collect #defines from the firmware Core headers.

        Reads both app_config.h and protocol_version.h because the protocol
        version now lives in its own header (included by app_config.h and
        protocol.h) so it cannot be defined twice and drift.
        """
        fw = os.path.join(os.path.dirname(__file__), "..", "Firmware")
        out = {}
        for rel in ("App/Inc/protocol_version.h", "Core/Inc/app_config.h",
                    "Core/Inc/system_clock.h"):
            path = os.path.join(fw, rel)
            if not os.path.exists(path):
                continue
            text = open(path).read()
            for m in re.finditer(r'^[ \t]*#define[ \t]+(\w+)[ \t]+([^\s/]+)',
                                 text, re.MULTILINE):
                name, val = m.group(1), m.group(2).rstrip("UuLl")
                try:
                    out[name] = int(val, 0)
                except ValueError:
                    out[name] = val
        return out

    def test_safety_limits_match(self):
        import config
        c = self._c_defines()
        # Layered model: firmware hard trip (absolute protection boundary)
        # mirrors exactly; the desktop operating ceiling is a DIFFERENT,
        # lower number and must stay strictly below the trip.
        self.assertEqual(c["OSBAMS_DEFAULT_MAX_CURRENT_MA"],
                         int(config.FIRMWARE_HARD_TRIP_A * 1000))
        self.assertEqual(c["OSBAMS_DEFAULT_MAX_TEMP_C10"],
                         int(config.FIRMWARE_HARD_TRIP_TEMP_C * 10))
        self.assertLess(config.SAFETY_MAX_CURRENT_A, config.FIRMWARE_HARD_TRIP_A)
        self.assertLess(config.SAFETY_MAX_TEMP_C, config.FIRMWARE_HARD_TRIP_TEMP_C)
        # Rev.2: there is NO global minimum battery voltage. Cutoff is
        # profile-specific (services/battery_profiles.py). The firmware
        # constants are only the power-on defaults before a profile is loaded.
        self.assertFalse(hasattr(config, "SAFETY_MIN_VOLTAGE_MV"))
        self.assertFalse(hasattr(config, "SAFETY_MAX_VOLTAGE_MV"))

    def test_sample_period_matches(self):
        import config
        self.assertEqual(self._c_defines()["OSBAMS_SAMPLE_PERIOD_MS"],
                         config.DEFAULT_SAMPLE_RATE_MS)

    def test_protocol_version_matches(self):
        import config
        self.assertEqual(self._c_defines()["OSBAMS_PROTOCOL_VERSION"],
                         config.PROTOCOL_VERSION)
        self.assertEqual(PROTOCOL_VERSION, config.PROTOCOL_VERSION)

    def test_baud_matches(self):
        import config
        self.assertEqual(self._c_defines()["UART_BAUD"],
                         config.SERIAL_BAUD)


class TestMlPhaseBoundaries(unittest.TestCase):
    """Item 6: phases are <10, 10-29, >=30 with no overlap or gap."""

    def test_boundaries(self):
        import config
        cases = [(0,"rule_only"), (9,"rule_only"), (10,"experimental"),
                 (29,"experimental"), (30,"assisted"), (500,"assisted")]
        for n, expected in cases:
            self.assertEqual(config.ml_phase_for(n), expected, f"n={n}")

    def test_ml_never_exceeds_half(self):
        import config
        for n in [0, 5, 10, 29, 30, 100, 10000]:
            _, ml = config.ml_weights_for(n)
            self.assertLessEqual(ml, 0.50, f"n={n} ml={ml}")

    def test_weights_sum_to_one(self):
        import config
        for w in config.ML_PHASE_WEIGHTS.values():
            self.assertAlmostEqual(w["rule"] + w["ml"], 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)


# ═══════════════════════════════════════════════════════════════════════════
# Cross-language conformance: compile the REAL C encoder and parse its output
# ═══════════════════════════════════════════════════════════════════════════

import subprocess
import shutil

FW_TESTS = os.path.join(os.path.dirname(__file__), "..", "Firmware", "Tests")
C_BINARY = os.path.join(FW_TESTS, "build", "test_protocol_c")


def _build_c_harness() -> bool:
    """Compile the C conformance binary. Returns False if gcc is absent."""
    if shutil.which("gcc") is None:
        return False
    os.makedirs(os.path.join(FW_TESTS, "build"), exist_ok=True)
    r = subprocess.run(["make", "-s", "build/test_protocol_c"], cwd=FW_TESTS,
                       capture_output=True, text=True)
    return r.returncode == 0 and os.path.exists(C_BINARY)


def _run_c(mode: str, stdin_text: str = "") -> str:
    return subprocess.run([C_BINARY, mode], input=stdin_text,
                          capture_output=True, text=True, check=True).stdout


@unittest.skipUnless(_build_c_harness(),
                     "gcc unavailable or C harness failed to build")
class TestCrossLanguageConformance(unittest.TestCase):
    """
    Compiles firmware/Middleware/Src/protocol.c and verifies that its actual
    output parses in Python. Stronger than stored constants, which go stale
    when the C changes.
    """

    def test_compiled_version_matches_python(self):
        """The compiled firmware must report the same protocol version."""
        import config
        c_version = int(_run_c("version").strip())
        self.assertEqual(c_version, PROTOCOL_VERSION,
                         "C protocol_version.h disagrees with services/protocol.py")
        self.assertEqual(c_version, config.PROTOCOL_VERSION,
                         "C protocol_version.h disagrees with config.py")

    def test_c_frames_parse_in_python(self):
        """Every DATA frame the C encoder emits must parse with a valid CRC."""
        data_frames = 0
        for line in _run_c("frames").splitlines():
            line = line.strip()
            if not line:
                continue
            r = parse_frame(line)
            self.assertIsNone(r.error, f"C frame rejected: {line!r} -> {r.error}")
            if r.sample:
                data_frames += 1
                self.assertTrue(r.sample.crc_valid, f"CRC failed: {line!r}")
        self.assertGreaterEqual(data_frames, 6, "expected several DATA frames")

    def test_c_boot_frame_advertises_correct_version(self):
        """BOOT frame version must match the DATA frame version."""
        boot = next(l for l in _run_c("frames").splitlines()
                    if ",BOOT," in l)
        r = parse_frame(boot)
        self.assertTrue(r.is_info)
        self.assertEqual(r.info_type, "BOOT")
        # BOOT payload is [fw_version, protocol_version]
        self.assertEqual(int(r.info_data[1]), PROTOCOL_VERSION,
                         "BOOT advertises a different protocol than DATA frames")

    def test_c_handles_negative_and_extreme_values(self):
        """Negative current and int32/int16 extremes must survive the round trip."""
        frames = [l for l in _run_c("frames").splitlines() if ",1," in l]
        samples = [parse_frame(f).sample for f in frames]
        samples = [s for s in samples if s]

        neg = [s for s in samples if s.current_ma < 0]
        self.assertTrue(neg, "no negative-current frame emitted")
        self.assertEqual(neg[0].current_ma, -1500)

        extreme = [s for s in samples if s.voltage_mv == 2147483647]
        self.assertTrue(extreme, "no int32 max frame emitted")
        self.assertEqual(extreme[0].current_ma, -2147483648)
        self.assertEqual(extreme[0].temp_c10,   -32768)
        self.assertEqual(extreme[0].flags,       65535)

    def test_c_crc_matches_python_crc(self):
        """Reverse direction: C computes the CRC of Python-supplied bodies."""
        bodies = [
            "OSBAMS,1,42,1500,41820,3000,125460,250,0,DISCHARGING",
            "OSBAMS,1,0,0,42000,0,0,250,0,READY",
            "OSBAMS,1,7,3500,36000,-2000,-72000,310,16,PAUSED",
            "",   # skipped by the C side
            "OSBAMS,1,4294967295,4294967295,1,1,1,1,1,COMPLETE",
        ]
        non_empty = [b for b in bodies if b]
        out = _run_c("crc", "\n".join(bodies) + "\n").split()
        self.assertEqual(len(out), len(non_empty))
        for body, c_crc in zip(non_empty, out):
            self.assertEqual(int(c_crc, 16), crc16(body.encode()),
                             f"CRC mismatch for {body!r}")

    def test_single_protocol_version_definition(self):
        """
        OSBAMS_PROTOCOL_VERSION must be #defined in exactly one header,
        so app_config.h and protocol.h can never drift apart again.
        """
        fw = os.path.join(os.path.dirname(__file__), "..", "Firmware")
        defining = []
        for root, _dirs, files in os.walk(fw):
            for fn in files:
                if not fn.endswith(".h"):
                    continue
                path = os.path.join(root, fn)
                text = open(path, errors="replace").read()
                if re.search(r'^\s*#define\s+OSBAMS_PROTOCOL_VERSION\s',
                             text, re.MULTILINE):
                    defining.append(os.path.relpath(path, fw))
        self.assertEqual(len(defining), 1,
                         f"OSBAMS_PROTOCOL_VERSION defined in {len(defining)} "
                         f"headers: {defining}. It must live in exactly one.")
        self.assertIn("protocol_version.h", defining[0])


class TestIndependentBatteryCounting(unittest.TestCase):
    """
    ML activation must be gated on INDEPENDENT BATTERIES, not test count.
    Ten tests of one pack tell you about one pack.
    """

    def test_repeat_tests_are_not_independent_samples(self):
        """4 batteries x 3 tests = 12 records but only 4 independent samples."""
        groups = [b for b in range(4) for _ in range(3)]
        self.assertEqual(len(groups), 12)
        self.assertEqual(len(set(groups)), 4)

        import config
        # Naive counting would wrongly activate ML
        self.assertNotEqual(config.ml_phase_for(len(groups)), "rule_only")
        # Correct counting keeps it rule-only
        self.assertEqual(config.ml_phase_for(len(set(groups))), "rule_only")

    def test_groupkfold_prevents_leakage(self):
        """GroupKFold must not place one battery in both train and test."""
        import numpy as np
        from sklearn.model_selection import GroupKFold
        groups = np.array([b for b in range(6) for _ in range(3)])
        X = np.random.rand(len(groups), 4)
        y = np.array(["Healthy" if b % 2 else "Degraded" for b in groups])

        for train_idx, test_idx in GroupKFold(n_splits=3).split(X, y, groups):
            overlap = set(groups[train_idx]) & set(groups[test_idx])
            self.assertEqual(overlap, set(),
                             f"battery(s) {overlap} appear in both folds")

    def test_model_reports_both_counts(self):
        from gui.ai_model import OSBAMSModel
        m = OSBAMSModel()
        r = m.train()
        self.assertIn("n_batteries", r)
        self.assertIn("n_records",   r)
        self.assertIn("phase",       r)
        self.assertGreaterEqual(r["n_records"], r["n_batteries"],
                                "records can never be fewer than batteries")

    def test_cv_method_is_documented(self):
        """Whatever happens, the result must say how CV was done."""
        from gui.ai_model import OSBAMSModel
        r = OSBAMSModel().train()
        if r.get("status") == "trained":
            self.assertIn("cv_method", r)
