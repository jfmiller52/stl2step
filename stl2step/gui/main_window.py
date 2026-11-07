# SPDX-FileCopyrightText: 2025 stl2step contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Main application window — Layout A (preview dominant)."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from stl2step.convert import default_output_path
from stl2step.gui.viewer import MODE_SPLIT, MODE_STEP, MODE_STL, MeshViewer
from stl2step.gui.worker import BatchConvertWorker, ConvertWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("stl2step")
        self.resize(1200, 720)

        self._worker: Optional[ConvertWorker] = None
        self._batch_worker: Optional[BatchConvertWorker] = None

        self._viewer = MeshViewer(self)

        self._input_edit = QLineEdit()
        self._input_edit.setPlaceholderText("Select an STL file…")
        self._output_edit = QLineEdit()
        self._output_edit.setPlaceholderText("Output STEP path…")

        browse_in = QToolButton()
        browse_in.setText("…")
        browse_in.clicked.connect(self.open_stl)
        browse_out = QToolButton()
        browse_out.setText("…")
        browse_out.clicked.connect(self.choose_output)

        in_row = QHBoxLayout()
        in_row.addWidget(self._input_edit)
        in_row.addWidget(browse_in)
        out_row = QHBoxLayout()
        out_row.addWidget(self._output_edit)
        out_row.addWidget(browse_out)

        form = QFormLayout()
        form.addRow("Input STL", in_row)
        form.addRow("Output STEP", out_row)

        self._convert_btn = QPushButton("Convert")
        self._convert_btn.clicked.connect(self.start_convert)
        self._convert_btn.setEnabled(False)

        mode_row = QHBoxLayout()
        self._btn_stl = QPushButton("STL")
        self._btn_step = QPushButton("STEP")
        self._btn_split = QPushButton("Split")
        for btn, mode in (
            (self._btn_stl, MODE_STL),
            (self._btn_step, MODE_STEP),
            (self._btn_split, MODE_SPLIT),
        ):
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, m=mode: self._set_view_mode(m))
            mode_row.addWidget(btn)
        self._btn_stl.setChecked(True)

        self._progress = QProgressBar()
        self._progress.setRange(0, 5)
        self._progress.setValue(0)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setPlaceholderText("Conversion log…")
        self._log.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        right = QVBoxLayout()
        right.addLayout(form)
        right.addLayout(mode_row)
        right.addWidget(self._convert_btn)
        right.addWidget(QLabel("Progress"))
        right.addWidget(self._progress)
        right.addWidget(QLabel("Log"))
        right.addWidget(self._log, stretch=1)

        right_panel = QWidget()
        right_panel.setLayout(right)
        right_panel.setMinimumWidth(320)
        right_panel.setMaximumWidth(420)

        body = QHBoxLayout()
        body.addWidget(self._viewer, stretch=2)
        body.addWidget(right_panel, stretch=1)

        central = QWidget()
        central.setLayout(body)
        self.setCentralWidget(central)

        self._build_menus()
        self._input_edit.textChanged.connect(self._on_input_changed)
        self.statusBar().showMessage("Open an STL file to begin.")

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        open_act = QAction("Open STL…", self)
        open_act.setShortcut(QKeySequence.StandardKey.Open)
        open_act.triggered.connect(self.open_stl)
        file_menu.addAction(open_act)

        save_as_act = QAction("Save STEP As…", self)
        save_as_act.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_act.triggered.connect(self.choose_output)
        file_menu.addAction(save_as_act)

        file_menu.addSeparator()

        batch_act = QAction("Convert folder…", self)
        batch_act.triggered.connect(self.convert_folder)
        file_menu.addAction(batch_act)

        file_menu.addSeparator()

        quit_act = QAction("Quit", self)
        quit_act.setShortcut(QKeySequence.StandardKey.Quit)
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        view_menu = self.menuBar().addMenu("&View")
        for label, mode in (
            ("Show STL", MODE_STL),
            ("Show STEP", MODE_STEP),
            ("Split view", MODE_SPLIT),
        ):
            act = QAction(label, self)
            act.triggered.connect(lambda checked=False, m=mode: self._set_view_mode(m))
            view_menu.addAction(act)

    def _append_log(self, message: str) -> None:
        self._log.appendPlainText(message)

    def _on_input_changed(self, text: str) -> None:
        path = text.strip()
        ready = bool(path) and Path(path).is_file()
        self._convert_btn.setEnabled(ready and not self._busy())
        if ready and not self._output_edit.text().strip():
            self._output_edit.setText(default_output_path(path))

    def _busy(self) -> bool:
        return (
            self._worker is not None and self._worker.isRunning()
        ) or (self._batch_worker is not None and self._batch_worker.isRunning())

    def _set_busy(self, busy: bool) -> None:
        self._convert_btn.setEnabled(
            (not busy)
            and bool(self._input_edit.text().strip())
            and Path(self._input_edit.text().strip()).is_file()
        )
        self.menuBar().setEnabled(not busy)

    def _set_view_mode(self, mode: str) -> None:
        self._btn_stl.setChecked(mode == MODE_STL)
        self._btn_step.setChecked(mode == MODE_STEP)
        self._btn_split.setChecked(mode == MODE_SPLIT)
        self._viewer.set_mode(mode)

    def open_stl(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open STL",
            "",
            "STL files (*.stl *.STL);;All files (*)",
        )
        if not path:
            return
        self._input_edit.setText(path)
        self._output_edit.setText(default_output_path(path))
        self._viewer.clear_step()
        try:
            self._viewer.load_stl(path)
            self._set_view_mode(MODE_STL)
            self.statusBar().showMessage(f"Loaded {path}")
            self._append_log(f"Opened STL: {path}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Failed to load STL", str(exc))

    def choose_output(self) -> None:
        start = self._output_edit.text().strip() or str(Path.home())
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save STEP As",
            start,
            "STEP files (*.step *.stp);;All files (*)",
        )
        if path:
            if not path.lower().endswith((".step", ".stp")):
                path += ".step"
            self._output_edit.setText(path)

    def start_convert(self) -> None:
        if self._busy():
            return
        input_path = self._input_edit.text().strip()
        output_path = self._output_edit.text().strip() or default_output_path(input_path)
        if not input_path or not Path(input_path).is_file():
            QMessageBox.warning(self, "Missing input", "Choose a valid STL file first.")
            return
        self._output_edit.setText(output_path)
        self._progress.setRange(0, 5)
        self._progress.setValue(0)
        self._append_log(f"Starting conversion → {output_path}")
        self._set_busy(True)

        self._worker = ConvertWorker(input_path, output_path, self)
        self._worker.log.connect(self._append_log)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_convert_finished)
        self._worker.failed.connect(self._on_convert_failed)
        self._worker.finished.connect(lambda: self._set_busy(False))
        self._worker.start()

    def _on_progress(self, current: int, total: int) -> None:
        self._progress.setMaximum(max(total, 1))
        self._progress.setValue(current)

    def _on_convert_finished(self, output_path: str) -> None:
        self._progress.setValue(self._progress.maximum())
        self.statusBar().showMessage(f"Wrote {output_path}")
        self._append_log(f"Finished: {output_path}")
        try:
            self._viewer.load_step(output_path)
            self._set_view_mode(MODE_STEP)
        except Exception as exc:  # noqa: BLE001
            self._append_log(f"STEP preview failed: {exc}")

    def _on_convert_failed(self, message: str) -> None:
        self.statusBar().showMessage("Conversion failed")
        self._append_log(f"ERROR: {message}")
        QMessageBox.critical(self, "Conversion failed", message)

    def convert_folder(self) -> None:
        if self._busy():
            return
        input_dir = QFileDialog.getExistingDirectory(self, "Select folder with STL files")
        if not input_dir:
            return
        output_dir = QFileDialog.getExistingDirectory(
            self, "Select output folder for STEP files"
        )
        if not output_dir:
            return

        stl_files = sorted(
            list(Path(input_dir).glob("*.stl")) + list(Path(input_dir).glob("*.STL"))
        )
        # Deduplicate case-insensitive duplicates on case-sensitive FS
        seen = set()
        unique: List[Path] = []
        for path in stl_files:
            key = str(path.resolve()).lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(path)

        if not unique:
            QMessageBox.information(
                self, "No STL files", f"No .stl files found in:\n{input_dir}"
            )
            return

        jobs: List[Tuple[str, str]] = []
        for stl in unique:
            out = Path(output_dir) / f"{stl.stem}.step"
            jobs.append((str(stl), str(out)))

        self._append_log(
            f"Batch: {len(jobs)} file(s) from {input_dir} → {output_dir}"
        )
        self._progress.setRange(0, len(jobs))
        self._progress.setValue(0)
        self._set_busy(True)

        self._batch_worker = BatchConvertWorker(jobs, self)
        self._batch_worker.log.connect(self._append_log)
        self._batch_worker.progress.connect(self._on_progress)
        self._batch_worker.file_finished.connect(self._on_batch_file_finished)
        self._batch_worker.finished_ok.connect(self._on_batch_finished)
        self._batch_worker.failed.connect(self._on_convert_failed)
        self._batch_worker.finished.connect(lambda: self._set_busy(False))
        self._batch_worker.start()

    def _on_batch_file_finished(self, input_path: str, output_path: str) -> None:
        # Load the latest successful pair into the viewer for inspection.
        try:
            self._input_edit.setText(input_path)
            self._output_edit.setText(output_path)
            self._viewer.load_stl(input_path)
            self._viewer.load_step(output_path)
            self._set_view_mode(MODE_SPLIT)
        except Exception as exc:  # noqa: BLE001
            self._append_log(f"Preview update failed: {exc}")

    def _on_batch_finished(self, ok: int, fail: int) -> None:
        self._progress.setValue(self._progress.maximum())
        msg = f"Batch complete: {ok} succeeded, {fail} failed"
        self.statusBar().showMessage(msg)
        self._append_log(msg)
        if fail:
            QMessageBox.warning(self, "Batch finished with errors", msg)
        else:
            QMessageBox.information(self, "Batch finished", msg)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._busy():
            reply = QMessageBox.question(
                self,
                "Conversion in progress",
                "A conversion is still running. Quit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            for worker in (self._worker, self._batch_worker):
                if worker is not None and worker.isRunning():
                    worker.requestInterruption()
                    worker.wait(1000)
        event.accept()
