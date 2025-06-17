from evdev import InputDevice, categorize, ecodes
import subprocess

device = InputDevice('/dev/input/event13')

def get_current_brightness():
    try:
        output = subprocess.check_output(["ddcutil", "getvcp", "10"], text=True)
        value = output.split("=")[-1].split()[0]
        return int(value)
    except Exception as e:
        print(f"get_light_false: {e}")
        return 50  

def adjust_brightness(delta):
    global current_brightness  
    
    new_value = max(10, min(100, current_brightness + delta))  
    print(f"ctrl_light: {current_brightness}% -> {new_value}%")
    subprocess.run(["ddcutil", "setvcp", "10", str(new_value)], check=True)
    current_brightness = new_value  

try:
    current_brightness = get_current_brightness()  

    for event in device.read_loop():
        if event.type == ecodes.EV_KEY:
            key_event = categorize(event)
            
            if key_event.keycode == "KEY_ESC" and event.value == 1:
                print("\nESC pressed, exiting...")
                break
                
            if event.value == 1:  
                if key_event.keycode == "KEY_BRIGHTNESSDOWN":
                    adjust_brightness(-10)
                elif key_event.keycode == "KEY_BRIGHTNESSUP":
                    adjust_brightness(10)
except KeyboardInterrupt:
    print("\nout")
finally:
    device.close()
