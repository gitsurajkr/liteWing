# drone/interface.py  –  The ONLY place LiteWing is imported.
# Every other module talks to DroneInterface, never to LiteWing directly.

from litewing import LiteWing, SensorData
from .config import DroneConfig
from .enums import LedColor


class DroneInterface:
    """
    Thin adapter around LiteWing. Translates our config/enums into raw
    LiteWing calls so the rest of the codebase never touches the library.
    """

    def __init__(self, cfg: DroneConfig) -> None:
        self._cfg = cfg
        self._drone = LiteWing(cfg.ip)
        self._apply_config()

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def connect(self) -> None:
        self._drone.connect()

    def disconnect(self) -> None:
        self._drone.disconnect()

    def arm(self) -> None:
        self._drone.arm()

    def takeoff(self) -> None:
        self._drone.takeoff(self._cfg.hover_height, self._cfg.takeoff_duration)

    def land(self) -> None:
        self._drone.land(self._cfg.landing_duration)

    def emergency_stop(self) -> None:
        self._drone.emergency_stop()

    # ── Motion ─────────────────────────────────────────────────────────────────

    def hover(self, seconds: float) -> None:
        self._drone.hover(seconds)

    def change_height(self, delta: float) -> None:
        """Climb (+) or descend (-) by delta metres while flying."""
        self._drone.change_height(delta)

    def fly_to(self, x: float, y: float,
               z: float | None = None,
               yaw: float | None = None,
               speed: float | None = None) -> None:
        self._drone.fly_to(
            x, y,
            z=z,
            yaw=yaw,
            speed=speed or self._cfg.waypoint_speed,
            threshold=self._cfg.waypoint_threshold,
        )

    # ── Sensors ────────────────────────────────────────────────────────────────

    @property
    def battery(self) -> float:
        return self._drone.battery

    @property
    def height(self) -> float:
        return self._drone.height

    @property
    def position(self) -> tuple[float, float]:
        return self._drone.position

    @property
    def is_connected(self) -> bool:
        return self._drone.is_connected

    @property
    def is_flying(self) -> bool:
        return self._drone.is_flying

    def read_sensors(self) -> SensorData:
        return self._drone.read_sensors()

    # ── LEDs ───────────────────────────────────────────────────────────────────

    def set_led(self, color: LedColor) -> None:
        r, g, b = color.value
        self._drone.set_led_color(r, g, b)

    def clear_leds(self) -> None:
        self._drone.clear_leds()

    # ── Logging pass-through ───────────────────────────────────────────────────

    def start_logging(self, filename: str) -> None:
        self._drone.start_logging(filename)

    def stop_logging(self) -> None:
        self._drone.stop_logging()

    # ── Internal ───────────────────────────────────────────────────────────────

    def _apply_config(self) -> None:
        d = self._drone
        c = self._cfg
        d.target_height             = c.hover_height
        d.descent_rate              = c.descent_rate
        d.default_takeoff_duration  = c.takeoff_duration
        d.default_landing_duration  = c.landing_duration
        d.debug_mode                = c.debug_mode
        d.enable_sensor_check       = c.enable_sensor_check
        d.hover_trim_pitch          = c.trim_pitch
        d.hover_trim_roll           = c.trim_roll
        d.waypoint_threshold        = c.waypoint_threshold
        d.waypoint_stabilization_time = c.waypoint_stabilize
