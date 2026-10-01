"""
services/bms.py — software BMS abstraction (Rev.2).

Interfaces researched for packs INSIDE the 60 V envelope: CAN, UART, SMBus and
other documented buses. A pack whose protocol is not documented/implemented is
SMART_PACK_UNSUPPORTED; OSBAMS may still take permitted external measurements
on its normal discharge output. OSBAMS NEVER bypasses or overrides BMS
protection: it has no write path to cell-protection state.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from services.battery_profiles import SMART_PACK_UNSUPPORTED

SUPPORTED_BUSES = ("CAN", "UART", "SMBUS")      # research targets, none implemented yet


@dataclass
class BmsSnapshot:
    pack_voltage_v: Optional[float] = None
    current_a: Optional[float] = None
    soc_pct: Optional[float] = None
    cell_voltages_v: Optional[list] = None
    temperatures_c: Optional[list] = None
    protection_flags: Optional[list] = None


class BmsInterface(ABC):
    """Read-only by design."""
    status: str = "SUPPORTED"

    @abstractmethod
    def read(self) -> BmsSnapshot: ...


class UnsupportedBms(BmsInterface):
    status = SMART_PACK_UNSUPPORTED

    def read(self) -> BmsSnapshot:
        raise NotImplementedError(
            f"{SMART_PACK_UNSUPPORTED}: no documented interface — use external "
            f"OSBAMS measurements only; do not bypass BMS protection")


def bms_for(profile) -> BmsInterface:
    """Only SMART_PACK_UNSUPPORTED exists today."""
    return UnsupportedBms()
