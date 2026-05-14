import os
import time
from .config import DroneConfig
from .interface import DroneInterface


class FlightLogger:
    def __init__(self, drone: DroneInterface, cfg: DroneConfig) -> None:
        self._drone    = drone
        self._cfg      = cfg
        self._filename: str | None = None
        self._active   = False

    def start(self) -> None:
        if not self._cfg.log_to_csv:
            return
        stamp = time.strftime("%Y%m%d_%H%M%S")
        base, ext = os.path.splitext(self._cfg.log_filename)
        self._filename = f"{base}_{stamp}{ext}"
        self._drone.start_logging(self._filename)
        self._active = True
        print(f"[LOG] Recording → {self._filename}")

    def stop(self) -> None:
        if not self._active:
            return
        self._drone.stop_logging()
        self._active = False
        print(f"[LOG] Saved {self._filename}")

    def preview(self, rows: int = 5) -> None:
        if not self._filename or not os.path.exists(self._filename):
            return
        print(f"[LOG] Preview ({rows} rows):")
        with open(self._filename) as f:
            for line in f.readlines()[: rows + 1]:
                print(f"  {line.rstrip()}")
