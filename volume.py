from evdev import InputDevice, categorize, ecodes
import subprocess
import time
import threading

# Use Consumer Control device (event13)
device = InputDevice('/dev/input/event13')

# Initialize volume state
is_muted = False
# Variables for continuous adjustment
continuous_adjustment = False
adjustment_direction = 0  # 0: no adjustment, -1: decrease, 1: increase
adjustment_lock = threading.Lock()

def get_current_volume():
    try:
        # Get current volume percentage
        output = subprocess.check_output(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], text=True)
       
        # Check if muted
        global is_muted
        if "MUTED" in output:
            is_muted = True
        else:
            is_muted = False
       
        # Parse volume percentage
        for part in output.split():
            if part.endswith('%'):
                return int(float(part[:-1]))
            elif part.replace('.', '').isdigit(): # Handle decimal format
                return int(float(part) * 100)
       
        return 50 # Default value
    except Exception as e:
        print(f"Failed to get volume: {e}")
        return 50 # Default value

def adjust_volume(delta):
    try:
        # Get current volume
        current_volume = get_current_volume()
       
        # Calculate new volume (0-100 range)
        new_volume = max(0, min(100, current_volume + delta))
       
        print(f"Adjusting volume: {current_volume}% -> {new_volume}%")
       
        # Set new volume (using percentage format)
        subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{new_volume}%"], check=True)
       
        # If previously muted and volume adjusted, unmute
        global is_muted
        if is_muted and delta != 0:
            subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"], check=True)
            is_muted = False
           
    except Exception as e:
        print(f"Failed to adjust volume: {e}")

def toggle_mute():
    global is_muted
    try:
        if is_muted:
            # Unmute
            subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"], check=True)
            is_muted = False
            print("Unmuted")
        else:
            # Mute
            subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1"], check=True)
            is_muted = True
            print("Muted")
    except Exception as e:
        print(f"Failed to toggle mute status: {e}")

def continuous_volume_adjustment():
    global continuous_adjustment, adjustment_direction
    while True:
        with adjustment_lock:
            if continuous_adjustment and adjustment_direction != 0:
                adjust_volume(adjustment_direction * 5)  
        time.sleep(0.1)  

adjustment_thread = threading.Thread(target=continuous_volume_adjustment, daemon=True)
adjustment_thread.start()

try:
    # Initialize by getting current volume status
    current_volume = get_current_volume()
    print(f"Current volume: {current_volume}%, Mute status: {is_muted}")
   
    for event in device.read_loop():
        if event.type == ecodes.EV_KEY:
            key_event = categorize(event)
            current_time = time.time()

            print(f"Key event: code={event.code}, value={event.value}, keycode={key_event.keycode}")

            if event.code == ecodes.KEY_MUTE:
                if event.value == 1:  
                    toggle_mute()
                continue

            if event.code == ecodes.KEY_VOLUMEDOWN:
                if event.value == 1:  
                    with adjustment_lock:
                        continuous_adjustment = True
                        adjustment_direction = -1
                elif event.value == 0: 
                    with adjustment_lock:
                        continuous_adjustment = False
                        adjustment_direction = 0

            elif event.code == ecodes.KEY_VOLUMEUP:
                if event.value == 1:  
                    with adjustment_lock:
                        continuous_adjustment = True
                        adjustment_direction = 1
                elif event.value == 0:  
                    with adjustment_lock:
                        continuous_adjustment = False
                        adjustment_direction = 0

except KeyboardInterrupt:
    print("\nProgram exited")
finally:
    device.close()
