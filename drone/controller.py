
from .config import DroneConfig
from .enums import LedColor, MissionResult
from .interface import DroneInterface


class MissionController:
    def __init__(self, drone: DroneInterface, cfg: DroneConfig) -> None:
        self._cfg = cfg
        self._d   = drone

    def preflight_ok(self) -> bool:
        """Battery and sensor sanity checks. Returns True if safe to fly."""
        ok = True

        v = self._d.battery
        if v < self._cfg.min_battery_v:
            print(f"[PREFLIGHT] FAIL  Battery {v:.2f} V < {self._cfg.min_battery_v} V — charge first.")
            ok = False
        else:
            print(f"[PREFLIGHT] OK    Battery {v:.2f} V")

        s = self._d.read_sensors()

        if s.range_height == 0.0:
            print("[PREFLIGHT] WARN  ToF reads 0 — check positioning module wiring.")
        else:
            print(f"[PREFLIGHT] OK    ToF height {s.range_height:.3f} m")

        if abs(s.roll) > 10 or abs(s.pitch) > 10:
            print(f"[PREFLIGHT] WARN  Drone tilted R={s.roll:.1f}° P={s.pitch:.1f}° — place on flat surface.")
        else:
            print(f"[PREFLIGHT] OK    IMU R={s.roll:.1f}° P={s.pitch:.1f}° Y={s.yaw:.1f}°")

        if self._cfg.debug_mode:
            print("[PREFLIGHT] NOTE  debug_mode=True — motors DISABLED.")

        if ok:
            print("[PREFLIGHT] All checks passed.")
        else:
            print("[PREFLIGHT] Checks FAILED — aborting.")
        return ok

    def run(self) -> MissionResult:
        """Execute the full mission. Returns a MissionResult."""
        drone   = self._d
        cfg = self._cfg

        # ── Arm ───────────────────────────────────────────────────────────────
        print("[CTRL] Arming...")
        drone.arm()

        # ── Takeoff ───────────────────────────────────────────────────────────
        print(f"[CTRL] Takeoff → {cfg.hover_height:.2f} m")
        drone.set_led(LedColor.GREEN)
        drone.takeoff()

        print(f"[CTRL] Stabilising {cfg.hover_after_takeoff:.1f} s")
        drone.hover(cfg.hover_after_takeoff)

        # ── Waypoints ─────────────────────────────────────────────────────────
        print(f"[CTRL] Mission: {len(cfg.mission_waypoints)} waypoints @ {cfg.waypoint_speed:.2f} m/s")
        drone.set_led(LedColor.BLUE)

        for i, wp in enumerate(cfg.mission_waypoints):
            x, y = wp[0], wp[1]
            z    = wp[2] if len(wp) > 2 else None
            yaw  = wp[3] if len(wp) > 3 else None
            print(f"[CTRL]   WP{i+1}: ({x:.2f}, {y:.2f})")
            drone.fly_to(x, y, z=z, yaw=yaw, speed=cfg.waypoint_speed)
            px, py = drone.position
            print(f"[CTRL]     reached ({px:.2f}, {py:.2f})")

            v = drone.battery
            if v > 0 and v < cfg.land_battery_v:
                print(f"[CTRL] Battery critical ({v:.2f} V) — aborting!")
                drone.set_led(LedColor.RED)
                drone.land()
                return MissionResult.BATTERY_LOW

        # ── End hold ──────────────────────────────────────────────────────────
        print(f"[CTRL] End hold {cfg.hover_at_end:.1f} s")
        drone.set_led(LedColor.ORANGE)
        drone.hover(cfg.hover_at_end)

        # ── Land ──────────────────────────────────────────────────────────────
        print("[CTRL] Landing...")
        drone.set_led(LedColor.RED)
        drone.land()
        drone.clear_leds()
        return MissionResult.SUCCESS
