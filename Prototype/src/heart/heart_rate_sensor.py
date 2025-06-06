import time as Time
import threading
import RPi.GPIO as GPIO

class HeartRateSensor:
    
    def __init__(self, gpio_pin_hr : int, gpio_pin_led : int):
        self._gpio_pin_hr = gpio_pin_hr
        self._gpio_pin_led = gpio_pin_led
        self._last_pulse_time = None
        
        self.blink_thread = threading.Thread(target=self._blinking, daemon=True)
        self.blinking_condition = threading.Condition()

    def setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self._gpio_pin_hr, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)         
        GPIO.setup(self._gpio_pin_led, GPIO.OUT)
                
        self.blink_thread.start()
        
        GPIO.add_event_detect(
            self._gpio_pin_hr,
            GPIO.RISING,
            callback=self._default_ISR,
            bouncetime=260
        )

    def blink(self):
        with self.blinking_condition:
            self.blinking_condition.notify()
        
    def _default_ISR(self, channel):
        if channel != self._gpio_pin_hr:
            return
        current_time = Time.time()
        if self._last_pulse_time is not None:
            interval = current_time - self._last_pulse_time
            if interval > 0:
                bpm = 60 / interval
                print(f"Battito rilevato (INT): BPM = {bpm:.1f}")
        else:
            print("Primo impulso rilevato (INT)...")

        self._last_pulse_time = current_time
        self.blink()
        
    def _blinking(self):
        while True:
            with self.blinking_condition:
                self.blinking_condition.wait()
            GPIO.output(self._gpio_pin_led, GPIO.HIGH)
            Time.sleep(0.3)
            GPIO.output(self._gpio_pin_led, GPIO.LOW)
                
    def cleanup(self):
        GPIO.cleanup(self._gpio_pin_hr)
        
        if self.blink_thread.is_alive():
            with self.blinking_condition:
                self.blinking_condition.notify()
            self.blink_thread.join(timeout=1)
    
        GPIO.cleanup(self._gpio_pin_led)
