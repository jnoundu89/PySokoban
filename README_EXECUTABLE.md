# Creating an Executable for PySokoban

This document explains how to create a standalone executable (.exe) file for PySokoban that can be run on Windows without requiring Python to be installed.

## Prerequisites

- Windows operating system
- Python 3.6 or higher installed
- PySokoban source code

## Method 1: Using the build_exe.py Script (Recommended)

We've provided a script that automates the process of creating an executable using PyInstaller.

### Steps:

1. Open a command prompt in the PySokoban directory
2. Run the build script:
   ```
   python build_exe.py
   ```
3. Wait for the process to complete (this may take several minutes)
4. Once finished, you'll find the executable in the `dist` folder
5. To run the game, simply double-click on `PySokoban.exe` in the dist folder

## Method 2: Manual PyInstaller Setup

If you prefer to run PyInstaller manually or need to customize the build process:

### Steps:

1. Install PyInstaller if you haven't already:
   ```
   pip install pyinstaller
   ```

2. Open a command prompt in the PySokoban directory

3. Run PyInstaller with the following command:
   ```
   pyinstaller --name=PySokoban --onefile --windowed --add-data=levels;levels --add-data=skins;skins --add-data=config.json;. src\main.py
   ```

4. The executable will be created in the `dist` folder

## Running the Executable

- Double-click on `PySokoban.exe` in the dist folder to start the game
- The executable contains all necessary files and dependencies, so it can be shared with others who don't have Python installed
- Note that the first launch might take a bit longer as the executable unpacks its resources

## Troubleshooting

If you encounter any issues:

1. **Missing dependencies**: Make sure all required packages are installed:
   ```
   pip install -r requirements.txt
   ```

2. **File not found errors**: Ensure all paths in the build command are correct for your system

3. **Antivirus blocking**: Some antivirus software may flag PyInstaller-created executables. You may need to add an exception.

4. **Black screen or immediate close**: Try running the executable from the command line to see error messages:
   ```
   dist\PySokoban.exe
   ```

## Distribution

To share your executable with others:

1. You can distribute just the `PySokoban.exe` file from the dist folder
2. Alternatively, create a zip file containing the executable and any additional files you want to include
3. The recipient only needs to extract the files and run the executable - no Python installation required

## Notes

- The executable may be quite large (100+ MB) due to including Python and all dependencies
- The `--onefile` option creates a single executable that's easier to distribute but takes longer to start
- If you prefer a faster startup time, you can remove the `--onefile` option, but this will create a folder with many files instead of a single executable