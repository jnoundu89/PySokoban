# Creating a Python Package for PySokoban

This document explains how to create a Python package for PySokoban that can be installed using pip and distributed to others.

## Prerequisites

- Python 3.6 or higher installed
- pip (Python package installer)
- setuptools and wheel packages installed
- PySokoban source code

## Method 1: Using the build_package.py Script (Recommended)

We've provided a script that automates the process of creating a Python package.

### Steps:

1. Open a command prompt in the PySokoban directory
2. Run the build script:
   ```
   python build_package.py
   ```
3. Wait for the process to complete
4. Once finished, you'll find the package files in the `dist` folder

## Method 2: Manual Package Building

If you prefer to build the package manually or need to customize the build process:

### Steps:

1. Install required build tools if you haven't already:
   ```
   pip install --upgrade setuptools wheel
   ```

2. Open a command prompt in the PySokoban directory

3. Build the package:
   ```
   python setup.py sdist bdist_wheel
   ```

4. The package files will be created in the `dist` folder:
   - A source distribution (.tar.gz file)
   - A wheel distribution (.whl file)

## Installing the Package

### Local Installation

To install the package locally from the built files:

```
pip install dist/pysokoban-1.0.0-py3-none-any.whl
```

Or directly from the source code:

```
pip install -e .
```

### Installing from PyPI (if published)

If the package has been published to the Python Package Index (PyPI):

```
pip install pysokoban
```

## Using the Installed Package

After installation, you can run PySokoban using the following commands:

- Basic version: `pysokoban`
- GUI version: `pysokoban-gui`
- Enhanced version: `pysokoban-enhanced`
- Level editor: `pysokoban-editor`

You can also import the package in your Python code:

```python
from pysokoban import main
main()
```

## Publishing the Package to PyPI

If you want to share your package with the wider Python community:

1. Create an account on PyPI (https://pypi.org)

2. Install twine:
   ```
   pip install twine
   ```

3. Upload your package:
   ```
   twine upload dist/*
   ```

4. Enter your PyPI username and password when prompted

## Troubleshooting

If you encounter any issues:

1. **Missing dependencies**: Make sure all required packages are installed:
   ```
   pip install -r requirements.txt
   ```

2. **Import errors after installation**: Ensure your package structure is correct and that `__init__.py` files are present in all necessary directories

3. **Package not found after installation**: Check that the package was installed correctly using `pip list | grep pysokoban`

## Notes

- The package includes all necessary game files (levels, skins, assets, etc.)
- Users who install your package will be able to run the game without downloading the source code
- Consider updating the version number in setup.py when making changes to the package