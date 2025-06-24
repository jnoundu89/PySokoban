"""
Script to build a standalone executable for PySokoban using PyInstaller.
This script will create an .exe file that can be run on Windows without requiring Python.
"""

import os
import subprocess
import sys
import shutil

def main():
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller installed successfully.")

    # Check if the executable exists and try to terminate any running instances
    import os
    import time

    exe_path = os.path.join('dist', 'PySokoban.exe')
    if os.path.exists(exe_path):
        print(f"Found existing executable at {exe_path}")
        try:
            # Try to terminate any running instances of the executable
            print("Attempting to terminate any running instances...")
            subprocess.call(['taskkill', '/F', '/IM', 'PySokoban.exe'], 
                           stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            # Wait a moment to ensure the process is fully terminated
            time.sleep(1)
        except Exception as e:
            print(f"Warning: Could not terminate running instances: {e}")

        # Try to remove the file if it still exists
        try:
            if os.path.exists(exe_path):
                os.remove(exe_path)
                print("Removed existing executable.")
                # Wait a moment to ensure the file is fully released
                time.sleep(1)
        except Exception as e:
            print(f"Warning: Could not remove existing executable: {e}")
            print("You may need to close any running instances of PySokoban.exe manually.")

    # Create the spec file for PyInstaller
    print("Creating executable...")

    # Define the command to run PyInstaller
    pyinstaller_cmd = [
        "pyinstaller",
        "--name=PySokoban",
        "--onefile",  # Create a single executable file
        "--windowed",  # Don't show the console window when running the app
        "--icon=assets\\icon.ico" if os.path.exists("assets\\icon.ico") else "",
        "--add-data=levels;levels",  # Include the levels directory
        "--add-data=skins;skins",    # Include the skins directory
        "--add-data=assets;assets" if os.path.exists("assets") else "",
        "--add-data=config.json;.",  # Include the config file
        "src\\main.py"  # The main script to execute
    ]

    # Remove empty arguments
    pyinstaller_cmd = [arg for arg in pyinstaller_cmd if arg]

    # Run PyInstaller
    subprocess.check_call(pyinstaller_cmd)

    print("\nExecutable created successfully!")
    print("You can find the executable in the 'dist' folder.")
    print("\nTo run the game, simply double-click on 'PySokoban.exe' in the dist folder.")

if __name__ == "__main__":
    main()
