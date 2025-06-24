from setuptools import setup, find_packages

setup(
    name="pysokoban",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pygame",
        "pillow",
        "numpy",
        "matplotlib",
        "scikit-learn",
        "tensorflow",
        "keyboard",
    ],
    entry_points={
        "console_scripts": [
            "pysokoban=src.main:main",
            "pysokoban-gui=src.gui_main:main",
            "pysokoban-enhanced=src.enhanced_main:main",
            "pysokoban-editor=src.editor_main:main",
        ],
    },
    python_requires=">=3.6",
    author="Yassine EL IDRISSI",
    author_email="your.email@example.com",  # Replace with actual email if available
    description="A Python implementation of the classic Sokoban puzzle game",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pysokoban",  # Replace with actual URL if available
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Adjust license as needed
        "Operating System :: OS Independent",
        "Topic :: Games/Entertainment :: Puzzle Games",
    ],
    keywords="sokoban, game, puzzle",
    package_data={
        "": ["levels/*/*.txt", "skins/*/*.png", "assets/*", "config.json"],
    },
)
