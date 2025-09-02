#!/usr/bin/env python3
"""
Systemd service auto-install script - dynamic user version
Used to automatically create and enable volume.service, adapting to the current user
"""
import os
import sys
import subprocess
import pwd
import getpass

def get_current_user_info():
    """Retrieve current user information"""
    try:
        # Attempt to get the original user if running with sudo
        sudo_user = os.environ.get('SUDO_USER')
        if sudo_user:
            user = sudo_user
        else:
            user = getpass.getuser()
        
        # Get user details
        user_info = pwd.getpwnam(user)
        user_home = user_info.pw_dir
        user_id = user_info.pw_uid
        
        return user, user_home, user_id
    except Exception as e:
        print(f"Failed to retrieve user info: {e}")
        return "pi", "/home/pi", 1000  # Default values

def generate_service_content(user, user_home, user_id):
    """Generate service file content"""
    return f"""[Unit]
Description=Volume Control Python Script
After=multi-user.target
Wants=multi-user.target

[Service]
Type=simple
User={user}
WorkingDirectory={user_home}
ExecStart=/usr/bin/python3 {user_home}/volume.py
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
Environment=PYTHONUNBUFFERED=1
Environment=DISPLAY=:0
Environment=XAUTHORITY={user_home}/.Xauthority
Environment=PULSE_RUNTIME_PATH=/run/user/{user_id}/pulse
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{user_id}/bus

[Install]
WantedBy=multi-user.target
"""

def check_root():
    """Check if running with root privileges"""
    if os.geteuid() != 0:
        print("Error: This script must be run with root privileges. Please use sudo.")
        sys.exit(1)

def create_service_file(service_content):
    """Create systemd service file"""
    service_path = "/etc/systemd/system/volume.service"
    
    try:
        with open(service_path, 'w') as f:
            f.write(service_content)
        print(f"Successfully created service file: {service_path}")
        return True
    except Exception as e:
        print(f"Failed to create service file: {e}")
        return False
def reload_systemd():
    """Reload systemd configuration"""
    try:
        result = subprocess.run(['systemctl', 'daemon-reload'],
                              capture_output=True, text=True, check=True)
        print("Successfully reloaded systemd configuration")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to reload systemd configuration: {e}")
        return False

def enable_service():
    """Enable the service"""
    try:
        result = subprocess.run(['systemctl', 'enable', 'volume.service'],
                              capture_output=True, text=True, check=True)
        print("Successfully enabled volume.service")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to enable service: {e}")
        return False

def start_service():
    """Start the service"""
    try:
        result = subprocess.run(['systemctl', 'start', 'volume.service'],
                              capture_output=True, text=True, check=True)
        print("Successfully started volume.service")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to start service: {e}")
        return False

def check_service_status():
    """Check service status"""
    try:
        result = subprocess.run(['systemctl', 'status', 'volume.service'],
                              capture_output=True, text=True)
        print("Service status:")
        print(result.stdout)
        if result.returncode != 0:
            print(f"Service may have issues, return code: {result.returncode}")
        return result.returncode == 0
    except Exception as e:
        print(f"Failed to check service status: {e}")
        return False

def check_volume_script_exists(user_home):
    """Check if volume.py script exists"""
    volume_script = f"{user_home}/volume.py"
    if not os.path.exists(volume_script):
        print(f"Warning: {volume_script} not found")
        print("Please ensure your volume.py script is located in the user's home directory")
        response = input("Continue with installation? (y/N): ")
        if response.lower() != 'y':
            print("Installation aborted")
            return False
    return True
def main():
    """Main function"""
    print("Starting installation of volume.service...")
    
    # Check privileges
    check_root()
    
    # Get current user information
    user, user_home, user_id = get_current_user_info()
    print(f"Detected user: {user}, home directory: {user_home}, UID: {user_id}")
    
    # Check if volume.py exists
    if not check_volume_script_exists(user_home):
        sys.exit(1)
    
    # Generate service content
    service_content = generate_service_content(user, user_home, user_id)
    print("Generated service configuration:")
    print(service_content)
    
    # Confirm continuation
    response = input("\nContinue with installation? (Y/n): ")
    if response.lower() == 'n':
        print("Installation aborted")
        sys.exit(0)
    
    # Create service file
    if not create_service_file(service_content):
        sys.exit(1)
    
    # Reload systemd
    if not reload_systemd():
        sys.exit(1)
    
    # Enable service
    if not enable_service():
        sys.exit(1)
    
    # Start service
    if not start_service():
        sys.exit(1)
    
    # Check service status
    print("\nInstallation completed, checking service status:")
    check_service_status()
    
    print(f"\nService installed and started for user: {user}")
    print("You can manage the service with the following commands:")
    print(" sudo systemctl status volume.service  # Check status")
    print(" sudo systemctl stop volume.service    # Stop service")
    print(" sudo systemctl restart volume.service # Restart service")
    print(" journalctl -u volume.service -f       # View logs")

if __name__ == "__main__":
    main()
