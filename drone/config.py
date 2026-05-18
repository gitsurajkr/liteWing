# drone/config.py  –  Every tunable value lives here. Nothing else needs editing.

from dataclasses import dataclass, field
from typing import List, Tuple

# Waypoint type: (x, y) | (x, y, z) | (x, y, z, yaw)
Waypoint = Tuple


@dataclass
class DroneConfig:
    # ── Network ────────────────────────────────────────────────────────────────
    ip: str = "192.168.43.42"

    # ── Safety ─────────────────────────────────────────────────────────────────
    min_battery_v: float = 3.5          # refuse to fly below this
    land_battery_v: float = 3.3         # auto-land mid-flight threshold

    # ── Flight envelope ────────────────────────────────────────────────────────
    hover_height: float = 0.35          # cruise altitude (m)
    max_speed: float = 0.25             # hard cap for all moves (m/s)
    takeoff_duration: float = 1.2       # takeoff ramp time (s)
    landing_duration: float = 2.5       # landing timeout (s)
    descent_rate: float = 0.25          # m/s during land()

    # ── Hover pauses ───────────────────────────────────────────────────────────
    hover_after_takeoff: float = 2.0    # settle after takeoff (s)
    hover_at_end: float = 3.0           # hold before landing (s)

    # ── L0: Arm-only test ─────────────────────────────────────────────────────
    l0_hold_seconds: float = 3.0        # how long to keep motors armed (no takeoff)

    # ── L1: Telemetry-only test ───────────────────────────────────────────────
    l1_duration: float = 10.0           # seconds of sensor streaming
    l1_print_interval: float = 0.5      # seconds between prints

    # ── L2: Hover-in-place test ───────────────────────────────────────────────
    l2_hover_seconds: float = 5.0       # how long to hold position

    # ── L3: Altitude up/down test ─────────────────────────────────────────────
    l3_low_height: float = 0.25         # initial hover height (m)
    l3_high_height: float = 0.45        # climb target (m)
    l3_hold_seconds: float = 2.0        # hold at each height

    # ── Waypoint navigation ────────────────────────────────────────────────────
    # Keep moves ≤ 0.5 m for first indoor tests (1 m² clear area is enough).
    # +X = forward, -X = backward, +Y = left, -Y = right
    mission_waypoints: List[Waypoint] = field(default_factory=lambda: [
        (0.4,  0.0),   # forward
        (0.4,  0.4),   # forward-left
        (0.0,  0.4),   # left
        (0.0,  0.0),   # back to origin
    ])
    waypoint_speed: float = 0.20        # m/s between waypoints
    waypoint_threshold: float = 0.10    # arrival tolerance (m)
    waypoint_stabilize: float = 0.6     # pause at each waypoint (s)

    # ── Trim (adjust if drone drifts on flat surface) ──────────────────────────
    trim_pitch: float = 0.0             # positive → nudge forward
    trim_roll: float = 0.0              # positive → nudge right

    # ── Dev / debug ────────────────────────────────────────────────────────────
    debug_mode: bool = False            # True = motors off, sensors still stream
    enable_sensor_check: bool = True    # False = skip ToF/flow check on arm()

    # ── Logging ────────────────────────────────────────────────────────────────
    log_to_csv: bool = True
    log_filename: str = "flight_log.csv"


# Singleton used across the app — override fields before passing to DroneService.
config = DroneConfig()
