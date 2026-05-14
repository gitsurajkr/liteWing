# Architecture — How the three layers work

## The big picture

```
main.py
  └── DroneService          (service.py)       ← orchestrator
        ├── DroneInterface  (interface.py)      ← the ONLY file that imports LiteWing
        ├── MissionController (controller.py)   ← pure flight logic
        └── FlightLogger    (logger.py)         ← CSV recording
```

Each layer has one job. Nothing skips a layer.

---

## DroneInterface — `interface.py`

**Job:** Be the only file in the project that ever calls `LiteWing`. Everyone else
calls `DroneInterface`. If the library ever changes, you fix it here, nowhere else.

| Method / Property | What it does |
|---|---|
| `__init__(cfg)` | Creates the real `LiteWing(ip)` object and calls `_apply_config()` to push all your config values into the library before any flight |
| `_apply_config()` | Translates `DroneConfig` fields → `LiteWing` properties (target height, trims, timeouts, sensor check flag, etc.) in one place |
| `connect()` | Calls `drone.connect()` — opens the Wi-Fi link and starts sensor streaming |
| `disconnect()` | Calls `drone.disconnect()` — closes the link safely |
| `arm()` | Calls `drone.arm()` — unlocks motors, runs sensor health check |
| `takeoff()` | Calls `drone.takeoff(hover_height, takeoff_duration)` from config — you never hardcode numbers here |
| `land()` | Calls `drone.land(landing_duration)` from config |
| `emergency_stop()` | Cuts all motors immediately — called on Ctrl-C or crash |
| `hover(seconds)` | Holds position for N seconds |
| `fly_to(x, y, z, yaw, speed)` | Flies to an absolute coordinate, fills in speed/threshold from config if not given |
| `battery` *(property)* | Returns current voltage as a float |
| `height` *(property)* | Returns current filtered height in metres |
| `position` *(property)* | Returns `(x, y)` estimated position tuple |
| `is_connected` *(property)* | True if the Wi-Fi link is open |
| `is_flying` *(property)* | True if motors are running |
| `read_sensors()` | Returns a full `SensorData` snapshot (all values at the same instant) |
| `set_led(LedColor)` | Takes a `LedColor` enum, unpacks the RGB tuple, calls `set_led_color` |
| `clear_leds()` | Turns off all LEDs |
| `start_logging(filename)` | Passes the filename through to LiteWing's built-in CSV logger |
| `stop_logging()` | Stops the CSV recorder |

**Why this matters:** `MissionController` and `FlightLogger` never see `LiteWing` at
all — they only see `DroneInterface`. If you swap the library tomorrow, you rewrite
one file.

---

## MissionController — `controller.py`

**Job:** Decide *what* the drone does. No connection logic, no error handling,
no CSV — just the flight plan.

| Method | What it does |
|---|---|
| `__init__(drone, cfg)` | Stores the interface as `self._d` and config as `self._cfg`. Does nothing else. |
| `preflight_ok()` | Reads battery, ToF height, and IMU tilt **before** arming. Returns `True` if safe, `False` if not. Prints a `[PREFLIGHT]` line for each check. The service calls this and aborts if it returns `False`. |
| `run()` | The full mission sequence — arm → takeoff → stabilise → fly each waypoint in order → end hold → land. Returns a `MissionResult` enum. |

**Inside `run()` step by step:**

1. `drone.arm()` — unlocks motors
2. LED → GREEN, `drone.takeoff()` — climbs to `hover_height`
3. `drone.hover(hover_after_takeoff)` — waits for the drone to settle
4. LED → BLUE, loop over `mission_waypoints`:
   - calls `drone.fly_to(x, y, ...)` for each point
   - after each waypoint, checks battery — if below `land_battery_v` it lands and returns `BATTERY_LOW`
5. LED → ORANGE, `drone.hover(hover_at_end)` — final hold
6. LED → RED, `drone.land()`, LEDs off
7. Returns `MissionResult.SUCCESS`

**Why this matters:** The controller never catches exceptions. It never calls
`disconnect()`. It never writes to CSV. Those are the service's jobs. Keeping
them separate means you can change the mission without touching error handling,
and vice versa.

---

## DroneService — `service.py`

**Job:** Wire everything together and own all error handling. This is the only
place `try / except / finally` appears.

| Method | What it does |
|---|---|
| `__init__(cfg)` | Creates `DroneInterface`, `MissionController`, and `FlightLogger` — all three wired to the same config |
| `run()` | Connects, waits for telemetry, runs preflight, starts logger, runs mission, handles errors, always disconnects |

**The `run()` flow:**

```
connect → sleep(2) → preflight_ok?
    NO  → return SENSOR_FAIL
    YES → logger.start() → controller.run() → return result

KeyboardInterrupt → emergency_stop → result = ABORTED
Any other Exception → emergency_stop → re-raise (crash visible to user)

finally (always runs):
    logger.stop() → logger.preview() → clear_leds() → disconnect()
```

The `finally` block is the safety net — even if the mission crashes halfway
through, the drone always disconnects cleanly and the CSV always gets closed.

**Why this matters:** `main.py` creates a `DroneService` and calls `.run()`.
That one call handles the entire session. You never need to write
`try/finally/disconnect` in your own scripts.

---

## How they call each other

```
main.py
  DroneService(config).run()
    │
    ├── DroneInterface.connect()
    ├── DroneInterface.battery          ← preflight reads sensors
    ├── DroneInterface.read_sensors()
    │
    ├── FlightLogger.start()            ← opens timestamped CSV
    │
    ├── MissionController.run()
    │     ├── DroneInterface.arm()
    │     ├── DroneInterface.set_led(GREEN)
    │     ├── DroneInterface.takeoff()
    │     ├── DroneInterface.hover(2.0)
    │     ├── DroneInterface.set_led(BLUE)
    │     ├── DroneInterface.fly_to(x, y) × N waypoints
    │     ├── DroneInterface.battery     ← battery check each waypoint
    │     ├── DroneInterface.set_led(ORANGE)
    │     ├── DroneInterface.hover(3.0)
    │     ├── DroneInterface.set_led(RED)
    │     ├── DroneInterface.land()
    │     └── DroneInterface.clear_leds()
    │
    ├── FlightLogger.stop()             ← closes CSV
    ├── FlightLogger.preview()          ← prints first 5 rows
    ├── DroneInterface.clear_leds()     ← safety clear
    └── DroneInterface.disconnect()
```

---

## Where to make changes

| I want to… | Edit this file |
|---|---|
| Change IP, height, speed, waypoints | `drone/config.py` or override in `main.py` |
| Add a new flight move (e.g. rotate) | `drone/interface.py` (expose it), `drone/controller.py` (call it) |
| Change what happens before/after flight | `drone/service.py` |
| Add a new pre-flight check | `drone/controller.py` → `preflight_ok()` |
| Change LED colours | `drone/enums.py` → `LedColor` |
| Change log format or filename pattern | `drone/logger.py` |
