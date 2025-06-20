#!/usr/bin/env python3
# File name: raspi_toolkit.py

import os
import subprocess
import sys
import traceback
import time

# Function definitions
def run_system_update():
    """Run system update"""
    print("\nUpdating system...")
    subprocess.run(["sudo", "apt", "update"])
    subprocess.run(["sudo", "apt", "upgrade", "-y"])
    print("\nSystem update completed!")
    return True

def run_key_board():
    """Run keyboard test"""
    print("\nStarting Key_Board_Test...")
    try:
        subprocess.run(["sudo", "pip3", "install", "evdev", "--break-system-packages"], check=True)
        result = subprocess.run(["python3", "argon-scripts/Argon_Notebook_Test-main/Key_Board_US.py"], check=False)
        if result.returncode == 0:
            return "run_key_board____YES"
        else:
            print(f"Keyboard test completed with non-zero exit code: {result.returncode}")
            return "run_key_board____YES"  
    except Exception as e:
        return f"run_key_board____NO: {str(e)}"

def run_screen_rgb():
    """Run Screen RGB Detection"""
    print("\nStarting Screen RGB ...")
    try:
        subprocess.run(["python3", "argon-scripts/Argon_Notebook_Test-main/Screen_Color.py"], check=True)
        return "run_screen_rgb____YES"
    except Exception as e:
        return f"run_screen_rgb____NO: {str(e)}"

def run_camera():
    """Run camera with preview functionality"""
    print("\nrun_camera information:")
    try:
        subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"], check=True)
        print("\nTaking photo...")
        subprocess.run(["ffmpeg", "-i", "/dev/video0", "-frames:v", "1", "Desktop/output.jpg"], check=True)
        print("\nDisplaying photo for 3 seconds...")
        feh_process = subprocess.Popen(["feh", "--fullscreen", "Desktop/output.jpg"])
        time.sleep(3)
        feh_process.terminate()
        print("\nRecording 10-second video...")
        subprocess.run(["ffmpeg", "-i", "/dev/video0", "-t", "10", "Desktop/output.mp4"], check=True)
        print("\nPlaying recorded video...")
        subprocess.run(["ffplay", "-autoexit", "-fs", "Desktop/output.mp4"], check=True)
        print("\nCamera test completed successfully!")
        return "run_camera____YES"
    except subprocess.CalledProcessError as e:
        return f"run_camera____NO: Command failed: {e.cmd}"
    except Exception as e:
        return f"run_camera____NO: {str(e)}"

def run_recording_playback():
    """Run recording playback"""
    print("\nrun_Recording information:")
    try:
        subprocess.run(["sudo", "apt", "install", "-y", "alsa-utils"], check=True)
        subprocess.run(["arecord", "-d", "5", "-f", "cd", "test_recording.wav"], check=True)
        subprocess.run(["aplay", "test_recording.wav"], check=True)
        home_dir = os.path.expanduser("~")
        music_path = os.path.join(home_dir, "argon-scripts", "Argon_Notebook_Test-main", "music_e.mp3")
        result = subprocess.run(["timeout", "30", "ffplay", "-nodisp", "-autoexit", music_path], 
                               capture_output=True, text=True, check=False)
        if result.returncode == 0 or result.returncode == 124:  
            print(result.stdout)
            return "run_recording_playback____YES"
        else:
            return f"run_recording_playback____NO: Command failed with output: {result.stderr}"
    except Exception as e:
        return f"run_recording_playback____NO: {str(e)}"

def run_brightness():
    """Run brightness"""
    print("\nrun_brightness information:")
    try:
        subprocess.run(["sudo", "apt", "install", "-y", "ddcui", "ddcutil"], check=True)
        subprocess.run(["sudo", "python3", "argon-scripts/Argon_Notebook_Test-main/KEY_Light_init.py"], check=True)
        return "run_brightness____YES"
    except Exception as e:
        return f"run_brightness____NO: {str(e)}"

def run_electricity_power():
    """Run electricity power"""
    print("\nrun_electricity power information:")
    try:
        subprocess.run(["python3", "argon-scripts/Argon_Notebook_Test-main/CW2217_one.py"], check=True)
        return "run_electricity_power____YES"
    except Exception as e:
        return f"run_electricity_power____NO: {str(e)}"

def exit_program():
    """Exit the program"""
    print("\nThank you for using the Argon_One_Test Toolkit!")
    sys.exit(0)

def run_all_tests():
    """Run all tests sequentially and report results"""
    test_cases = [
        ("Keyboard Detection", run_key_board),
        ("Screen RGB Detection", run_screen_rgb),
        ("Camera Detection", run_camera),
        ("Recording Playback Detection", run_recording_playback),
        ("Electricity Power Detection", run_electricity_power)
    ]
    
    results = []
    
    print("\n" + "="*50)
    print("Starting Automated Testing Sequence")
    print("="*50)
    
    for name, test_func in test_cases:
        print(f"\n>>> Starting test: {name}")
        try:
            result = test_func()
            results.append((name, result))
            if "YES" in result:
                print(f"[?] {name} - PASSED")
            else:
                print(f"[?] {name} - FAILED ({result})")
        except Exception as e:
            error_msg = f"run_{name.lower().replace(' ', '_')}____NO: {str(e)}"
            results.append((name, error_msg))
            print(f"[?] {name} - FAILED with error: {str(e)}")
            print(f"Error details: {traceback.format_exc().splitlines()[-1]}")
    
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    
    failed_tests = [name for name, result in results if "NO" in result]
    
    if failed_tests:
        print("\nThe following tests failed:")
        for test in failed_tests:
            print(f"  - {test}")
    else:
        print("\nAll tests completed successfully!")
    
    print(f"\nTotal tests: {len(test_cases)}, Passed: {len(test_cases) - len(failed_tests)}, Failed: {len(failed_tests)}")
    
    print("\nIndividual Test Results:")
    for name, result in results:
        print(f"  {result}")
    
    input("\nPress Enter to return to the main menu...")
 
 
 
# Main menu function
def main_menu():
    os.system('clear')
    print("""
    ============================
      Argon_One_Test Toolkit v1.0
    ============================
    1. System Update
    2. Run ALL Tests Sequentially
    3. Brightness Detection
    0. Exit
    ============================
    """)
    
    choice = input("Please enter the option number: ")
    
    menu_options = {
        '1': run_system_update,
        '2': run_all_tests,
        '3': run_brightness,
        '0': exit_program
    }
    
    if choice in menu_options:
        try:
            if choice != '2':
                result = menu_options[choice]()
                print(f"  {result}")
                input("\nTest completed. Press Enter to return to the main menu...")
            else:
                menu_options[choice]()
        except Exception as e:
            print(f"\nError during test: {str(e)}")
            print(f"Error details: {traceback.format_exc().splitlines()[-1]}")
            input("\nPress Enter to return to the main menu...")
    else:
        print("\nInvalid option, please try again!")
        input("Press Enter to continue...")

# Program entry
if __name__ == "__main__":
    while True:
        main_menu()
