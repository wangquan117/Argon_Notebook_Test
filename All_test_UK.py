import os
import subprocess
import sys
import traceback
import time
import threading
import select
import signal
import shutil


exit_program_event = threading.Event()

def clear_screen():
    try:
        print("\033[H\033[J", end="")
        print("\n" * 2, end="", flush=True)  
    except Exception as e:
        print(f"Error clearing screen: {e}", flush=True)
        os.system('cls' if os.name == 'nt' else 'clear')

def signal_handler(sig, frame, stop_event=None):
    print("\nExiting tests...", flush=True)
    if stop_event:
        stop_event.set()
    exit_program_event.set() 
    for cmd in ["arecord", "aplay", "ffmpeg", "ffplay"]:
        subprocess.run(["sudo", "pkill", "-f", cmd], check=False)
    try:
        subprocess.run(["stty", "sane"], check=False)
    except Exception as e:
        print(f"Error restoring terminal: {e}", flush=True)

signal.signal(signal.SIGINT, signal_handler)

def input_with_timeout(prompt, timeout=10):
    print(prompt, end='', flush=True)

    try:
        subprocess.run(["stty", "sane"], check=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Failed to restore terminal: {e}", flush=True)
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        if exit_program_event.is_set():
            return ""
        if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
            return sys.stdin.readline().strip()
        time.sleep(0.1)
    print(f"\nInput timed out after {timeout} seconds", flush=True)
    return ""

def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []
    try:
        subprocess.run(["pip3", "show", "evdev"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        missing.append("evdev (install with: sudo pip3 install evdev --break-system-packages)")
    try:
        subprocess.run(["which", "ffmpeg"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        missing.append("ffmpeg (install with: sudo apt install -y ffmpeg)")
    try:
        subprocess.run(["which", "ffplay"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        missing.append("ffplay (install with: sudo apt install -y ffmpeg)")
    try:
        subprocess.run(["which", "arecord"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        missing.append("arecord (install with: sudo apt install -y alsa-utils)")
    try:
        subprocess.run(["which", "aplay"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        missing.append("aplay (install with: sudo apt install -y alsa-utils)")
    try:
        subprocess.run(["which", "ddcutil"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        missing.append("ddcutil (install with: sudo apt install -y ddcutil)")
    
    if missing:
        print("\nMissing dependencies:", flush=True)
        for dep in missing:
            print(f"  - {dep}", flush=True)
        print("Would you like to continue without these dependencies? (y/n)", flush=True)
        choice = input().strip().lower()
        return choice == 'y'
    return True
    
def run_system_update():
    """Run system update"""
    print("\nUpdating system...", flush=True)
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "upgrade", "-y"], check=True)
        print("\nSystem update completed!", flush=True)
    except subprocess.CalledProcessError as e:
        print(f"System update failed: {e}", flush=True)
    return True

def run_key_board(stop_event=None):
    """Run keyboard test"""
    print("\nStarting Key_Board_Test...", flush=True)
    try:
        display = os.environ.get('DISPLAY')
        if not display:
            raise Exception("DISPLAY environment variable not set. Try running: export DISPLAY=:0")
        print(f"Using display: {display}", flush=True)
        
        subprocess.run(["sudo", "pip3", "install", "evdev", "--break-system-packages"], check=True)
        script_path = "argon-scripts/Argon_Notebook_Test-main/Key_Board_UK.py"
        if not os.path.exists(script_path):
            raise Exception(f"{script_path} not found. Please check the directory.")
        
        result = subprocess.run(
            ["python3", script_path],
            check=False,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Keyboard test completed successfully!", flush=True)
            return "run_key_board____YES"
        else:
            print(f"Keyboard test failed with exit code: {result.returncode}", flush=True)
            print(f"stdout: {result.stdout}", flush=True)
            print(f"stderr: {result.stderr}", flush=True)
            return f"run_key_board____NO: Exit code {result.returncode}"
    except Exception as e:
        print(f"Error running keyboard test: {str(e)}", flush=True)
        return f"run_key_board____NO: {str(e)}"

def run_screen_rgb(stop_event=None):
    """Run Screen RGB Detection"""
    print("\nStarting Screen RGB ...", flush=True)
    try:
        script_path = "argon-scripts/Argon_Notebook_Test-main/Screen_Color.py"
        if not os.path.exists(script_path):
            raise Exception(f"{script_path} not found. Please check the directory.")
        subprocess.run(["python3", script_path], check=True)
        return "run_screen_rgb____YES"
    except Exception as e:
        return f"run_screen_rgb____NO: {str(e)}"
        
def run_camera(stop_event):
    print("\nrun_camera information:", flush=True)
    try:
        display = os.environ.get('DISPLAY')
        if not display:
            raise Exception("No display available (DISPLAY not set). Set it with: export DISPLAY=:0")
        if not os.path.exists("/dev/video0"):
            raise Exception("/dev/video0 not found. Check camera connection or load v4l2loopback.")
        print(f"Using display: {display}", flush=True)

        print("\nStarting real-time video recording and playback (press 'q' in ffplay to return to main menu)...", flush=True)
        with open("ffmpeg.log", "w") as ffmpeg_log, open("ffplay.log", "w") as ffplay_log:
            ffmpeg_process = subprocess.Popen(
                ["ffmpeg", "-y", "-i", "/dev/video0", "-f", "mjpeg", "-"],
                stdout=subprocess.PIPE,
                stderr=ffmpeg_log,
                bufsize=0,
                close_fds=True
            )
            ffplay_process = subprocess.Popen(
                ["ffplay", "-i", "-", "-fflags", "nobuffer", "-autoexit"],
                stdin=ffmpeg_process.stdout,
                stderr=ffplay_log,
                close_fds=True
            )
            ffplay_process.wait()
            ffmpeg_process.terminate()
            try:
                ffmpeg_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                ffmpeg_process.kill()
                print("ffmpeg process killed due to timeout", flush=True)
        return "run_camera____YES"
    except Exception as e:
        stop_event.set()
        return f"run_camera____NO: {str(e)}"

def run_recording_playback(stop_event):
    print("\nrun_Recording information:", flush=True)
    try:
        subprocess.run(["sudo", "apt", "install", "-y", "alsa-utils"], check=True)
        subprocess.run(["amixer", "set", "Master", "50%"], check=True)
        subprocess.run(["amixer", "set", "Capture", "50%"], check=True)
        arecord_process = subprocess.Popen(
            ["arecord", "-f", "S16_LE", "-r", "44100", "-c", "2", "--buffer-size", "1024"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        aplay_process = subprocess.Popen(
            ["aplay", "-f", "S16_LE", "-r", "44100", "-c", "2", "--buffer-size", "1024"],
            stdin=arecord_process.stdout,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        
        while not stop_event.is_set():
            time.sleep(0.1)
        
        arecord_process.terminate()
        try:
            arecord_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            arecord_process.kill()
            print("arecord process killed due to timeout", flush=True)
        
        aplay_process.terminate()
        try:
            aplay_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            aplay_process.kill()
            print("aplay process killed due to timeout", flush=True)
        
        return "run_recording_playback____YES"
    except Exception as e:
        stop_event.set()
        print(f"Error in run_recording_playback: {str(e)}", flush=True)
        return f"run_recording_playback____NO: {str(e)}"
        
def run_brightness():
    """Run brightness"""
    print("\nrun_brightness information:", flush=True)
    try:
        subprocess.run(["sudo", "apt", "install", "-y", "ddcui", "ddcutil"], check=True)
        script_path = "argon-scripts/Argon_Notebook_Test-main/KEY_Light_init.py"
        if not os.path.exists(script_path):
            raise Exception(f"{script_path} not found. Please check the directory.")
        subprocess.run(["sudo", "python3", script_path], check=True)
        return "run_brightness____YES"
    except Exception as e:
        return f"run_brightness____NO: {str(e)}"

def run_electricity_power(stop_event=None):
    """Run electricity power"""
    print("\nrun_electricity power information:", flush=True)
    try:
        script_path = "argon-scripts/Argon_Notebook_Test-main/CW2217_one.py"
        if not os.path.exists(script_path):
            raise Exception(f"{script_path} not found. Please check the directory.")
        subprocess.run(["python3", script_path], check=True)
        return "run_electricity_power____YES"
    except Exception as e:
        return f"run_electricity_power____NO: {str(e)}"

def exit_program():
    """Exit the program"""
    print("\nThank you for using the Argon_One_Test Toolkit!", flush=True)
    sys.exit(0)

def print_test_results(test_cases, results):
    """Print test results"""
    print("\n" + "="*50, flush=True)
    print("Test Summary", flush=True)
    print("="*50, flush=True)
    
    failed_tests = []
    for name, result in results:
        if isinstance(result, tuple) and "NO" in result[0]:
            failed_tests.append(name)
        elif isinstance(result, str) and "NO" in result:
            failed_tests.append(name)
    
    if failed_tests:
        print("\nThe following tests failed:", flush=True)
        for test in failed_tests:
            print(f"  - {test}", flush=True)
    else:
        print("\nAll tests completed successfully!", flush=True)
    
    print(f"\nTotal tests: {len(test_cases)}, Passed: {len(test_cases) - len(failed_tests)}, Failed: {len(failed_tests)}", flush=True)
    
    print("\nIndividual Test Results:", flush=True)
    for name, result in results:
        if isinstance(result, tuple):
            print(f"  {result[0]}", flush=True)
        else:
            print(f"  {result}", flush=True)

def run_all_tests():
    """Run all tests sequentially and report results"""
    test_cases = [
        ("Keyboard Detection", run_key_board),
        ("Screen RGB Detection", run_screen_rgb),
        ("Electricity Power Detection", run_electricity_power),
        ("Camera Test", run_camera),
        ("Recording Playback Test", run_recording_playback),
    ]
    results = []
    threads = []
    stop_event = threading.Event()
    
    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, stop_event))
    
    print("\n" + "="*50, flush=True)
    print("Starting Automated Testing Sequence", flush=True)
    print("="*50, flush=True)
    
    if not check_dependencies():
        print("\nDependencies check failed. Please install missing packages or continue with 'y'.", flush=True)
        return False
    
    for name, test_func in test_cases[:3]:
        print(f"\n>>> Starting Test: {name}...", flush=True)
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            results.append((name, f"Test {name} Failed: {str(e)}"))

    for name, test_func in test_cases[3:]:
        print(f"\n>>> Starting Test: {name}...", flush=True)
        thread = threading.Thread(target=lambda n=name, f=test_func: results.append((n, f(stop_event))))
        thread.daemon = True
        threads.append(thread)
        thread.start()
    
    print("\nWaiting for real-time tests to complete. Press 'q' in ffplay to exit, or Enter to continue...", flush=True)
    try:
        input_with_timeout("", timeout=20)
    except KeyboardInterrupt:
        print("\nReceived Ctrl+C, stopping tests...", flush=True)
    finally:
        stop_event.set()
    
    print("\nWaiting for all tests to complete...", flush=True)
    for i, thread in enumerate(threads):
        thread.join(timeout=10)  
        if thread.is_alive():
            results.append((test_cases[i+3][0], f"{test_cases[i+3][0]}____NO: Thread timed out"))
            print(f"Warning: Test {test_cases[i+3][0]} did not terminate in time", flush=True)
    
    print("\nCleaning up any remaining processes...", flush=True)
    for cmd in ["arecord", "aplay", "ffmpeg", "ffplay"]:
        subprocess.run(["pkill", "-15", "-f", cmd], check=False)
        time.sleep(0.1)
    
    if exit_program_event.is_set():
        print("\nResults may be incomplete due to early exit.", flush=True)
        print_test_results(test_cases, results)
        print("\nReturning to main menu in 5 seconds...", flush=True)
        time.sleep(5)
        print("\nReturning to main menu...", flush=True)
        return True
    
    print_test_results(test_cases, results)
    
    try:
        input_with_timeout("\nPress Enter to return to the main menu...", timeout=10)
    except Exception as e:
        print(f"Error during input: {e}", flush=True)
    
    try:
        subprocess.run(["stty", "sane"], check=False)
    except Exception as e:
        print(f"Error restoring terminal: {e}", flush=True)
    return True
    
def main_menu():
    clear_screen()
    menu = [
        "=" * 40,
        "Argon_One_Test Toolkit v1.0".center(40),
        "=" * 40,
        "1. System Update".ljust(40),
        "2. Run ALL Tests Sequentially".ljust(40),
        "3. Brightness Detection".ljust(40),
        "0. Exit".ljust(40),
        "=" * 40,
        "",
        "Please enter the option number: ",
    ]
    for line in menu:
        print(line, flush=True)
    
    try:
        subprocess.run(["stty", "sane"], check=True, stderr=subprocess.PIPE)
        choice = input().strip()
    except (EOFError, KeyboardInterrupt):
        print("\nInput interrupted, returning to main menu...", flush=True)
        return
    except Exception as e:
        print(f"\nError during input: {e}", flush=True)
        return
    
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
                print(f"  {result}", flush=True)
                
                subprocess.run(["stty", "sane"], check=True, stderr=subprocess.PIPE)
                input("\nTest completed. Press Enter to return to the main menu...")
            else:
                menu_options[choice]()
        except Exception as e:
            print(f"\nError during test: {str(e)}", flush=True)
            print(f"Error details: {traceback.format_exc().splitlines()[-1]}", flush=True)
            
            subprocess.run(["stty", "sane"], check=True, stderr=subprocess.PIPE)
            input("\nPress Enter to return to the main menu...")
    else:
        print("\nInvalid option, please try again!", flush=True)
       
        subprocess.run(["stty", "sane"], check=True, stderr=subprocess.PIPE)
        input("Press Enter to continue...")

if __name__ == "__main__":
    while True:
        main_menu()                                    
