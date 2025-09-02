#!/usr/bin/env python3
"""
Systemd user service auto-install script
Used to automatically create and enable volume.service in the user's home directory
"""
import os
import sys
import subprocess
import pwd
import getpass
import stat

def get_current_user_info():
    """Retrieve current user information"""
    try:
        # Use SUDO_USER if available, otherwise fall back to getuser()
        user = os.environ.get('SUDO_USER', getpass.getuser())
        user_info = pwd.getpwnam(user)
        user_home = user_info.pw_dir
        user_id = user_info.pw_uid
        return user, user_home, user_id
    except Exception as e:
        print(f"Failed to retrieve user info: {e}")
        return None, None, None

def generate_service_content(user_home):
    """Generate user service file content"""
    return f"""[Unit]
Description=Volume Control Python Script
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 {user_home}/volume.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
"""

def create_user_service_directory(user_home, user_id):
    """Create user service directory if it doesn't exist"""
    service_dir = os.path.join(user_home, ".config", "systemd", "user")
    try:
        os.makedirs(service_dir, exist_ok=True)
        os.chown(service_dir, user_id, user_id)
        os.chmod(service_dir, stat.S_IRWXU)
        print(f"Created/verified user service directory: {service_dir}")
        return True
    except Exception as e:
        print(f"Failed to create user service directory: {e}")
        return False

def create_service_file(user_home, user_id, service_content):
    """Create systemd user service file"""
    service_path = os.path.join(user_home, ".config", "systemd", "user", "volume.service")
    try:
        with open(service_path, 'w') as f:
            f.write(service_content)
        os.chown(service_path, user_id, user_id)
        os.chmod(service_path, stat.S_IRUSR | stat.S_IWUSR)
        print(f"Successfully created user service file: {service_path}")
        return True
    except Exception as e:
        print(f"Failed to create user service file: {e}")
        return False

def run_systemctl_user_command(user, command, check=True):
    """Run systemctl --user command as the specified user"""
    try:
        # Set XDG_RUNTIME_DIR for user session
        xdg_runtime_dir = f"/run/user/{pwd.getpwnam(user).pw_uid}"
        env = os.environ.copy()
        env['XDG_RUNTIME_DIR'] = xdg_runtime_dir
        cmd = ['sudo', '-u', user, 'XDG_RUNTIME_DIR=' + xdg_runtime_dir, 'systemctl', '--user'] + command
        result = subprocess.run(cmd, capture_output=True, text=True, check=check, env=env)
        print(f"Successfully executed: {' '.join(command)}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute {' '.join(command)}: {e.stderr}")
        return None
    except Exception as e:
        print(f"Unexpected error executing {' '.join(command)}: {e}")
        return None
def check_volume_script_exists(user_home):
    """Check if volume.py script exists"""
    volume_script = os.path.join(user_home, "volume.py")
    if not os.path.exists(volume_script):
        print(f"Warning: {volume_script} not found")
        print("Please ensure your volume.py script is located in the user's home directory")
        response = input("Continue with installation? (y/N): ")
        if response.lower() != 'y':
            print("Installation aborted")
            return False
    return True

def check_user_systemd_session(user):
    """Check if user has an active systemd session"""
    try:
        result = run_systemctl_user_command(user, ['is-system-running'], check=False)
        if result and result.returncode == 0:
            return True
        print(f"Warning: No active systemd user session for {user}. Ensure the user is logged in or has lingering enabled.")
        return False
    except Exception as e:
        print(f"Failed to check systemd user session: {e}")
        return False

def main():
    """Main function"""
    print("Starting installation of user volume.service...")

    # Get current user information
    user, user_home, user_id = get_current_user_info()
    if not user:
        print("Error: Could not determine user information")
        sys.exit(1)
    print(f"Detected user: {user}, home directory: {user_home}, UID: {user_id}")

    # Check if volume.py exists
    if not check_volume_script_exists(user_home):
        sys.exit(1)

    # Generate service content
    service_content = generate_service_content(user_home)
    print("Generated user service configuration:")
    print(service_content)

    # Confirm continuation
    response = input("\nContinue with installation? (Y/n): ")
    if response.lower() == 'n':
        print("Installation aborted")
        sys.exit(0)

    # Create user service directory
    if not create_user_service_directory(user_home, user_id):
        sys.exit(1)

    # Create service file
    if not create_service_file(user_home, user_id, service_content):
        sys.exit(1)

    # Check if user has an active systemd session
    if not check_user_systemd_session(user):
        print("Hint: Enable lingering for persistent user services with:")
        print(f" sudo loginctl enable-linger {user}")
        response = input("Continue despite no active user session? (y/N): ")
        if response.lower() != 'y':
            print("Installation aborted")
            sys.exit(1)

    # Reload systemd
    if not run_systemctl_user_command(user, ['daemon-reload']):
        sys.exit(1)

    # Enable service
    if not run_systemctl_user_command(user, ['enable', 'volume.service']):
        sys.exit(1)

    # Start service
    if not run_systemctl_user_command(user, ['start', 'volume.service']):
        sys.exit(1)

    if not run_systemctl_user_command(user, ['restart', 'volume.service']):
        sys.exit(1)

    # Check service status
    print("\nInstallation completed, checking user service status:")
    run_systemctl_user_command(user, ['status', 'volume.service'], check=False)

    print(f"\nUser service installed and started for user: {user}")
    print("You can manage the user service with the following commands:")
    print(f" systemctl --user status volume.service # Check status")
    print(f" systemctl --user stop volume.service # Stop service")
    print(f" systemctl --user restart volume.service # Restart service")
    print(f" journalctl --user -u volume.service -f # View logs")
    print(f"\nIf the service fails to start, ensure lingering is enabled:")
    print(f" sudo loginctl enable-linger {user}")

if __name__ == "__main__":
    main()        
