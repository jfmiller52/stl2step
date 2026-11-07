# SPDX-FileCopyrightText: 2025 stl2step contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Launch the stl2step GUI: python -m stl2step.gui"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_API", "pyqt6")


def main(argv: list[str] | None = None) -> int:
    # argv reserved for future CLI flags; Qt consumes its own args from sys.argv.
    _ = argv
    from PyQt6.QtWidgets import QApplication

    from stl2step.gui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("stl2step")
    app.setOrganizationName("stl2step")

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
