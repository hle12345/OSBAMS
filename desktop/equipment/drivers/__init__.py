"""Rev.2 active load drivers: Keysight6060B, Manual6060B, Simulator6060B."""
from .base import ElectronicLoad, LoadStatus, InterfaceBlocked, CommandNotVerified
from .manual_6060b import Manual6060B
from .simulator_6060b import Simulator6060B
from .keysight_6060b import Keysight6060B


def create_load(load_type: str = "manual", **kwargs) -> ElectronicLoad:
    """load_type: 'manual' | 'simulator' | 'keysight' (case-insensitive)."""
    types = {"manual": Manual6060B, "manual6060b": Manual6060B,
             "simulator": Simulator6060B, "simulator6060b": Simulator6060B,
             "keysight": Keysight6060B, "keysight6060b": Keysight6060B}
    try:
        cls = types[load_type.lower()]
    except KeyError:
        raise ValueError(f"unknown load type {load_type!r}; "
                         f"active Rev.2 loads: manual, simulator, keysight")
    return cls(**kwargs)
