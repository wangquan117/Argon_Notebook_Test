#!/usr/bin/env python3
# File name: raspi_toolkit.py

import os
import subprocess
import sys
import traceback

# Function definitions
def run_system_update():
    """Run system update"""
    print("\nUpdating system...")
    subprocess.run(["sudo", "apt", "update"])
    subprocess.run(["sudo", "apt", "upgrade", "-y"])
    print("\nSystem update completed!")
    return True

def run_key_board():
    """Run sensor monitor"""
    print("\nStarting Key_Board_Test...")
    subprocess.run(["python3", "argon-scripts/Argon_Notebook_Test-main/Key_Board_US.py"])
    return True

def run_screen_rgb():
    """Run Screen RGB Detection"""
    print("\nStarting Screen RGB ...")
    subprocess.run(["python3", "argon-scripts/Argon_Notebook_Test-main/Screen_Color.py"])
    return True

def run_camera():
    """run_camera"""
    print("\nrun_camera information:")
    subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"])
    subprocess.run(["ffmpeg", "-i", "/dev/video0", "-frames:v", "1", "Desktop/output.jpg"])
    subprocess.run(["ffmpeg", "-i", "/dev/video0", "-t", "10", "Desktop/output.mp4"])
    return True

def run_recording_playback():
    """run_Recording_playback"""
    print("\nrun_Recording information:")
    subprocess.run(["sudo", "apt", "install", "-y", "alsa-utils"])
    subprocess.run(["arecord", "-d", "10", "-f", "cd", "test_recording.wav"])
    subprocess.run(["aplay", "test_recording.wav"])
    return True

def run_brightness():
    """run_brightness"""
    print("\nrun_brightness information:")
    subprocess.run(["sudo", "apt", "install", "-y", "ddcui", "ddcutil"])
    subprocess.run(["sudo", "python3", "Desktop/Notebook_Test/KEY_Light_init.py"])
    return True

def run_electricity_power():
    """run_electricity power"""
    print("\nrun_electricity power information:")
    subprocess.run(["python3", "argon-scripts/Argon_Notebook_Test-main/CW2217_one.py"])
    return True
    
 
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
    
    failed_tests = []
    
    print("\n" + "="*50)
    print("Starting Automated Testing Sequence")
    print("="*50)
    
    for name, test_func in test_cases:
        print(f"\n>>> Starting test: {name}")
        try:
            success = test_func()
            if success:
                print(f"[?] {name} - PASSED")
            else:
                print(f"[?] {name} - FAILED (returned False)")
                failed_tests.append(name)
        except Exception as e:
            print(f"[?] {name} - FAILED with error: {str(e)}")
            print(f"Error details: {traceback.format_exc().splitlines()[-1]}")
            failed_tests.append(name)
            continue
    
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    
    if failed_tests:
        print("\nThe following tests failed:")
        for test in failed_tests:
            print(f"  - {test}")
    else:
        print("\nAll tests completed successfully!")
    
    print(f"\nTotal tests: {len(test_cases)}, Passed: {len(test_cases) - len(failed_tests)}, Failed: {len(failed_tests)}")
    input("\nPress Enter to return to the main menu...")
 
 
# Main menu function
def main_menu():
    os.system('clear')  # Clear screen
    
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
    
    # Option mapping dictionary
    menu_options = {
        '1': run_system_update,
        '2': run_all_tests,
        '3': run_brightness,
        '0': exit_program
    }
    
    # Execute the selected function
    if choice in menu_options:
        try:
            if choice != '8':  # For individual tests
                menu_options[choice]()
                input("\nTest completed. Press Enter to return to the main menu...")
            else:  # For run_all_tests
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
