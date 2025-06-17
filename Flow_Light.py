import RPi.GPIO as GPIO
import time


led_pins = [i for i in range(28)] 


GPIO.setmode(GPIO.BCM)


for pin in led_pins:
    GPIO.setup(pin, GPIO.OUT)

try:
    while True:
        
        for pin in led_pins:
            GPIO.output(pin, GPIO.HIGH)  
            time.sleep(0.1)               
 #           GPIO.output(pin, GPIO.LOW)    

        
        for pin in reversed(led_pins):
 #           GPIO.output(pin, GPIO.HIGH) 
            GPIO.output(pin, GPIO.LOW) 
            time.sleep(0.1)               
 #           GPIO.output(pin, GPIO.LOW)    

except KeyboardInterrupt:
    print("over")

finally:
    GPIO.cleanup()  
