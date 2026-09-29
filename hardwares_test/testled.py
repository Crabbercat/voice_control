import lgpio
import time

LED_PIN = 16

h = lgpio.gpiochip_open(0)

try:
    lgpio.gpio_claim_output(h, LED_PIN, 0)

    print("LED test started")

    while True:
        print("LED ON")
        lgpio.gpio_write(h, LED_PIN, 1)
        time.sleep(2)

        print("LED OFF")
        lgpio.gpio_write(h, LED_PIN, 0)
        time.sleep(2)

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    lgpio.gpio_write(h, LED_PIN, 0)
    lgpio.gpiochip_close(h)
    print("GPIO released")