import time
from .config import DroneConfig
from .enums import MissionResult, MissionLevel
from .interface import DroneInterface
from .controller import MissionController
from .logger import FlightLogger


class DroneService:
    def __init__(self, cfg: DroneConfig) -> None:
        self._cfg        = cfg
        self._interface  = DroneInterface(cfg)
        self._controller = MissionController(self._interface, cfg)
        self._logger     = FlightLogger(self._interface, cfg)

    def run(self, level: MissionLevel) -> MissionResult:
        result = MissionResult.EMERGENCY
        try:
            print(f"[SVC] Connecting to {self._cfg.ip}...")
            self._interface.connect()
            print("[SVC] Waiting for telemetry (2 s)...")
            time.sleep(2)

            if not self._controller.preflight_ok(level):
                return MissionResult.SENSOR_FAIL

            # L0/L1 don't fly → no CSV needed
            if level not in (MissionLevel.L0_ARM, MissionLevel.L1_TELEMETRY):
                self._logger.start()

            result = self._controller.run(level)

        except KeyboardInterrupt:
            print("\n[SVC] Ctrl-C — emergency stop!")
            self._interface.emergency_stop()
            result = MissionResult.ABORTED

        except Exception as exc:
            print(f"[SVC] Unhandled error: {exc}")
            self._interface.emergency_stop()
            raise

        finally:
            self._logger.stop()
            self._logger.preview()
            self._interface.clear_leds()
            self._interface.disconnect()
            print(f"[SVC] Done — result: {result.name}")

        return result
