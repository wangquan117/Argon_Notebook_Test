import os
import subprocess
import sys
import traceback
import time
import threading
import select
import signal
import shutil
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, PhotoImage
import webbrowser
from PIL import Image, ImageTk

exit_program_event = threading.Event()
TEST_SCRIPTS_DIR = "argon-scripts/Argon_Notebook_Test-main"

def clear_screen():
    pass  # Not needed in GUI

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
        return False, missing
    return True, []
    

def run_media_recording(stop_event, output_text):
    """Run media recording test with GUI output"""
    output_text.insert(tk.END, "\nStarting media recording (audio and video) for 6 seconds...\n", "info")
    output_text.see(tk.END)
    output_text.update()
    
    try:
        display = os.environ.get('DISPLAY')
        if not display:
            raise Exception("No display available (DISPLAY not set). Set it with: export DISPLAY=:0")
        if not os.path.exists("/dev/video0"):
            raise Exception("/dev/video0 not found. Check camera connection or load v4l2loopback.")
        output_text.insert(tk.END, f"Using display: {display}\n", "info")

        output_file = "recorded_media.mp4"
        if os.path.exists(output_file):
            os.remove(output_file)

        # Record audio and video for 10 seconds
        ffmpeg_process = subprocess.Popen(
            ["ffmpeg", "-y", "-f", "v4l2", "-i", "/dev/video0", "-f", "alsa", "-i", "default", "-t", "6", output_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        ffmpeg_process.wait()

        output_text.insert(tk.END, "\nRecording completed. Starting playback...\n", "info")
        output_text.see(tk.END)
        output_text.update()
        
        # Playback the recorded video
        ffplay_process = subprocess.Popen(
            ["ffplay", "-autoexit", output_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        ffplay_process.wait()
        
        output_text.insert(tk.END, "Media test completed successfully!\n", "success")
        return "run_media_recording____YES"
    except Exception as e:
        if stop_event:
            stop_event.set()
        output_text.insert(tk.END, f"Error in media recording: {str(e)}\n", "error")
        return f"run_media_recording____NO: {str(e)}"
        
def run_system_update(output_text):
    """Run system update with GUI output"""
    output_text.insert(tk.END, "\nUpdating system...\n", "info")
    output_text.see(tk.END)
    output_text.update()

    
    try:
        process = subprocess.Popen(["sudo", "apt", "update"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            output_text.insert(tk.END, line)
            output_text.see(tk.END)
            output_text.update()
        process.wait()
        
        process = subprocess.Popen(["sudo", "apt", "upgrade", "-y"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            output_text.insert(tk.END, line)
            output_text.see(tk.END)
            output_text.update()
        process.wait()
        
        output_text.insert(tk.END, "\nSystem update completed!\n", "success")
        return True
    except subprocess.CalledProcessError as e:
        output_text.insert(tk.END, f"System update failed: {e}\n", "error")
        return False

def run_key_board(output_text):
    """Run keyboard test with GUI output"""
    output_text.insert(tk.END, "\nStarting Keyboard Test...\n", "info")
    output_text.see(tk.END)
    output_text.update()

    
    try:
        display = os.environ.get('DISPLAY')
        if not display:
            raise Exception("DISPLAY environment variable not set. Try running: export DISPLAY=:0")
        output_text.insert(tk.END, f"Using display: {display}\n", "info")
        
        # Install evdev if needed
        try:
            subprocess.run(["sudo", "pip3", "install", "evdev", "--break-system-packages"], 
                          check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
            
        script_path = os.path.join(TEST_SCRIPTS_DIR, "Key_Board_UK.py")
        if not os.path.exists(script_path):
            raise Exception(f"{script_path} not found. Please check the directory.")
        
        result = subprocess.run(
            ["python3", script_path],
            check=False,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            output_text.insert(tk.END, "Keyboard test completed successfully!\n", "success")
            return "run_key_board____YES"
        else:
            output_text.insert(tk.END, f"Keyboard test failed with exit code: {result.returncode}\n", "error")
            output_text.insert(tk.END, f"stdout: {result.stdout}\n")
            output_text.insert(tk.END, f"stderr: {result.stderr}\n")
            return f"run_key_board____NO: Exit code {result.returncode}"
    except Exception as e:
        output_text.insert(tk.END, f"Error running keyboard test: {str(e)}\n", "error")
        return f"run_key_board____NO: {str(e)}"        
        

def run_screen_rgb(output_text):
    """Run Screen RGB Detection with GUI output"""
    output_text.insert(tk.END, "\nStarting Screen RGB Test...\n", "info")
    output_text.see(tk.END)
    output_text.update()
    
    try:
        script_path = os.path.join(TEST_SCRIPTS_DIR, "Screen_Color.py")
        if not os.path.exists(script_path):
            raise Exception(f"{script_path} not found. Please check the directory.")
        
        process = subprocess.Popen(["python3", script_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            output_text.insert(tk.END, line)
            output_text.see(tk.END)
            output_text.update()
        process.wait()
        
        if process.returncode == 0:
            output_text.insert(tk.END, "Screen RGB test completed successfully!\n", "success")
            return "run_screen_rgb____YES"
        else:
            output_text.insert(tk.END, f"Screen RGB test failed with exit code: {process.returncode}\n", "error")
            return f"run_screen_rgb____NO: Exit code {process.returncode}"
    except Exception as e:
        output_text.insert(tk.END, f"Error running screen RGB test: {str(e)}\n", "error")
        return f"run_screen_rgb____NO: {str(e)}"
        
def run_camera(stop_event, output_text):
    """Run camera test with GUI output"""
    output_text.insert(tk.END, "\nStarting Camera Test...\n", "info")
    output_text.see(tk.END)
    output_text.update()
    
    
    try:
        display = os.environ.get('DISPLAY')
        if not display:
            raise Exception("No display available (DISPLAY not set). Set it with: export DISPLAY=:0")
        if not os.path.exists("/dev/video0"):
            raise Exception("/dev/video0 not found. Check camera connection or load v4l2loopback.")
        output_text.insert(tk.END, f"Using display: {display}\n", "info")

        output_text.insert(tk.END, "\nStarting real-time video recording and playback (press 'q' in ffplay to return to main menu)...\n", "info")
        output_text.see(tk.END)
        output_text.update()
        
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
                output_text.insert(tk.END, "ffmpeg process killed due to timeout\n", "warning")
        
        output_text.insert(tk.END, "Camera test completed successfully!\n", "success")
        return "run_camera____YES"
    except Exception as e:
        if stop_event:
            stop_event.set()
        output_text.insert(tk.END, f"Error in camera test: {str(e)}\n", "error")
        return f"run_camera____NO: {str(e)}"
        
def run_recording_playback(stop_event, output_text):
    """Run audio recording and playback test with GUI output"""
    output_text.insert(tk.END, "\nStarting Audio Recording and Playback Test...\n", "info")
    output_text.see(tk.END)
    output_text.update()
    
    
    try:
        # Install alsa-utils if needed
        try:
            subprocess.run(["sudo", "apt", "install", "-y", "alsa-utils"], 
                          check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
            
#        subprocess.run(["amixer", "set", "Master", "75%"], check=False)
#        subprocess.run(["amixer", "set", "Capture", "75%"], check=False)
        
        output_text.insert(tk.END, "Recording audio for 5 seconds...\n", "info")
        output_text.see(tk.END)
        output_text.update()
        
        arecord_process = subprocess.Popen(
            ["arecord", "-f", "S16_LE", "-r", "44100", "-c", "2", "-d", "5", "test_audio.wav"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        arecord_process.wait()
        
        if arecord_process.returncode != 0:
            raise Exception("Audio recording failed")
            
        output_text.insert(tk.END, "Playing back recorded audio...\n", "info")
        output_text.see(tk.END)
        output_text.update()
        
        aplay_process = subprocess.Popen(
            ["aplay", "test_audio.wav"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        aplay_process.wait()
        
        if aplay_process.returncode != 0:
            raise Exception("Audio playback failed")
        
        output_text.insert(tk.END, "Audio recording and playback test completed successfully!\n", "success")
        return "run_recording_playback____YES"
    except Exception as e:
        if stop_event:
            stop_event.set()
        output_text.insert(tk.END, f"Error in audio test: {str(e)}\n", "error")
        return f"run_recording_playback____NO: {str(e)}"  
        
def run_brightness(output_text):
    """Run brightness test with GUI output"""
    output_text.insert(tk.END, "\nStarting Brightness Control Test...\n", "info")
    output_text.see(tk.END)
    output_text.update()
    
    
    try:
        # Install ddcutil if needed
        try:
            subprocess.run(["sudo", "apt", "install", "-y", "ddcutil"], 
                          check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
            
        script_path = os.path.join(TEST_SCRIPTS_DIR, "KEY_Light_init.py")
        if not os.path.exists(script_path):
            raise Exception(f"{script_path} not found. Please check the directory.")
        
        process = subprocess.Popen(["sudo", "python3", script_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            output_text.insert(tk.END, line)
            output_text.see(tk.END)
            output_text.update()
        process.wait()
        
        
        if process.returncode == 0:
            output_text.insert(tk.END, "Brightness control test completed successfully!\n", "success")
            return "run_brightness____YES"
        else:
            output_text.insert(tk.END, f"Brightness control test failed with exit code: {process.returncode}\n", "error")
            return f"run_brightness____NO: Exit code {process.returncode}"
    except Exception as e:
        output_text.insert(tk.END, f"Error running brightness test: {str(e)}\n", "error")
        return f"run_brightness____NO: {str(e)}"              

def run_electricity_power(output_text):
    """Run electricity power test with GUI output"""
    output_text.insert(tk.END, "\nStarting Electricity Power Test...\n", "info")
    output_text.see(tk.END)
    output_text.update()
    
    try:
        script_path = os.path.join(TEST_SCRIPTS_DIR, "CW2217_one.py")
        if not os.path.exists(script_path):
            raise Exception(f"{script_path} not found. Please check the directory.")
        
        process = subprocess.Popen(["python3", script_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            output_text.insert(tk.END, line)
            output_text.see(tk.END)
            output_text.update()
        process.wait()
        
        if process.returncode == 0:
            output_text.insert(tk.END, "Electricity power test completed successfully!\n", "success")
            return "run_electricity_power____YES"
        else:
            output_text.insert(tk.END, f"Electricity power test failed with exit code: {process.returncode}\n", "error")
            return f"run_electricity_power____NO: Exit code {process.returncode}"
    except Exception as e:
        output_text.insert(tk.END, f"Error running electricity power test: {str(e)}\n", "error")
        return f"run_electricity_power____NO: {str(e)}"


def run_flow_light(output_text):
    """Run flow light test with GUI output"""
    output_text.insert(tk.END, "\nStarting Flow Light Test...\n", "info")
    output_text.see(tk.END)
    output_text.update()
    
    try:
        script_path = os.path.join(TEST_SCRIPTS_DIR, "Flow_Light.py")
        if not os.path.exists(script_path):
            raise Exception(f"{script_path} not found. Please check the directory.")
        
        process = subprocess.Popen(["python3", script_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            output_text.insert(tk.END, line)
            output_text.see(tk.END)
            output_text.update()
        process.wait()
        
        if process.returncode == 0:
            output_text.insert(tk.END, "Flow light test completed successfully!\n", "success")
            return "run_flow light____YES"
        else:
            output_text.insert(tk.END, f"Flow light test failed with exit code: {process.returncode}\n", "error")
            return f"run_flow light____NO: Exit code {process.returncode}"
    except Exception as e:
        output_text.insert(tk.END, f"Error running flow light test: {str(e)}\n", "error")
        return f"run_flow light____NO: {str(e)}"

def run_full_load_test(output_text, progress_bar, run_button):
    """Run full load test with stress and temperature monitoring"""
    run_button.config(state=tk.DISABLED)
    output_text.delete(1.0, tk.END)
    

    stop_progress_event = threading.Event()
    
    def update_progress():
  
        total_duration = 1800  
        start_time = time.time()
        
        while not stop_progress_event.is_set():
            elapsed = time.time() - start_time
            progress = min(100, (elapsed / total_duration) * 100)
        
            root.after(0, lambda: progress_bar.config(value=progress))

            time.sleep(1)
    
    try:
   
        progress_thread = threading.Thread(target=update_progress, daemon=True)
        progress_thread.start()
        
        output_text.insert(tk.END, "Installing required dependencies...\n", "info")
        output_text.see(tk.END)
        output_text.update()
        
        try:
            subprocess.run(["sudo", "apt", "install", "-y", "stress"], 
                          check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            output_text.insert(tk.END, f"Error installing stress: {e.stderr.decode()}\n", "error")
            stop_progress_event.set()
            return False
        
        try:
            subprocess.run(["pip3", "install", "stressberry", "--user", "--break-system-packages"], 
                          check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["pip3", "install", "--upgrade", "numpy", "--break-system-packages"], 
                          check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            output_text.insert(tk.END, f"Error installing Python packages: {e.stderr.decode()}\n", "error")
            stop_progress_event.set()
            return False
                   
        
        home_dir = os.path.expanduser("~")
        test_dir = os.path.join(home_dir, "TemperatureTests")
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
        
        output_text.insert(tk.END, "Starting full load test (30 minutes)...\n", "info")
        output_text.see(tk.END)
        output_text.update()
        
        stress_cmd = [
            os.path.join(home_dir, ".local", "bin", "stressberry-run"),
            "-n", "Full Load Test",
            "-d", "1800",  
            "-i", "300",  
            "-c", "4",     
            "mytest.out"
        ]
        
        output_text.insert(tk.END, f"Running command: {' '.join(stress_cmd)}\n", "info")
        output_text.see(tk.END)
        output_text.update()
        
        process = subprocess.Popen(
            stress_cmd,
            cwd=test_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1, 
            universal_newlines=True
        )
        
       
        while True:
            line = process.stdout.readline()
            if not line:
                break
            output_text.insert(tk.END, line)
            output_text.see(tk.END)
            output_text.update()
            
            if exit_program_event.is_set():
                process.terminate()
                output_text.insert(tk.END, "Test interrupted by user\n", "warning")
                stop_progress_event.set()
                return False
        
        process.wait()
        
        if process.returncode != 0:
            output_text.insert(tk.END, f"Full load test failed with exit code: {process.returncode}\n", "error")
            stop_progress_event.set()
            return False
        
    
        output_text.insert(tk.END, "\nGenerating temperature graph...\n", "info")
        output_text.see(tk.END)
        output_text.update()
        
        plot_cmd = [
            "MPLBACKEND=Agg",
            os.path.join(home_dir, ".local", "bin", "stressberry-plot"),
            "mytest.out",
            "-f",
            "-d", "300",
            "-f",
            "-l", "400", "2600",
            "-t", "30", "90",
            "-o", "mytest.png",
            "--not-transparent"
        ]
        
        output_text.insert(tk.END, f"Running command: {' '.join(plot_cmd)}\n", "info")
        output_text.see(tk.END)
        output_text.update()

        
        plot_process = subprocess.Popen(
            " ".join(plot_cmd),
            cwd=test_dir,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
       
        while True:
            line = plot_process.stdout.readline()
            if not line:
                break
            output_text.insert(tk.END, line)
            output_text.see(tk.END)
            output_text.update()
        
        plot_process.wait()
        
        if plot_process.returncode != 0:
            output_text.insert(tk.END, f"Graph generation failed with exit code: {plot_process.returncode}\n", "error")
            stop_progress_event.set()
            return False

        output_path = os.path.join(test_dir, "mytest.png")
        output_text.insert(tk.END, f"\nFull load test completed successfully!\n", "success")
        output_text.insert(tk.END, f"Temperature graph saved to: {output_path}\n", "info")
        
       
        progress_bar.config(value=100)
        
        def open_image():
            if os.path.exists(output_path):
                webbrowser.open(f"file://{output_path}")
            else:
                messagebox.showerror("Error", "Image file not found!")
        
        open_button = ttk.Button(
            output_text.winfo_toplevel(), 
            text="Open Temperature Graph", 
            command=open_image
        )
        open_button.pack(pady=10)
        
        return True
    except Exception as e:
        output_text.insert(tk.END, f"Error in full load test: {str(e)}\n", "error")
        traceback.print_exc()
        return False
    finally:
        stop_progress_event.set() 
        run_button.config(state=tk.NORMAL)         

def create_restart_script():

    user_home = os.path.expanduser("~")
    counter_file = os.path.join(user_home, "restart_count.txt")
    
    script_content = f"""#!/bin/bash

COUNTER_FILE="{counter_file}"
MAX_RESTARTS=$1

CRON_SCRIPT="{os.path.join(user_home, 'restart_test.sh')}"

if [ ! -f "$COUNTER_FILE" ]; then
    echo "0" > "$COUNTER_FILE"
fi

CURRENT_COUNT=$(cat "$COUNTER_FILE")

if [ "$CURRENT_COUNT" -ge "$MAX_RESTARTS" ]; then
    echo "Maximum restarts reached! Cleaning up..." | sudo tee /dev/kmsg
    rm -f "$COUNTER_FILE"

    crontab -l | grep -v "$CRON_SCRIPT" | crontab -
    exit 0
fi

NEXT_COUNT=$((CURRENT_COUNT + 1))
echo "$NEXT_COUNT" > "$COUNTER_FILE"
echo "Reboot #$NEXT_COUNT/$MAX_RESTARTS" | sudo tee /dev/kmsg

if ! crontab -l | grep -q "$CRON_SCRIPT"; then
    (crontab -l 2>/dev/null; echo "@reboot /bin/bash $CRON_SCRIPT $MAX_RESTARTS") | crontab -
fi

sleep 10

echo "Restarting now..." | sudo tee /dev/kmsg
sudo /sbin/reboot
"""
    script_path = os.path.join(user_home, "restart_test.sh")
    with open(script_path, "w") as f:
        f.write(script_content)
    os.chmod(script_path, 0o755)
    return script_path

def start_restart_test(restart_count, output_text):
    try:
        count = int(restart_count)
        script_path = create_restart_script()

        counter_file = os.path.join(os.path.expanduser("~"), "restart_count.txt")
        with open(counter_file, "w") as f:
            f.write("0")

        cron_cmd = f"@reboot /bin/bash {script_path} {count}"
        current_cron = subprocess.check_output(["crontab", "-l"], stderr=subprocess.DEVNULL).decode()
        
        if cron_cmd not in current_cron:
            subprocess.run(
                f'(crontab -l 2>/dev/null; echo "{cron_cmd}") | crontab -',
                shell=True,
                check=True
            )

        output_text.insert(tk.END, "The first restart will begin in 10 seconds.始...\n", "info")
        output_text.see(tk.END)
        output_text.update()
        

        time.sleep(2)
        subprocess.Popen(
            ["sudo", "/sbin/reboot"],
            start_new_session=True
        )
        
        output_text.insert(tk.END, "The reboot sequence has been initiated....\n", "success")
        output_text.see(tk.END)
    except Exception as e:
        output_text.insert(tk.END, f"false: {str(e)}\n", "error")
        traceback.print_exc()

def stop_restart_test(output_text):

    try:
        user = os.getlogin()
        counter_file = os.path.expanduser(f"~{user}/restart_count.txt")
        

        if os.path.exists(counter_file):
            os.remove(counter_file)
        

        subprocess.run("crontab -l | grep -v restart_test.sh | crontab -", 
                      shell=True, check=True)
        

        subprocess.run(["pkill", "-f", "restart_test.sh"], check=False)
        
        output_text.insert(tk.END, "Restart task fully stopped\n", "success")
    except Exception as e:
        output_text.insert(tk.END, f"Stop failed: {str(e)}\n", "error")


def run_all_tests(output_text, progress_bar, run_button):
    """Run all tests sequentially and report results"""
    run_button.config(state=tk.DISABLED)
    output_text.delete(1.0, tk.END) 
    
   
    stop_event = threading.Event()
    
    
    test_cases = [
        ("Keyboard Detection", lambda: run_key_board(output_text)),
        ("Screen RGB Detection", lambda: run_screen_rgb(output_text)),
        ("Electricity Power Detection", lambda: run_electricity_power(output_text)),
        ("Flow Light Test", lambda: run_flow_light(output_text)),
        ("Media Recording Test", lambda: run_media_recording(stop_event, output_text)),
#        ("Camera Test", lambda: run_camera(stop_event, output_text)),
#        ("Audio Test", lambda: run_recording_playback(stop_event, output_text)),
    ]
    
    results = []
    total_tests = len(test_cases)
    
    output_text.insert(tk.END, "\n" + "="*50 + "\n", "info")
    output_text.insert(tk.END, "Starting Automated Testing Sequence\n", "info")
    output_text.insert(tk.END, "="*50 + "\n", "info")
    output_text.see(tk.END)
    
  
    for i, (name, test_func) in enumerate(test_cases):
        if stop_event.is_set() or exit_program_event.is_set():
            output_text.insert(tk.END, "\nTesting interrupted by user\n", "warning")
            break
            
       
        progress = int((i / total_tests) * 100)
        progress_bar['value'] = progress
        progress_bar.update()
        
        output_text.insert(tk.END, f"\n>>> Starting Test {i+1}/{total_tests}: {name}...\n", "info")
        output_text.see(tk.END)
        output_text.update_idletasks()  
        
      
        try:
            result = test_func()
            results.append((name, result))
            
          
            if "____NO" in result:
                output_text.insert(tk.END, f"! Test failed, stopping further tests\n", "error")
                stop_event.set()
        except Exception as e:
            error_msg = f"run_{name.lower().replace(' ', '_')}____NO: {str(e)}"
            results.append((name, error_msg))
            output_text.insert(tk.END, f"! Critical error: {str(e)}\n", "error")
            stop_event.set()
    
    
    progress_bar['value'] = 100
    progress_bar.update()
    

    output_text.insert(tk.END, "\n" + "="*50 + "\n", "info")
    output_text.insert(tk.END, "Test Results Summary:\n", "info")
    output_text.insert(tk.END, "="*50 + "\n", "info")
    
    passed = 0
    failed = 0
    
    for name, result in results:
        if "____YES" in result:
            output_text.insert(tk.END, f"? {name}: PASSED\n", "success")
            passed += 1
        else:
            output_text.insert(tk.END, f"? {name}: FAILED - {result}\n", "error")
            failed += 1
    
    output_text.insert(tk.END, f"\nTotal: {passed} passed, {failed} failed\n", "bold")
    output_text.see(tk.END)
    
    run_button.config(state=tk.NORMAL)
    return True

def cleanup_and_exit(root):
      
    home_dir = os.path.expanduser("~")
    
    files_to_remove = [
        'recorded_media.mp4', 
        'test_audio.wav',
        'ffmpeg.log',
        'ffplay.log',
        os.path.join(home_dir, 'argon_notebook_test_UK.sh'),
        os.path.join(home_dir, 'argon-scripts'),
        os.path.join(home_dir, 'Desktop', 'Argon_Test_Toolkit_One.desktop'),
        os.path.join(home_dir, 'restart_test.sh'),
        os.path.join(home_dir, 'restart_count.txt'),
        os.path.join(home_dir, 'TemperatureTests')
    ]
  
    removed = []
    not_found = []
    failed = []
    
    for item in files_to_remove:
        try:
            if os.path.exists(item):
                if os.path.isfile(item):
                    os.remove(item)
                    removed.append(item)
                elif os.path.isdir(item):
                    shutil.rmtree(item)
                    removed.append(item + " (folder)")
            else:
                not_found.append(item)
        except Exception as e:
            failed.append(f"{item}: {str(e)}")
    

    message = "Clear results :\n"
    if removed:
        message += f"YES_Deleted files: {', '.join(removed)}\n"
    if not_found:
        message += f"File not found.: {', '.join(not_found)}\n"
    if failed:
        message += f"Deletion failed: {', '.join(failed)}\n"
    
    if not removed and not failed:
        message += "no files that need to be cleaned up"
    
    messagebox.showinfo("Cleanup completed", message)
    root.destroy()

    
def create_gui():
    """Create the main GUI for the Argon One Test Toolkit"""
    root = tk.Tk()
    root.title("Argon One Test Toolkit")
    root.geometry("1280x960")
    root.resizable(True, True)
    
    # Set application icon (if available)
    try:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "argon-icon.png")
        if os.path.exists(icon_path):
            root.iconphoto(True, tk.PhotoImage(file=icon_path))
    except:
        pass
    
    # Create style
    style = ttk.Style()
    style.configure("TButton", padding=6, font=('Helvetica', 10))
    style.configure("Big.TButton", font=('Helvetica', 12, 'bold'), padding=10)
    style.configure("Title.TLabel", font=('Helvetica', 16, 'bold'))
    style.configure("Info.TLabel", font=('Helvetica', 10))
    style.configure("Cleanup.TButton", background="#ffcccc", foreground="#990000")
    
    # Main container frame
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Header frame
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill=tk.X, pady=(0, 10))
    
    # Title
    title_label = ttk.Label(header_frame, text="Argon One Test Toolkit", style="Title.TLabel")
    title_label.pack(side=tk.LEFT)
    
    # Version info
    version_label = ttk.Label(header_frame, text="v1.0", style="Info.TLabel")
    version_label.pack(side=tk.RIGHT)
    
    # Create button frame
    button_container = ttk.Frame(main_frame)
    button_container.pack(fill=tk.X, pady=(0, 10))
    
    # Run All Tests button (full width)
    run_all_frame = ttk.Frame(button_container)
    run_all_frame.pack(fill=tk.X, pady=(0, 10))
    
    run_all_button = ttk.Button(
        run_all_frame, 
        text="Run All Tests", 
        style="Big.TButton",
        command=lambda: threading.Thread(
            target=run_all_tests, 
            args=(output_text, progress_bar, run_all_button), 
            daemon=True).start()
    )
    run_all_button.pack(fill=tk.X, expand=True)

 
    # Full Load Test button (full width)
    full_load_frame = ttk.Frame(button_container)
    full_load_frame.pack(fill=tk.X, pady=(0, 10))
    
    full_load_button = ttk.Button(
        full_load_frame, 
        text="Full-load Test", 
        style="Big.TButton",
        command=lambda: threading.Thread(
            target=run_full_load_test, 
            args=(output_text, progress_bar, full_load_button), 
            daemon=True).start()
    )
    full_load_button.pack(fill=tk.X, expand=True) 
    
    # Other test buttons in a grid
    test_buttons_frame = ttk.Frame(button_container)
    test_buttons_frame.pack(fill=tk.X)

# Create restart test frame - above the button container
    restart_frame = ttk.LabelFrame(main_frame, text="Restart Test")
    restart_frame.pack(fill=tk.X, pady=(0, 10))
    
    # Restart test controls
    ttk.Label(restart_frame, text="Restart Count:").pack(side=tk.LEFT, padx=(10, 5))
    
    restart_var = tk.StringVar(value="5")
    restart_spinbox = ttk.Spinbox(
        restart_frame, 
        from_=1, 
        to=100, 
        textvariable=restart_var,
        width=5
    )
    restart_spinbox.pack(side=tk.LEFT, padx=5)
    
    start_button = ttk.Button(
        restart_frame,
        text="Start Restart Task",
        command=lambda: threading.Thread(
            target=start_restart_test, 
            args=(restart_var.get(), output_text),
            daemon=True
        ).start()
    )
    start_button.pack(side=tk.LEFT, padx=5)
    
    stop_button = ttk.Button(
        restart_frame,
        text="Stop Restart Task",
        command=lambda: threading.Thread(
            target=stop_restart_test, 
            args=(output_text,),
            daemon=True
        ).start()
    )
    stop_button.pack(side=tk.LEFT, padx=5)
    
    # Add note for restart test
    ttk.Label(
        restart_frame,
        text="Note: This operation will set the system to automatically reboot multiple times, please save all work!",
        foreground="red"
    ).pack(side=tk.LEFT, padx=10)
    
    # Create button container frame - now below the restart test
    button_container = ttk.Frame(main_frame)
    button_container.pack(fill=tk.X, pady=(0, 10))        
    
    test_buttons = [
        ("Keyboard Test", lambda: threading.Thread(target=run_key_board, args=(output_text,), daemon=True).start()),
        ("Screen RGB Test", lambda: threading.Thread(target=run_screen_rgb, args=(output_text,), daemon=True).start()),
        ("Camera Test", lambda: threading.Thread(target=run_camera, args=(threading.Event(), output_text), daemon=True).start()),
        ("Audio Test", lambda: threading.Thread(target=run_recording_playback, args=(threading.Event(), output_text), daemon=True).start()),
        ("Power Test", lambda: threading.Thread(target=run_electricity_power, args=(output_text,), daemon=True).start()),
        ("Flow Light Test", lambda: threading.Thread(target=run_flow_light, args=(output_text,), daemon=True).start()),
    ]
    
# Create buttons in a 3-column grid
    for i, (text, command) in enumerate(test_buttons):
        row = i // 3
        col = i % 3
        btn = ttk.Button(test_buttons_frame, text=text, command=command)
        btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        test_buttons_frame.columnconfigure(col, weight=1)
    
    # Progress bar
    progress_frame = ttk.Frame(main_frame)
    progress_frame.pack(fill=tk.X, pady=(0, 10))
    
    progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode='determinate')
    progress_bar.pack(fill=tk.X)
    
    # Output text area
    output_frame = ttk.Frame(main_frame)
    output_frame.pack(fill=tk.BOTH, expand=True)
    
    output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, font=('Courier', 10))
    output_text.pack(fill=tk.BOTH, expand=True)
    
    # Configure text tags
    output_text.tag_configure("info", foreground="blue")
    output_text.tag_configure("success", foreground="green")
    output_text.tag_configure("warning", foreground="orange")
    output_text.tag_configure("error", foreground="red")
    output_text.tag_configure("bold", font=('Courier', 10, 'bold'))
    
    # Bottom buttons frame
    bottom_frame = ttk.Frame(main_frame)
    bottom_frame.pack(fill=tk.X, pady=(10, 0))
    
    cleanup_button = ttk.Button(
        bottom_frame, 
        text="Clear Output", 
        command=lambda: cleanup_and_exit(root),
        style="Cleanup.TButton"
    )
    cleanup_button.pack(side=tk.RIGHT, padx=5)
    
    exit_button = ttk.Button(bottom_frame, text="Exit", command=root.destroy)
    exit_button.pack(side=tk.RIGHT)
    
    # Initial message
    output_text.insert(tk.END, "Argon One Test Toolkit v1.0\n", "bold")
    output_text.insert(tk.END, "Ready to run tests. Select a test from the buttons above.\n\n")
    
    output_text.insert(tk.END, "Full-load Test Instructions:\n", "bold")
    output_text.insert(tk.END, "1. This test will install stress and stressberry if not already installed\n")
    output_text.insert(tk.END, "2. It will create a directory ~/TemperatureTests\n")
    output_text.insert(tk.END, "3. Run a 30-minute full load test on 4 cores\n")
    output_text.insert(tk.END, "4. Generate a temperature graph after completion\n")
    output_text.insert(tk.END, "Note: This test will take approximately 30 minutes to complete\n\n")    
    
    # Check dependencies
    deps_ok, missing = check_dependencies()
    if not deps_ok:
        output_text.insert(tk.END, "Warning: Missing dependencies detected!\n", "warning")
        output_text.insert(tk.END, "Some tests may not work properly. Missing:\n", "warning")
        for dep in missing:
            output_text.insert(tk.END, f"  - {dep}\n", "warning")
        output_text.insert(tk.END, "\n")
    
    return root


def main():
    # Check if we're running on Raspberry Pi
    if not os.path.exists('/proc/device-tree/model'):
        print("This application is designed to run on Raspberry Pi.")
        return
    
    # Create and run the GUI
    root = create_gui()
    root.mainloop()

if __name__ == "__main__":
    main()                        
