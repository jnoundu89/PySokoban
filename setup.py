from setuptools import setup, find_packages

setup(
    name="pysokoban",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pygame",
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
    description="A Python implementation of the classic Sokoban puzzle game",
    keywords="sokoban, game, puzzle",
    package_data={
        "": ["levels/*/*.txt", "skins/*/*.png"],
    },
)