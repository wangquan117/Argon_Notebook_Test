import RPi.GPIO as GPIO
import time


led_pins = [i for i in range(27)] 


GPIO.setmode(GPIO.BCM)


for pin in led_pins:
    GPIO.setup(pin, GPIO.OUT)

try:
    loop_count = 0
    max_loop = 2
    while loop_count<max_loop:
        
        for pin in led_pins:
            GPIO.output(pin, GPIO.HIGH)  
            time.sleep(0.1)               


        
        for pin in reversed(led_pins):

            GPIO.output(pin, GPIO.LOW) 
            time.sleep(0.1)  
        
        loop_count += 1 
 

except KeyboardInterrupt:
    print("over")

finally:
    GPIO.cleanup()  
