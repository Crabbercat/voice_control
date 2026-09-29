import lgpio
import time

IN1 = 14
IN2 = 15

h = lgpio.gpiochip_open(0)

try:
    lgpio.gpio_claim_output(h, IN1, 0)
    lgpio.gpio_claim_output(h, IN2, 0)

    print("DC Motor test")
    print("Press Ctrl+C to stop")

    while True:

        # =========================
        # MOTOR ON
        # =========================

        print("Motor ON")

        lgpio.gpio_write(h, IN1, 1)
        lgpio.gpio_write(h, IN2, 0)

        time.sleep(3)

        # =========================
        # MOTOR OFF
        # =========================

        print("Motor OFF")

        lgpio.gpio_write(h, IN1, 0)
        lgpio.gpio_write(h, IN2, 0)

        time.sleep(3)

except KeyboardInterrupt:
    print("\nStopping motor...")

finally:
    # Always stop motor
    lgpio.gpio_write(h, IN1, 0)
    lgpio.gpio_write(h, IN2, 0)

    lgpio.gpiochip_close(h)

    print("GPIO released")