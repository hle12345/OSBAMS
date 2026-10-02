"""keysight_6060b/transport.py — GPIB transports (none assumed to exist at SFSU)."""

from typing import Optional, Protocol


class Transport(Protocol):
    def write(self, cmd: str) -> None: ...
    def query(self, cmd: str) -> str: ...
    def close(self) -> None: ...


class PyVisaTransport:
    """
    VISA transport, e.g. 'GPIB0::5::INSTR' via a USB-GPIB adapter, a LAN-GPIB
    gateway ('TCPIP0::host::gpib0,5::INSTR') or a GPIB-equipped PC.
    Requires: pip install pyvisa  (+ a VISA backend). Which of these SFSU has
    is NOT confirmed — see docs/rev2/GPIB_INTERFACE_CONFIRMATION.md.
    """

    def __init__(self, resource: str, timeout_ms: int = 5000):
        import pyvisa                       # deferred: optional dependency
        self._rm = pyvisa.ResourceManager()
        self._inst = self._rm.open_resource(resource)
        self._inst.timeout = timeout_ms

    def write(self, cmd: str) -> None:
        self._inst.write(cmd)

    def query(self, cmd: str) -> str:
        return self._inst.query(cmd).strip()

    def go_to_local(self) -> bool:
        """GPIB Go-To-Local (GTL) via VISA REN control; False if unsupported."""
        try:
            import pyvisa.constants as c
            self._inst.control_ren(c.RENLineOperation.address_gtl)
            return True
        except Exception:
            return False

    def close(self) -> None:
        try:
            self._inst.close()
        finally:
            self._rm.close()


class ScriptedTransport:
    """Test double: records writes, answers queries from a dict (prefix match)."""

    def __init__(self, replies: Optional[dict] = None):
        self.replies = dict(replies or {})
        self.log: list = []
        self.local_called = False

    def write(self, cmd: str) -> None:
        self.log.append(("w", cmd))

    def query(self, cmd: str) -> str:
        self.log.append(("q", cmd))
        for k, v in self.replies.items():
            if cmd.startswith(k):
                return v
        return "0"

    def go_to_local(self) -> bool:
        self.local_called = True
        return True

    def close(self) -> None:
        self.log.append(("close", ""))

    @property
    def writes(self) -> list:
        return [c for k, c in self.log if k == "w"]
