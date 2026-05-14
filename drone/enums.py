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
