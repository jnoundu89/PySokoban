"""
Script to build a Python package for PySokoban.
This script will create distribution files that can be installed using pip.
"""

import os
import subprocess
import sys
import shutil

def main():
    # Ensure setuptools and wheel are installed
    try:
        import setuptools
        import wheel
        print("setuptools and wheel are already installed.")
    except ImportError:
        print("Installing setuptools and wheel...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "setuptools", "wheel"])
        print("setuptools and wheel installed successfully.")

    # Clean up previous builds
    if os.path.exists("build"):
        print("Removing previous build directory...")
        shutil.rmtree("build")
    if os.path.exists("dist"):
        print("Removing previous dist directory...")
        shutil.rmtree("dist")
    if os.path.exists("pysokoban.egg-info"):
        print("Removing previous egg-info directory...")
        shutil.rmtree("pysokoban.egg-info")

    # Build the package
    print("Building the Python package...")
    subprocess.check_call([sys.executable, "setup.py", "sdist", "bdist_wheel"])

    # Check if twine is installed for uploading to PyPI
    try:
        import twine
        print("\nNote: If you want to upload the package to PyPI, you can use:")
        print("twine upload dist/*")
    except ImportError:
        print("\nNote: If you want to upload the package to PyPI, install twine first:")
        print("pip install twine")
        print("Then you can use: twine upload dist/*")

    print("\nPackage built successfully!")
    print("You can find the distribution files in the 'dist' folder:")
    for file in os.listdir("dist"):
        print(f"- {file}")
    
    print("\nTo install the package locally, run:")
    wheel_file = next((f for f in os.listdir("dist") if f.endswith(".whl")), None)
    if wheel_file:
        print(f"pip install dist/{wheel_file}")
    else:
        print("pip install -e .")
    
    print("\nAfter installation, you can run the game using these commands:")
    print("- pysokoban (basic version)")
    print("- pysokoban-gui (GUI version)")
    print("- pysokoban-enhanced (enhanced version)")
    print("- pysokoban-editor (level editor)")

if __name__ == "__main__":
    main()