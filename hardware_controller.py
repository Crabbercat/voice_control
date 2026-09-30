from __future__ import annotations

import atexit
import os
import threading


LED_PIN = 18
MOTOR_IN1 = 14
MOTOR_IN2 = 15


class HardwareController:
    """Control the light and fan GPIO outputs used by the voice commands."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._handle = None
        self._lgpio = None
        self._simulated = os.getenv("VOICE_CONTROL_SIMULATE", "").lower() in {
            "1",
            "true",
            "yes",
        }
        self._states = {"light": False, "fan": False}

        if not self._simulated:
            try:
                import lgpio

                self._lgpio = lgpio
                self._handle = lgpio.gpiochip_open(0)
                lgpio.gpio_claim_output(self._handle, LED_PIN, 0)
                lgpio.gpio_claim_output(self._handle, MOTOR_IN1, 0)
                lgpio.gpio_claim_output(self._handle, MOTOR_IN2, 0)
            except Exception as error:
                if self._handle is not None and self._lgpio is not None:
                    self._lgpio.gpiochip_close(self._handle)
                    self._handle = None
                if os.getenv("VOICE_CONTROL_STRICT_GPIO", "").lower() in {
                    "1",
                    "true",
                    "yes",
                }:
                    raise RuntimeError(f"GPIO initialization failed: {error}") from error
                self._simulated = True
                self._lgpio = None
                print(f"GPIO unavailable; using simulation mode: {error}")
        else:
            self._lgpio = None

        atexit.register(self.close)

    @property
    def mode(self) -> str:
        return "simulation" if self._simulated else "gpio"

    def status(self) -> dict[str, str]:
        with self._lock:
            return {
                "mode": self.mode,
                "light": "ON" if self._states["light"] else "OFF",
                "fan": "ON" if self._states["fan"] else "OFF",
            }

    def execute(self, command: str) -> dict[str, object]:
        actions = {
            "ALL_ON": self.all_on,
            "ALL_OFF": self.all_off,
            "LIGHT_ON": self.light_on,
            "LIGHT_OFF": self.light_off,
            "FAN_ON": self.fan_on,
            "FAN_OFF": self.fan_off,
        }
        action = actions.get(command)
        if action is None:
            return {"executed": False, "mode": self.mode, "message": "No action"}

        action()
        return {
            "executed": True,
            "mode": self.mode,
            "device": (
                "all"
                if command.startswith("ALL")
                else "light" if command.startswith("LIGHT") else "fan"
            ),
            "state": "on" if command.endswith("ON") else "off",
        }

    def all_on(self) -> None:
        with self._lock:
            self._write(LED_PIN, 1)
            self._write(MOTOR_IN1, 1)
            self._write(MOTOR_IN2, 0)
            self._states["light"] = True
            self._states["fan"] = True

    def all_off(self) -> None:
        with self._lock:
            self._write(LED_PIN, 0)
            self._write(MOTOR_IN1, 0)
            self._write(MOTOR_IN2, 0)
            self._states["light"] = False
            self._states["fan"] = False

    def light_on(self) -> None:
        with self._lock:
            self._write(LED_PIN, 1)
            self._states["light"] = True

    def light_off(self) -> None:
        with self._lock:
            self._write(LED_PIN, 0)
            self._states["light"] = False

    def fan_on(self) -> None:
        with self._lock:
            self._write(MOTOR_IN1, 1)
            self._write(MOTOR_IN2, 0)
            self._states["fan"] = True

    def fan_off(self) -> None:
        with self._lock:
            self._write(MOTOR_IN1, 0)
            self._write(MOTOR_IN2, 0)
            self._states["fan"] = False

    def _write(self, pin: int, value: int) -> None:
        if not self._simulated:
            self._lgpio.gpio_write(self._handle, pin, value)

    def close(self) -> None:
        with self._lock:
            if self._handle is None:
                return
            self._write(LED_PIN, 0)
            self._write(MOTOR_IN1, 0)
            self._write(MOTOR_IN2, 0)
            self._lgpio.gpiochip_close(self._handle)
            self._handle = None


hardware_controller = HardwareController()