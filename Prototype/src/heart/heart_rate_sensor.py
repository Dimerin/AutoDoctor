import time as Time
import threading
import RPi.GPIO as GPIO

class HeartRateSensor:
    
    def __init__(self, gpio_pin_hr : int):
        self._gpio_pin_hr = gpio_pin_hr
        self._last_pulse_time = None
        self._last_heart_rate_sample = None
        self._semaphore_hr = threading.Lock()

    def setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self._gpio_pin_hr, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)         
        
        GPIO.add_event_detect(
            self._gpio_pin_hr,
            GPIO.RISING,
            callback=self._default_ISR,
            bouncetime=260
        )
        
    def _default_ISR(self, channel):
        if channel != self._gpio_pin_hr:
            return
        current_time = Time.time()
        if self._last_pulse_time is not None:
            interval = current_time - self._last_pulse_time
            if interval > 0:
                bpm = 60 / interval
                #print(f"Battito rilevato (INT): BPM = {bpm:.1f}")
                with self._semaphore_hr:
                    self._last_heart_rate_sample = bpm
 
                # print("Primo impulso rilevato (INT)...")

        self._last_pulse_time = current_time

    def get_heart_rate(self):
        with self._semaphore_hr:
            if self._last_heart_rate_sample is not None:
                return self._last_heart_rate_sample
            else:
                return 0.0
                
    def cleanup(self):
        GPIO.cleanup(self._gpio_pin_hr)
