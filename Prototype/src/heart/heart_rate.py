import time as Time
import threading
import RPi.GPIO as GPIO

BLINKING_PERIOD = 0.3

class HRDriver:
    """ class driver for the Heart Rate Sensor (Polar T34) """
    def __init__(self, gpio_pin_hr, gpio_pin_led):
        self._gpio_pin = gpio_pin_hr
        self._gpio_pin_led = gpio_pin_led
        self.timeseries: list = []
        self.shared_timestamp = None
        self.wake_condition: threading.Condition = None
        self.blink_thread: threading.Thread = None
        self.blinking_condition: threading.Condition = None

    def setup(self):
        """ sensor driver setup """
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self._gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # PullDown interno attivo
        
        GPIO.setwarnings(False)
        GPIO.setup(self._gpio_pin_led, GPIO.OUT)
        
        self.blinking_condition = threading.Condition()
        self.blink_thread = threading.Thread(target=self._blinking, daemon=True)
        self.blink_thread.start()

    def read_sample(self):
        """ ritorna il valore digitale letto dal gpio_pin. DA USARE SOLO IN MODALITA' POLLING """
        return GPIO.input(self._gpio_pin)

    def set_interrupt_mode(self, shared_timestamp, wake_condition, gpio_event=GPIO.RISING, interrupt_handler=None):
        """ abilita la modalità di gestione ad Interrupt per il sampling """
        self.shared_timestamp = shared_timestamp
        self.wake_condition = wake_condition

        GPIO.add_event_detect(self._gpio_pin,
                              gpio_event,
                              callback=self._default_ISR if (interrupt_handler is None) else interrupt_handler,
                              bouncetime=260)  # debounce a 260ms

    def _default_ISR(self, channel):
        """ Interrupt Service Routine breve """
        self.shared_timestamp[0] = Time.time()
        with self.wake_condition:
            self.wake_condition.notify()
        # Per analisi tempi, opzionale:
        # comp_time = Time.time() - self.shared_timestamp[0]
        # with open('ComputationTime_ISR.csv', 'a') as file:
        #     file.write(str(comp_time) + "\n")

    def led_on(self):
        GPIO.output(self._gpio_pin_led, GPIO.HIGH)

    def led_off(self):
        GPIO.output(self._gpio_pin_led, GPIO.LOW)

    def blink(self):
        """ sveglia il thread di blinking """
        with self.blinking_condition:
            self.blinking_condition.notify()

    def _blinking(self):
        """ thread che fa lampeggiare il led """
        while True:
            with self.blinking_condition:
                self.blinking_condition.wait()
            _blink_number = 5
            while _blink_number > 0:
                self.led_on()
                Time.sleep(BLINKING_PERIOD)
                self.led_off()
                Time.sleep(BLINKING_PERIOD)
                _blink_number -= 1

#if __name__ == "__main__":
#    hrDriver = HRDriver(gpio_pin_hr=4, gpio_pin_led=17)
#    hrDriver.setup()
#
#    try:
#        print("Avvio campionamento GPIO...")
#        while True:
#            sample = hrDriver.read_sample()
#            print(f"Valore GPIO: {sample}")
#            Time.sleep(0.1)  # campiona ogni 100 ms (regolabile)
#    except KeyboardInterrupt:
#        print("Programma terminato dall'utente.")
#    finally:
#        GPIO.cleanup()
        
if __name__ == "__main__":
    hrDriver = HRDriver(gpio_pin_hr=4, gpio_pin_led=17)
    hrDriver.setup()

    last_pulse_time = None

    try:
        print("Avvio lettura in modalità polling...")
        while True:
            sample = hrDriver.read_sample()
            #print(f"Valore GPIO: {sample}")
            if sample == 1:
                current_time = Time.time()
                if last_pulse_time is not None:
                    interval = current_time - last_pulse_time
                    if interval > 0:
                        bpm = 60 / interval
                        print(f"Battito rilevato: BPM = {bpm:.1f}")
                else:
                    print("Primo impulso rilevato, attendo il successivo...")

                last_pulse_time = current_time
                hrDriver.blink()
                # Attendi un po' per evitare letture ripetute dello stesso impulso
                Time.sleep(0.3)
            else:
                Time.sleep(0.01)
    except KeyboardInterrupt:
        print("Programma terminato dall'utente.")
    finally:
        GPIO.cleanup()

