# Developer quickstart

The current GUI is a Python/Tkinter prototype. The C++17/CMake core will become the long-term implementation.

## Requirements

- Python 3 with Tkinter for the prototype GUI
- CMake 3.16+ and a C++17 compiler for the native CLI core

## Run the GUI

Windows: run `START_WINDOWS.bat`

macOS: `sh START_MAC.command`

Or on either system: `python3 editor/app.py`

## Tests

```sh
python3 -m unittest discover -s tests -v
```

## Native CLI build

```sh
cmake -S . -B build
cmake --build build
```

No Yamaha installers, binaries, or third-party music files should be committed.
