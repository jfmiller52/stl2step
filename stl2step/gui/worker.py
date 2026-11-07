# SPDX-FileCopyrightText: 2025 stl2step contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Background conversion workers for the GUI."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from PyQt6.QtCore import QThread, pyqtSignal

from stl2step.convert import convert_stl_to_step, default_output_path


class ConvertWorker(QThread):
    """Convert a single STL file on a background thread."""

    log = pyqtSignal(str)
    progress = pyqtSignal(int, int)
    finished_ok = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path or default_output_path(input_path)

    def run(self) -> None:
        try:
            stats = convert_stl_to_step(
                self.input_path,
                self.output_path,
                on_log=lambda msg: self.log.emit(msg),
                on_progress=lambda cur, total: self.progress.emit(cur, total),
            )
            self.finished_ok.emit(stats.output_path)
        except Exception as exc:  # noqa: BLE001 — surface any conversion failure
            self.failed.emit(str(exc))


class BatchConvertWorker(QThread):
    """Convert a list of STL files sequentially."""

    log = pyqtSignal(str)
    progress = pyqtSignal(int, int)
    file_finished = pyqtSignal(str, str)  # input, output
    finished_ok = pyqtSignal(int, int)  # ok_count, fail_count
    failed = pyqtSignal(str)

    def __init__(
        self,
        jobs: List[Tuple[str, str]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.jobs = jobs

    def run(self) -> None:
        ok = 0
        fail = 0
        total = len(self.jobs)
        try:
            for index, (input_path, output_path) in enumerate(self.jobs, start=1):
                name = Path(input_path).name
                self.log.emit(f"[{index}/{total}] Converting {name}")
                self.progress.emit(index - 1, total)
                try:
                    stats = convert_stl_to_step(
                        input_path,
                        output_path,
                        on_log=lambda msg: self.log.emit(msg),
                        on_progress=None,
                    )
                    ok += 1
                    self.file_finished.emit(input_path, stats.output_path)
                    self.log.emit(f"[{index}/{total}] Wrote {stats.output_path}")
                except Exception as exc:  # noqa: BLE001
                    fail += 1
                    self.log.emit(f"[{index}/{total}] FAILED {name}: {exc}")
            self.progress.emit(total, total)
            self.finished_ok.emit(ok, fail)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
