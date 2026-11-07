# SPDX-FileCopyrightText: 2025 stl2step contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""PyInstaller entry point for the stl2step GUI."""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_API", "pyqt6")


if __name__ == "__main__":
    from stl2step.gui.__main__ import main

    raise SystemExit(main())
