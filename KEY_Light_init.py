import os
import shutil
import subprocess
import sys
import getpass
import pwd

def get_original_user():
    """Get the original user (even if run through sudo)"""
    # Try to get the original user from environment variable
    original_user = os.environ.get('SUDO_USER')
    
    # If SUDO_USER does not exist, try to get from other environment variables
    if not original_user:
        original_user = os.environ.get('USER')
    
    # If still not found, use getpass
    if not original_user:
        original_user = getpass.getuser()
    
    # Ensure it is not root
    if original_user == "root":
        # Try to get the logged-in user
        login_user = os.getlogin()
        if login_user != "root":
            return login_user
        else:
            # Fallback to the first non-root user
            for user in pwd.getpwall():
                if user.pw_uid >= 1000 and user.pw_name != "root":
                    return user.pw_name
    
    return original_user

def create_systemd_service():
    try:
        # Get original user information
        current_user = get_original_user()
        
        try:
            user_info = pwd.getpwnam(current_user)
        except KeyError:
            print(f"Error: User '{current_user}' does not exist!")
            sys.exit(1)
            
        home_dir = user_info.pw_dir
        
        # Default script path
        script_path = os.path.join(home_dir, "Desktop", "Argon_Notebook_Test-main", "KEY_Light.py")
        
        # User confirmation for script path
        print(f"Detected user: {current_user}")
        print(f"Home directory: {home_dir}")
        print(f"Default script path: {script_path}")
        custom_path = input("Enter script path (press Enter to use the default path): ").strip()
        
        if custom_path:
            if os.path.exists(custom_path):
                script_path = custom_path
            else:
                print(f"Warning: Path {custom_path} does not exist, will use default path")
        
        print(f"Using script path: {script_path}")
        
        # Ensure the script exists
        if not os.path.exists(script_path):
            print(f"Error: Script not found at {script_path}")
            sys.exit(1)
        
        # Set executable permissions
        os.chmod(script_path, 0o755)
        print("Permissions set successfully")

        # Create systemd service file content
        service_content = f"""[Unit]
Description=KEY Light Control Script

[Service]
ExecStart=/usr/bin/python3 {script_path}
Restart=always
RestartSec=5
User={current_user}
WorkingDirectory={os.path.dirname(script_path)}
Environment="DISPLAY=:0" "XAUTHORITY={home_dir}/.Xauthority"

[Install]
WantedBy=multi-user.target
"""

        # Write the service file
        service_file = "/etc/systemd/system/KEY_Light.service"
        print(f"Creating service file: {service_file}")
        with open(service_file, "w") as f:
            f.write(service_content)
        print("Service file created successfully")

        # Reload systemd configuration
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        print("systemd configuration reloaded")

        # Enable the service
        subprocess.run(["systemctl", "enable", "KEY_Light.service"], check=True)
        print("Service set to start on boot")

        # Start the service
        subprocess.run(["systemctl", "start", "KEY_Light.service"], check=True)
        print("Service started")

        # Check service status
        print("\nService status:")
        subprocess.run(["systemctl", "status", "KEY_Light.service", "--no-pager"])
        
        # Ask about reboot
        restart = input("\nWould you like to reboot the system immediately to apply the changes? (y/n): ").strip().lower()
        if restart == 'y':
            print("The system will reboot...")
            subprocess.run(["reboot"])

    except subprocess.CalledProcessError as e:
        print(f"\nError: Command execution failed: {e.cmd}")
        print(f"Return code: {e.returncode}")
        print(f"Error output: {e.stderr.decode().strip() if e.stderr else 'None'}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: An error occurred during setup: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if running with root privileges
    if os.geteuid() != 0:
        print("Please run this script with sudo!")
        sys.exit(1)
    
    print("="*50)
    print("Keyboard Light Service Installation Tool")
    print("="*50)
    create_systemd_service()
