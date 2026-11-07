<!--
SPDX-FileCopyrightText: 2025 Stefan Helmert <stefan@entroserv.de>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Intelligent conversion from STL to STEP

This cli program converts STL files into STEP file in a non-trivial way. It segments the mesh into basic shapes. That means, the generated STEP file isn't only a bunch of triangles, it has planes, cylinders, spheres etc. resulting in less memory usage and it is friendlier to CAD and CAM. 

Experimental state: Only planes are implemented! Holes __are__ supported now!

![screenshot of the output step file imported into FreeCAD and the conversion log](example_step.png)


## Installation

```bash
pip3 install stl2step
```

## Usage

```bash
python3 -m stl2step myfile.stl
```

The out file is named similar to the input file: `myfile.step`, because it only replaces `.stl` with `.step`.

## GUI

A PyQt6 desktop UI is included for interactive conversion with a 3D preview (PyVista).

Requires **Python 3.10–3.12** (CadQuery / OCP wheels; 3.11 recommended on Apple Silicon).

From a Poetry checkout:

```bash
poetry env use python3.11
poetry install
poetry run python -m stl2step.gui
# or
poetry run stl2step-gui
```

Alternatively with a venv:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m stl2step.gui
```

- Open an STL, preview it, convert to STEP, then inspect the tessellated result (STL / STEP / Split views).
- **File → Convert folder…** batch-converts every `.stl` in a folder into a chosen output directory.
- CadQuery / OCCT remains required for conversion and STEP preview.

### Single binary

Build a one-file GUI executable with PyInstaller (large; bundles CadQuery / VTK / Qt):

```bash
pip install pyinstaller   # or: poetry install --with dev
pyinstaller stl2step-gui.spec --noconfirm --clean
# result: dist/stl2step-gui
```

On macOS the first launch may be slow while the archive unpacks. Unsigned builds may need Gatekeeper approval (`xattr -dr com.apple.quarantine dist/stl2step-gui`).

## Autor

Stefan Helmert <stefan@entroserv.de>

## License

AGPL v3



