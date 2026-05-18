# drone/enums.py  –  All string constants replaced with typed enums.

from enum import Enum, auto


class FlightPhase(str, Enum):
    IDLE        = "IDLE"
    CONNECTING  = "CONNECTING"
    CONNECTED   = "CONNECTED"
    TAKEOFF     = "TAKEOFF"
    HOVERING    = "HOVERING"
    NAVIGATING  = "NAVIGATING"
    LANDING     = "LANDING"
    COMPLETE    = "COMPLETE"
    ERROR       = "ERROR"


class LedColor(Enum):
    OFF    = (0,   0,   0)
    RED    = (255, 0,   0)
    GREEN  = (0,   255, 0)
    BLUE   = (0,   0,   255)
    ORANGE = (255, 165, 0)
    WHITE  = (255, 255, 255)
    YELLOW = (255, 255, 0)


class MissionResult(Enum):
    SUCCESS       = auto()
    ABORTED       = auto()
    BATTERY_LOW   = auto()
    SENSOR_FAIL   = auto()
    EMERGENCY     = auto()


class MissionLevel(str, Enum):
    L0_ARM       = "L0"   # arm only, no takeoff — verifies motors unlock
    L1_TELEMETRY = "L1"   # no motors – stream sensors for N seconds
    L2_HOVER     = "L2"   # takeoff → hover in place → land
    L3_ALTITUDE  = "L3"   # takeoff low → climb → descend → land
    L4_WAYPOINTS = "L4"   # full square mission

    @classmethod
    def parse(cls, value: str) -> "MissionLevel":
        """Accept 'L1', 'l1', '1', etc."""
        v = str(value).strip().upper()
        if not v.startswith("L"):
            v = "L" + v
        for level in cls:
            if level.value == v:
                return level
        valid = ", ".join(l.value for l in cls)
        raise ValueError(f"Unknown level '{value}'. Valid: {valid}")
