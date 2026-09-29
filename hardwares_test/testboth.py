import lgpio # type: ignore
import time

LED_PIN = 18

MOTOR_IN1 = 14
MOTOR_IN2 = 15

h = lgpio.gpiochip_open(0)

lgpio.gpio_claim_output(h, LED_PIN, 0)
lgpio.gpio_claim_output(h, MOTOR_IN1, 0)
lgpio.gpio_claim_output(h, MOTOR_IN2, 0)


def light_on():
    lgpio.gpio_write(h, LED_PIN, 1)
    print("LIGHT ON")


def light_off():
    lgpio.gpio_write(h, LED_PIN, 0)
    print("LIGHT OFF")


def fan_on():
    lgpio.gpio_write(h, MOTOR_IN1, 1)
    lgpio.gpio_write(h, MOTOR_IN2, 0)
    print("FAN ON")


def fan_off():
    lgpio.gpio_write(h, MOTOR_IN1, 0)
    lgpio.gpio_write(h, MOTOR_IN2, 0)
    print("FAN OFF")


try:
    while True:

        print()
        print("===== DEVICE CONTROL =====")
        print("1. Light ON")
        print("2. Light OFF")
        print("3. Fan ON")
        print("4. Fan OFF")
        print("5. Exit")

        choice = input("Choose: ")

        if choice == "1":
            light_on()

        elif choice == "2":
            light_off()

        elif choice == "3":
            fan_on()

        elif choice == "4":
            fan_off()

        elif choice == "5":
            break

        else:
            print("Invalid choice")

finally:
    # Safety: turn everything OFF
    light_off()
    fan_off()

    lgpio.gpiochip_close(h)

    print("GPIO released")