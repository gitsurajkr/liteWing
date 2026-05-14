import sys
from drone import DroneService, config

# ── Configure your session here ───────────────────────────────────────────────
config.ip                  = "192.168.43.42"
config.hover_height        = 0.35
config.debug_mode          = False      # set True for a motors-off dry run
config.mission_waypoints   = [          # (x, y) — 0.4 m square, fits ~1 m² area
    (0.4,  0.0),
    (0.4,  0.4),
    (0.0,  0.4),
    (0.0,  0.0),
]
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = DroneService(config).run()
    sys.exit(0 if result.name == "SUCCESS" else 1)
