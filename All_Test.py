#!/usr/bin/env python3
# File name: raspi_toolkit.py

import os
import subprocess
import sys

# Function definitions
def run_system_update():
    """Run system update"""
    print("\nUpdating system...")
    subprocess.run(["sudo", "apt", "update"])
    subprocess.run(["sudo", "apt", "upgrade", "-y"])
    input("\nSystem update completed! Press Enter to return to the main menu...")

def run_key_board():
    """Run sensor monitor"""
    print("\nStarting Key_Board_Test...")
    subprocess.run(["python3", "Desktop/Notebook_Test/Key_Board_UK.py"])
    input("\nPress Enter to return to the main menu...")

def run_screen_rgb():
    """Run Screen RGB Detection"""
    print("\nStarting Screen RGB ...")
    subprocess.run(["python3", "Desktop/Notebook_Test/Screen_Color.py"])
    input("\nPress Enter to return to the main menu...")

def run_camera():
    """run_camera"""
    print("\nrun_camera information:")
    subprocess.run(["sudo", "apt", "install", "ffmpeg"])
    subprocess.run(["ffmpeg", "-i", "/dev/video0", "-frames:v", "1", "Desktop/output.jpg"])
    subprocess.run(["ffmpeg", "-i", "/dev/video0", "-t", "10", "Desktop/output.mp4"])
    input("\nPress Enter to return to the main menu...")

def run_recording_playback():
    """run_Recording_playback"""
    print("\nrun_Recording information:")
    subprocess.run(["sudo", "apt", "install", "alsa-utils"])
    subprocess.run(["arecord", "-d", "10", "-f", "cd", "test_recording.wav"])
    subprocess.run(["aplay", "test_recording.wav"])
    input("\nPress Enter to return to the main menu...")

def run_brightness():
    """run_brightness"""
    print("\nrun_brightness information:")
    subprocess.run(["sudo", "apt", "install", "ddcui", "ddcutil"])
    subprocess.run(["python3", "Desktop/Notebook_Test/KEY_Light.py"])
    subprocess.run(["aplay", "test_recording.wav"])
    input("\nPress Enter to return to the main menu...")

def run_electricity_power():
    """run_electricity power"""
    print("\nrun_electricity power information:")
    subprocess.run(["python3", "Desktop/Notebook_Test/CW2217_one.py"])
    input("\nPress Enter to return to the main menu...")





def exit_program():
    """Exit the program"""
    print("\nThank you for using the Argon_One_Text Toolkit!")
    sys.exit(0)

# Main menu function
def main_menu():
    os.system('clear')  # Clear screen
    
    print("""
    ============================
      Argon_One_Text Toolkit v1.0
    ============================
    1. System Update
    2. Keyboard Detection
    3. Screen RGB Detection
    4. Camera Detection
    5. Recording playback Detection
    6. Brightness Detection
    7. Electricity Power_Detection
    0. Exit
    ============================
    """)
    
    choice = input("Please enter the option number: ")
    
    # Option mapping dictionary
    menu_options = {
        '1': run_system_update,
        '2': run_key_board,
        '3': run_screen_rgb,
        '4': run_camera,
        '5': run_recording_playback,
        '6': run_brightness,
        '7': run_electricity_power,
        '0': exit_program
    }
    
    # Execute the selected function
    if choice in menu_options:
        menu_options[choice]()
    else:
        print("\nInvalid option, please try again!")
        input("Press Enter to continue...")

# Program entry
if __name__ == "__main__":
    while True:
        main_menu()
