import sys
from drone import DroneService, MissionLevel, config

# ── Configure your session here ───────────────────────────────────────────────
config.ip                = "192.168.43.42"
config.hover_height      = 0.35
config.debug_mode        = False        # True = motors off, sensors still stream
config.mission_waypoints = [            # used by L4 only
    (0.4,  0.0),
    (0.4,  0.4),
    (0.0,  0.4),
    (0.0,  0.0),
]
# ─────────────────────────────────────────────────────────────────────────────

USAGE = """\
Usage: python main.py <LEVEL>

Levels (run them in order — only move on when the previous one works):
  L0   Arm only       — motors arm 3 s then disarm. NO takeoff. Props off recommended.
  L1   Telemetry only — no motors, prints sensor values for 10 s
  L2   Hover in place — takeoff, hover 5 s, land
  L3   Altitude check — takeoff low, climb, descend, land
  L4   Waypoint mission — full square pattern

Example:
  python main.py L0
"""


def main() -> int:
    if len(sys.argv) < 2:
        print(USAGE)
        return 2
    try:
        level = MissionLevel.parse(sys.argv[1])
    except ValueError as e:
        print(f"Error: {e}\n")
        print(USAGE)
        return 2

    result = DroneService(config).run(level)
    return 0 if result.name == "SUCCESS" else 1


if __name__ == "__main__":
    sys.exit(main())
