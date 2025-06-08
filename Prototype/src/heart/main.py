import time as Time
from heart_rate_sensor import HeartRateSensor

if __name__ == "__main__":
    heart_rate_sensor = HeartRateSensor(gpio_pin_hr=4)
    heart_rate_sensor.setup()

    try:
        print("Sistema in ascolto (interrupt attivo)...")
        while True:
            Time.sleep(1)  # Il thread principale dorme
    except KeyboardInterrupt:
        print("\nTerminazione da tastiera...")
    finally:
        heart_rate_sensor.cleanup()