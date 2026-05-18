import time
from .config import DroneConfig
from .enums import LedColor, MissionResult, MissionLevel
from .interface import DroneInterface


class MissionController:
    def __init__(self, drone: DroneInterface, cfg: DroneConfig) -> None:
        self._cfg = cfg
        self._d   = drone

    # ── Pre-flight ────────────────────────────────────────────────────────────

    def preflight_ok(self, level: MissionLevel) -> bool:
        """L1 only needs link + battery. L2/3/4 need full sensor checks."""
        ok = True

        v = self._d.battery
        if v < self._cfg.min_battery_v:
            print(f"[PREFLIGHT] FAIL  Battery {v:.2f} V < {self._cfg.min_battery_v} V — charge first.")
            ok = False
        else:
            print(f"[PREFLIGHT] OK    Battery {v:.2f} V")

        # L0/L1 don't fly; skip the rest
        if level in (MissionLevel.L0_ARM, MissionLevel.L1_TELEMETRY):
            print(f"[PREFLIGHT] {level.value} — no takeoff, skipping flight checks.")
            return ok

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

        print("[PREFLIGHT] All checks passed." if ok else "[PREFLIGHT] Checks FAILED — aborting.")
        return ok

    # ── Dispatcher ────────────────────────────────────────────────────────────

    def run(self, level: MissionLevel) -> MissionResult:
        print(f"[CTRL] Running {level.name}")
        if level == MissionLevel.L0_ARM:
            return self._run_l0_arm()
        if level == MissionLevel.L1_TELEMETRY:
            return self._run_l1_telemetry()
        if level == MissionLevel.L2_HOVER:
            return self._run_l2_hover()
        if level == MissionLevel.L3_ALTITUDE:
            return self._run_l3_altitude()
        if level == MissionLevel.L4_WAYPOINTS:
            return self._run_l4_waypoints()
        raise ValueError(f"Unhandled level: {level}")

    # ── L0: Arm only ──────────────────────────────────────────────────────────

    def _run_l0_arm(self) -> MissionResult:
        """Arm the drone, hold for N seconds, disarm. No takeoff."""
        d, cfg = self._d, self._cfg
        d.set_led(LedColor.YELLOW)
        print("[L0] WARNING — props will spin briefly. Keep hands clear!")
        print("[L0] Arming...")
        d.arm()

        print(f"[L0] Armed — holding {cfg.l0_hold_seconds:.1f} s (no takeoff)")
        time.sleep(cfg.l0_hold_seconds)

        print("[L0] Disarming (emergency_stop cuts motors cleanly)")
        d.emergency_stop()
        d.clear_leds()
        return MissionResult.SUCCESS

    # ── L1: Telemetry only ────────────────────────────────────────────────────

    def _run_l1_telemetry(self) -> MissionResult:
        """No motors. Stream all sensor values for N seconds."""
        d, cfg = self._d, self._cfg
        d.set_led(LedColor.WHITE)
        print(f"[L1] Streaming sensors for {cfg.l1_duration:.0f} s...")

        end = time.time() + cfg.l1_duration
        while time.time() < end:
            s = d.read_sensors()
            print(f"[L1] Bat:{s.battery:.2f}V  H:{s.height:.3f}m  "
                  f"Pos:({s.x:.2f},{s.y:.2f})  "
                  f"RPY:({s.roll:.1f},{s.pitch:.1f},{s.yaw:.1f})°")
            time.sleep(cfg.l1_print_interval)

        d.clear_leds()
        return MissionResult.SUCCESS

    # ── L2: Hover in place ────────────────────────────────────────────────────

    def _run_l2_hover(self) -> MissionResult:
        """Takeoff, hover for N seconds, land. No XY movement."""
        d, cfg = self._d, self._cfg

        print("[L2] Arming...")
        d.arm()

        d.set_led(LedColor.GREEN)
        print(f"[L2] Takeoff → {cfg.hover_height:.2f} m")
        d.takeoff()

        print(f"[L2] Hovering {cfg.l2_hover_seconds:.1f} s")
        d.hover(cfg.l2_hover_seconds)

        d.set_led(LedColor.RED)
        print("[L2] Landing...")
        d.land()
        d.clear_leds()
        return MissionResult.SUCCESS

    # ── L3: Altitude up/down ──────────────────────────────────────────────────

    def _run_l3_altitude(self) -> MissionResult:
        """Take off low → climb → descend → land. Vertical-axis test."""
        d, cfg = self._d, self._cfg
        delta = cfg.l3_high_height - cfg.l3_low_height

        print("[L3] Arming...")
        d.arm()

        d.set_led(LedColor.GREEN)
        print(f"[L3] Takeoff → low {cfg.l3_low_height:.2f} m")
        # Temporarily override target height for the low takeoff
        original = cfg.hover_height
        cfg.hover_height = cfg.l3_low_height
        d.takeoff()
        cfg.hover_height = original

        d.hover(cfg.l3_hold_seconds)

        d.set_led(LedColor.BLUE)
        print(f"[L3] Climbing +{delta:.2f} m → {cfg.l3_high_height:.2f} m")
        d.change_height(+delta)
        d.hover(cfg.l3_hold_seconds)

        d.set_led(LedColor.ORANGE)
        print(f"[L3] Descending -{delta:.2f} m → {cfg.l3_low_height:.2f} m")
        d.change_height(-delta)
        d.hover(cfg.l3_hold_seconds)

        d.set_led(LedColor.RED)
        print("[L3] Landing...")
        d.land()
        d.clear_leds()
        return MissionResult.SUCCESS

    # ── L4: Full waypoint mission ─────────────────────────────────────────────

    def _run_l4_waypoints(self) -> MissionResult:
        """Full square mission with battery monitoring at each waypoint."""
        d, cfg = self._d, self._cfg

        print("[L4] Arming...")
        d.arm()

        d.set_led(LedColor.GREEN)
        print(f"[L4] Takeoff → {cfg.hover_height:.2f} m")
        d.takeoff()
        d.hover(cfg.hover_after_takeoff)

        d.set_led(LedColor.BLUE)
        print(f"[L4] {len(cfg.mission_waypoints)} waypoints @ {cfg.waypoint_speed:.2f} m/s")
        for i, wp in enumerate(cfg.mission_waypoints):
            x, y = wp[0], wp[1]
            z    = wp[2] if len(wp) > 2 else None
            yaw  = wp[3] if len(wp) > 3 else None
            print(f"[L4]   WP{i+1}: ({x:.2f}, {y:.2f})")
            d.fly_to(x, y, z=z, yaw=yaw, speed=cfg.waypoint_speed)
            px, py = d.position
            print(f"[L4]     reached ({px:.2f}, {py:.2f})")

            v = d.battery
            if v > 0 and v < cfg.land_battery_v:
                print(f"[L4] Battery critical ({v:.2f} V) — aborting!")
                d.set_led(LedColor.RED)
                d.land()
                return MissionResult.BATTERY_LOW

        d.set_led(LedColor.ORANGE)
        print(f"[L4] End hold {cfg.hover_at_end:.1f} s")
        d.hover(cfg.hover_at_end)

        d.set_led(LedColor.RED)
        print("[L4] Landing...")
        d.land()
        d.clear_leds()
        return MissionResult.SUCCESS
