# -*- coding: utf-8 -*-
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
import tempfile

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
    
    try:
        subprocess.run(["which", "guvcview"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        try:
            subprocess.run(["sudo", "apt", "install", "-y", "guvcview"],
                         check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            missing.append("guvcview (install with: sudo apt install -y guvcview)")
    
    if missing:
        return False, missing
    return True, []

def run_media_recording(stop_event, output_text):
   """Run media recording test with GUI output"""
   try:
        # Create a non-blocking Toplevel window for the prompt
        prompt_window = tk.Toplevel()
        prompt_window.title("录音测试")
        # Set geometry and position
        prompt_window.geometry("500x300+100+100")
        prompt_window.transient(root)  # Set as transient to main window
        prompt_window.grab_set()  # Make the prompt modal
        prompt_window.update_idletasks()
        prompt_window.geometry("+100+100")  # Explicitly set position
        
        # Add prompt message
        tk.Label(prompt_window, 
                text="目前正在录音10秒，录音结束会自动播放录音内容，要求：正常录音及播放，播放内容除去环境声外，无额外杂音，噪音等",
                font=('Helvetica', 14),
                wraplength=450,  # Wrap text within 450 pixels
                justify="center"  # Center the text
        ).pack(pady=30, padx=20)
        
        prompt_window.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable closing via window manager
        prompt_window.lift()  # Ensure the prompt window is on top
        output_text.update_idletasks()

        output_text.insert(tk.END, "\nStarting media recording (audio and video) for 6 seconds...\n", "info")
        output_text.see(tk.END)
        output_text.update()
        
        output_file = "recorded_audio.wav"  
        if os.path.exists(output_file):
            os.remove(output_file)

        # Run ffmpeg recording process
        ffmpeg_process = subprocess.Popen(
            ["ffmpeg", "-y", "-f", "alsa", "-i", "default", "-t", "6", output_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        # Function to monitor the process and handle stop event
        def monitor_process():
            try:
                while True:
                    if stop_event.is_set():
                        ffmpeg_process.terminate()
                        try:
                            ffmpeg_process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            ffmpeg_process.kill()
                        output_text.insert(tk.END, "Audio recording interrupted by user.\n", "warning")
                        return "run_audio_recording____INTERRUPTED"
                  
                    if ffmpeg_process.poll() is not None:
                        # Recording completed, now play back
                        output_text.insert(tk.END, "\nRecording completed. Starting playback...\n", "info")
                        output_text.see(tk.END)
                        output_text.update()

                        ffplay_process = subprocess.Popen(
                            ["ffplay", "-autoexit", output_file],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            close_fds=True
                        )
                        
                        # Wait for playback to complete
                        ffplay_process.wait()
                        
                        if ffplay_process.returncode == 0:
                            output_text.insert(tk.END, "Audio test completed successfully!\n", "success")
                            return "run_audio_recording____YES"
                        else:
                            output_text.insert(tk.END, f"Playback failed with exit code: {ffplay_process.returncode}\n", "error")
                            return f"run_audio_recording____NO: Playback exit code {ffplay_process.returncode}"
                    
                    time.sleep(0.1)  # Avoid busy-waiting
                    
            except Exception as e:
                output_text.insert(tk.END, f"Error in audio recording: {str(e)}\n", "error")
                return f"run_audio_recording____NO: {str(e)}"
            finally:
                # Close the prompt window when the process finishes
                root.after(0, prompt_window.destroy)
                output_text.see(tk.END)
                output_text.update()
        
        # Run the monitor in a separate thread to avoid blocking the GUI
        monitor_thread = threading.Thread(target=lambda: setattr(monitor_thread, 'result', monitor_process()), daemon=True)
        monitor_thread.start()
        monitor_thread.join()  # Wait for the thread to finish
        return monitor_thread.result
        
   except Exception as e:
        if stop_event:
            stop_event.set()
        output_text.insert(tk.END, f"Error in audio recording: {str(e)}\n", "error")
        # Ensure the prompt window is closed if an exception occurs before process starts
        if 'prompt_window' in locals():
            root.after(0, prompt_window.destroy)
        return f"run_audio_recording____NO: {str(e)}"

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
        
        script_path = os.path.join(TEST_SCRIPTS_DIR, "Key_Board_US.py")
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
#    messagebox.showinfo("Screen RGB Test", "全屏须无色差、无光斑等异常，没问题按ESC键退出")
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
    """Run camera test using guvcview with GUI output and non-blocking prompt"""
    try:
        if not os.path.exists("/dev/video0"):
            subprocess.run(["sudo", "modprobe", "bcm2835-v4l2"], check=False)
            time.sleep(2)
            if not os.path.exists("/dev/video0"):
                raise Exception("/dev/video0 not found. Check camera connection and enable in raspi-config")
      
        output_text.insert(tk.END, "\nStarting Camera Test with guvcview...\n", "info")
        output_text.see(tk.END)
        output_text.update()
        
        # Create a non-blocking Toplevel window for the prompt
        prompt_window = tk.Toplevel()
        prompt_window.title("Camera Test")
        # Set geometry to 400x400 pixels and position at top-left (0,0)
        prompt_window.geometry("400x400+50+50")
        prompt_window.transient(root)  # Set as transient to main window
        prompt_window.grab_set()  # Make the prompt modal
        # Ensure the window is placed at the top-left corner
        prompt_window.update_idletasks()  # Update geometry before forcing position
        prompt_window.geometry("+50+50")  # Explicitly set to top-left corner
        tk.Label(prompt_window, text="1、点中间按键，录像10秒（工人计时）。2、点中间按键录制完成。3、点右边按键退出。4、播放视频，除环境声外，无额外杂音、噪音等", font=('Helvetica', 18),
            wraplength=350,  # Wrap text within 350 pixels
            justify="center"  # Center the text
        ).pack(pady=20, padx=10)
        prompt_window.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable closing via window manager
        # Ensure the prompt window is on top
        prompt_window.lift()
        output_text.update_idletasks()

        # Run the camera test with guvcview
        cheese_process = subprocess.Popen(
            ["guvcview"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output_text.insert(tk.END, "Camera test running. Close guvcview to complete test...\n", "info")
        output_text.see(tk.END)
        output_text.update()

        # Function to monitor the process and handle stop event
        def monitor_process():
            try:
                while True:
                    if stop_event.is_set():
                        cheese_process.terminate()
                        try:
                            cheese_process.wait(timeout=2)  # Give it time to terminate
                        except subprocess.TimeoutExpired:
                            cheese_process.kill()  # Force kill if it doesn't terminate
                        output_text.insert(tk.END, "Camera test interrupted by user.\n", "warning")
                        return "run_camera____INTERRUPTED"
                  
                    if cheese_process.poll() is not None:
                        stdout, stderr = cheese_process.communicate()
                        if cheese_process.returncode == 0:
                            output_text.insert(tk.END, "Camera test completed successfully!\n", "success")
                            return "run_camera____YES"
                        else:
                            output_text.insert(tk.END, f"Camera test failed with exit code: {cheese_process.returncode}\n", "error")
                            output_text.insert(tk.END, f"stdout: {stdout}\n")
                            output_text.insert(tk.END, f"stderr: {stderr}\n")
                            return f"run_camera____NO: Exit code {cheese_process.returncode}"
                    time.sleep(0.1)  # Avoid busy-waiting
            except Exception as e:
                output_text.insert(tk.END, f"Error in camera test: {str(e)}\n", "error")
                return f"run_camera____NO: {str(e)}"
            finally:
                # Close the prompt window when the script finishes or fails
                root.after(0, prompt_window.destroy)
                output_text.see(tk.END)
                output_text.update()
        
        # Run the monitor in a separate thread to avoid blocking the GUI
        monitor_thread = threading.Thread(target=lambda: setattr(monitor_thread, 'result', monitor_process()), daemon=True)
        monitor_thread.start()
        monitor_thread.join()  # Wait for the thread to finish
        return monitor_thread.result
    except Exception as e:
        output_text.insert(tk.END, f"Error in camera test: {str(e)}\n", "error")
        # Ensure the prompt window is closed if an exception occurs before process starts
        if 'prompt_window' in locals():
            root.after(0, prompt_window.destroy)
        return f"run_camera____NO: {str(e)}"

    except Exception as e:
        output_text.insert(tk.END, f"Error in camera test: {str(e)}\n", "error")
        # Ensure the prompt window is closed if an exception occurs before process starts
        if 'prompt_window' in locals():
            root.after(0, prompt_window.destroy)
        return f"run_camera____NO: {str(e)}"
                
def run_electricity_power(output_text):
    """Run electricity power test with GUI output"""
    messagebox.showinfo("Electricity Power Test", "读取电量要跟桌面电量显示相同")
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
    """Run flow light test with GUI output and non-blocking prompt"""
    output_text.insert(tk.END, "\nStarting Flow Light Test...\n", "info")
    output_text.see(tk.END)
    output_text.update()
  
    try:
        script_path = os.path.join(TEST_SCRIPTS_DIR, "Flow_Light.py")
        if not os.path.exists(script_path):
            raise Exception(f"{script_path} not found. Please check the directory.")
  
        # Create a non-blocking Toplevel window for the prompt
        prompt_window = tk.Toplevel()
        prompt_window.title("Flow Light Test")
        prompt_window.geometry("400x200")
        prompt_window.transient(root)  # Set as transient to main window
        prompt_window.grab_set()  # Make the prompt modal
        tk.Label(prompt_window, text="红灯常亮，绿灯流线型亮灭", font=('Helvetica', 14)).pack(pady=20)
        prompt_window.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable closing via window manager
        # Ensure the prompt window is on top
        prompt_window.lift()
        output_text.update_idletasks()
  
        # Run the flow light test script
        process = subprocess.Popen(
            ["python3", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
  
        # Function to monitor the process and close the prompt when done
        def monitor_process():
            try:
                stdout, stderr = process.communicate()  # Wait for the process to complete
                if process.returncode == 0:
                    output_text.insert(tk.END, "Flow light test completed successfully!\n", "success")
                    result = "run_flow_light____YES"
                else:
                    output_text.insert(tk.END, f"Flow light test failed with exit code: {process.returncode}\n", "error")
                    output_text.insert(tk.END, f"stdout: {stdout}\n")
                    output_text.insert(tk.END, f"stderr: {stderr}\n")
                    result = f"run_flow_light____NO: Exit code {process.returncode}"
            except Exception as e:
                output_text.insert(tk.END, f"Error running flow light test: {str(e)}\n", "error")
                result = f"run_flow_light____NO: {str(e)}"
            finally:
                # Close the prompt window when the script finishes or fails
                root.after(0, prompt_window.destroy)
                output_text.see(tk.END)
                output_text.update()
            return result
  
        # Run the monitor in a separate thread to avoid blocking the GUI
        monitor_thread = threading.Thread(target=lambda: setattr(monitor_thread, 'result', monitor_process()), daemon=True)
        monitor_thread.start()
        monitor_thread.join()  # Wait for the thread to finish
        return monitor_thread.result
  
    except Exception as e:
        output_text.insert(tk.END, f"Error running flow light test: {str(e)}\n", "error")
        # Ensure the prompt window is closed if an exception occurs before process starts
        if 'prompt_window' in locals():
            root.after(0, prompt_window.destroy)
        return f"run_flow_light____NO: {str(e)}"

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
NOTIFY_SCRIPT="{os.path.join(user_home, 'show_notification.sh')}"
if [ ! -f "$COUNTER_FILE" ]; then
    echo "1" > "$COUNTER_FILE"
fi
CURRENT_COUNT=$(cat "$COUNTER_FILE")
if [ "$CURRENT_COUNT" -ge "$MAX_RESTARTS" ]; then
    echo "Maximum restarts reached! Cleaning up..." | sudo tee /dev/kmsg
    rm -f "$COUNTER_FILE"
    crontab -l | grep -v "$CRON_SCRIPT" | crontab -
    
    # Create persistent notification script
    echo '#!/bin/bash' > "$NOTIFY_SCRIPT"
    echo 'export DISPLAY=:0' >> "$NOTIFY_SCRIPT"
    echo '# Show desktop notification (will auto-close after 10 seconds)' >> "$NOTIFY_SCRIPT"
    echo 'notify-send "Restart Test Completed" "Successfully completed $MAX_RESTARTS reboots!" -i dialog-information -t 10000' >> "$NOTIFY_SCRIPT"
    echo '# Show persistent dialog that stays until manually closed' >> "$NOTIFY_SCRIPT"
    echo 'zenity --info --text="Restart test completed after $MAX_RESTARTS reboots.\n\nClick OK to close this notification." --title="Test Completed" --width=400 --height=200' >> "$NOTIFY_SCRIPT"
    echo '# Clean up only the autostart entry (keep notification script)' >> "$NOTIFY_SCRIPT"
    echo 'rm -f ~/.config/autostart/restart_notifier.desktop' >> "$NOTIFY_SCRIPT"
    chmod +x "$NOTIFY_SCRIPT"
    
    # Add to autostart
    mkdir -p ~/.config/autostart
    echo "[Desktop Entry]
Type=Application
Exec=$NOTIFY_SCRIPT
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name[en_US]=Restart Test Notifier
Name=Restart Test Notifier
Comment[en_US]=Notify restart test completion
Comment=Notify restart test completion" > ~/.config/autostart/restart_notifier.desktop
    
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
        if count < 1:
            raise ValueError("Restart count must be at least 1")
        services_to_disable = [
            "avahi-daemon.service",
            "wayvnc.service",
            "NetworkManager-wait-online.service",
            "alsa-restore.service",
            "rpi-eeprom-update.service",
            "packagekit.service"
        ]
        
        output_text.insert(tk.END, "Disabling system services...\n", "info")
        output_text.see(tk.END)
        output_text.update()
        
        for service in services_to_disable:
            try:
                result = subprocess.run(
                    ["sudo", "systemctl", "disable", service],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    output_text.insert(tk.END, f"Disabled {service}\n", "success")
                else:
                    if "not found" in result.stderr.lower():
                        output_text.insert(tk.END, f"Service {service} not found (may be normal)\n", "warning")
                    else:
                        output_text.insert(tk.END, f"Failed to disable {service}: {result.stderr}\n", "warning")
            except subprocess.TimeoutExpired:
                output_text.insert(tk.END, f"Timeout disabling {service}\n", "warning")
            except Exception as e:
                output_text.insert(tk.END, f"Error disabling {service}: {str(e)}\n", "warning")
        
        output_text.insert(tk.END, "Service disabling completed\n", "info")
        output_text.see(tk.END)
        output_text.update()
        script_path = create_restart_script()
        counter_file = os.path.join(os.path.expanduser("~"), "restart_count.txt")
        with open(counter_file, "w") as f:
            f.write("0")
        cron_cmd = f"@reboot /bin/bash {script_path} {count}"
        try:
            current_cron = subprocess.check_output(["crontab", "-l"], stderr=subprocess.DEVNULL).decode()
        except subprocess.CalledProcessError:
            current_cron = ""
        
        if cron_cmd not in current_cron:
            with tempfile.NamedTemporaryFile(mode="w+") as tmp:
                if current_cron.strip():
                    tmp.write(current_cron + "\n")
                tmp.write(cron_cmd + "\n")
                tmp.flush()
                subprocess.run(["crontab", tmp.name], check=True)
        output_text.insert(tk.END, "The first restart will begin in 10 seconds...\n", "info")
        output_text.see(tk.END)
        output_text.update()
        time.sleep(10)
        subprocess.Popen(["sudo", "/sbin/reboot"], start_new_session=True)
        
        output_text.insert(tk.END, "The reboot sequence has been initiated....\n", "success")
    except Exception as e:
        output_text.insert(tk.END, f"false: {str(e)}\n", "error")
        traceback.print_exc()

def stop_restart_test(output_text):
    try:
        home_dir = os.path.expanduser("~")
        counter_file = os.path.join(home_dir, "restart_count.txt")
        if os.path.exists(counter_file):
            os.remove(counter_file)
        try:
            current_cron = subprocess.check_output(["crontab", "-l"], stderr=subprocess.DEVNULL).decode()
        except subprocess.CalledProcessError:
            current_cron = ""
        new_cron = "\n".join([line for line in current_cron.splitlines()
                             if "restart_test.sh" not in line])
        with tempfile.NamedTemporaryFile(mode="w+") as tmp:
            tmp.write(new_cron)
            tmp.flush()
            subprocess.run(["crontab", tmp.name], check=True)
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
#        ("Electricity Power Detection", lambda: run_electricity_power(output_text)),
        ("Flow Light Test", lambda: run_flow_light(output_text)),
#        ("Media Recording Test", lambda: run_media_recording(stop_event, output_text)),
        ("Camera Test", lambda: run_camera(stop_event, output_text)),
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
            if name == "Camera Test":
                output_text.insert(tk.END, "Waiting for Camera Test to complete...\n", "info")
                output_text.update_idletasks()
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
        os.path.join(home_dir, 'argon_notebook_test_US.sh'),
        os.path.join(home_dir, 'argon-scripts'),
        os.path.join(home_dir, 'Desktop', 'Argon_Test_Toolkit_One.desktop'),
        os.path.join(home_dir, 'restart_test.sh'),
        os.path.join(home_dir, 'restart_count.txt'),
        os.path.join(home_dir, 'show_notification.sh'),
        os.path.join(home_dir, 'Videos/Webcam'),
        os.path.join(home_dir, 'Desktop', 'music_e.mp3'),
        os.path.join(home_dir, 'Desktop', 'my_video-1.mkv'),
        os.path.join(home_dir, 'Desktop', 'my_video-2.mkv'),
        os.path.join(home_dir, 'Desktop', 'my_video-3.mkv'),
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
    global root
    root = tk.Tk()
    root.title("Argon One Test Toolkit")
    root.geometry("1600x960")
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
    
    paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    left_frame = ttk.Frame(paned_window)
    paned_window.add(left_frame, weight=3)
    right_frame = ttk.Frame(paned_window)
    paned_window.add(right_frame, weight=1)
    
    main_frame = ttk.Frame(left_frame)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Header frame
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill=tk.X, pady=(0, 10))
    
    # Title
    title_label = ttk.Label(header_frame, text="Argon One Test Toolkit", style="Title.TLabel")
    title_label.pack(side=tk.LEFT)
    
    # Version info
    version_label = ttk.Label(header_frame, text="v1.0", style="Info.TLabel")
    version_label.pack(side=tk.RIGHT)
    
    # Create restart test frame
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
    
    # Create button container frame
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
            daemon=True
        ).start()
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
            daemon=True
        ).start()
    )
    full_load_button.pack(fill=tk.X, expand=True)
    
    # Other test buttons in a grid
    test_buttons_frame = ttk.Frame(button_container)
    test_buttons_frame.pack(fill=tk.X)
    
    test_buttons = [
        ("Keyboard Test", lambda: threading.Thread(target=run_key_board, args=(output_text,), daemon=True).start()),
        ("Screen RGB Test", lambda: threading.Thread(target=run_screen_rgb, args=(output_text,), daemon=True).start()),
        ("Camera Test", lambda: threading.Thread(target=run_camera, args=(threading.Event(), output_text), daemon=True).start()),
        ("Media Recording Test", lambda: threading.Thread(target=run_media_recording, args=(threading.Event(), output_text), daemon=True).start()),
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
            output_text.insert(tk.END, f" - {dep}\n", "warning")
        output_text.insert(tk.END, "\n")
    
    chinese_instructions = """
一、笔记本全测标准
1) 键盘测试：软件笔记本运行模拟键盘需全部按亮。
2) 屏幕色差：软件笔记本运行RGB颜色须覆盖全屏幕无色差、无光斑等异常。
3) 自定义双USB+扩展板：软件笔记本运行测试"GPIO测试板"流水灯，红灯一直亮、绿灯流线型亮灯。
4) 摄像头+录音+麦克风：软件笔记本运行录制视频功能，须要正常录音、录像、播放，10S且除环境音外，无额外杂音、噪音等。
5) 屏幕亮度：按键触发屏幕亮度，屏幕亮度有明显亮暗，且屏幕右上角有提示修改。
6) 老化测试：软件笔记本运行老化测试结束后，显示的图表中温度不能超过60℃，且在指定区间内无法动态一直保持在2400MHz。
7) 音量调节：按键触发笔记本的音量，有明显变色且右上角图标有跟随变化。
8) 笔记本两端的接口：要能正常识别、打开使用。
9） 键盘底光：按‘FN+空格’可以控制键盘底光亮灭。
10) 删除测试笔记本和数据（三塔科技做的）：软件笔记本一键删除测试文件，保留显示电量图标，无额外多余测试文件。
其他测试：笔记本厂家通用测试。
"""
    
    instruction_label = ttk.Label(right_frame, text="Test Standard Description", font=('Helvetica', 14, 'bold'))
    instruction_label.pack(pady=(0, 10))
    
    instruction_text = scrolledtext.ScrolledText(
        right_frame,
        wrap=tk.WORD,
        font=('WenQuanYi Zen Hei', 12),
        width=40,
        height=50
    )
    instruction_text.pack(fill=tk.BOTH, expand=True)
    instruction_text.insert(tk.END, chinese_instructions)
    instruction_text.config(state=tk.DISABLED)
    
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
    
    
