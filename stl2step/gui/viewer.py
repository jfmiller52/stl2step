# SPDX-FileCopyrightText: 2025 stl2step contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""PyVista / PyQt6 3D viewer for STL and tessellated STEP previews."""

from __future__ import annotations

import os
from typing import Optional

# Prefer PyQt6 bindings for pyvistaqt / vtk.
os.environ.setdefault("QT_API", "pyqt6")

import cadquery as cq
import numpy as np
import pyvista as pv
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget
from pyvistaqt import QtInteractor

MODE_STL = "stl"
MODE_STEP = "step"
MODE_SPLIT = "split"


def _tessellate_step(path: str, tolerance: float = 0.1) -> pv.PolyData:
    """Import a STEP file and return a triangulated PyVista mesh."""
    workplane = cq.importers.importStep(path)
    shape = workplane.val()
    vertices, triangles = shape.tessellate(tolerance)
    if not vertices or not triangles:
        return pv.PolyData()
    points = np.array([[v.x, v.y, v.z] for v in vertices], dtype=float)
    faces = np.hstack([[3, int(a), int(b), int(c)] for a, b, c in triangles])
    return pv.PolyData(points, faces)


class MeshViewer(QWidget):
    """Viewer with STL / STEP / Split modes."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._mode = MODE_STL
        self._stl_path: Optional[str] = None
        self._step_path: Optional[str] = None
        self._stl_mesh: Optional[pv.PolyData] = None
        self._step_mesh: Optional[pv.PolyData] = None

        self._stack = QStackedWidget(self)
        self._single_page = QWidget()
        self._split_page = QWidget()

        single_layout = QVBoxLayout(self._single_page)
        single_layout.setContentsMargins(0, 0, 0, 0)
        self._single_plotter = QtInteractor(self._single_page)
        single_layout.addWidget(self._single_plotter.interactor)

        split_layout = QHBoxLayout(self._split_page)
        split_layout.setContentsMargins(0, 0, 0, 0)

        left_box = QVBoxLayout()
        left_label = QLabel("STL")
        left_label.setStyleSheet("color: #c8cdd5; padding: 2px 4px;")
        self._left_plotter = QtInteractor(self._split_page)
        left_box.addWidget(left_label)
        left_box.addWidget(self._left_plotter.interactor)

        right_box = QVBoxLayout()
        right_label = QLabel("STEP")
        right_label.setStyleSheet("color: #c8cdd5; padding: 2px 4px;")
        self._right_plotter = QtInteractor(self._split_page)
        right_box.addWidget(right_label)
        right_box.addWidget(self._right_plotter.interactor)

        split_layout.addLayout(left_box)
        split_layout.addLayout(right_box)

        self._stack.addWidget(self._single_page)
        self._stack.addWidget(self._split_page)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._stack)

        for plotter in (
            self._single_plotter,
            self._left_plotter,
            self._right_plotter,
        ):
            plotter.set_background("#22262e")
            plotter.add_axes()

        self._apply_mode()

    def set_mode(self, mode: str) -> None:
        if mode not in (MODE_STL, MODE_STEP, MODE_SPLIT):
            raise ValueError(f"Unknown viewer mode: {mode}")
        self._mode = mode
        self._apply_mode()
        self._refresh()

    def mode(self) -> str:
        return self._mode

    def load_stl(self, path: str) -> None:
        self._stl_path = path
        self._stl_mesh = pv.read(path)
        self._refresh()

    def load_step(self, path: str) -> None:
        self._step_path = path
        self._step_mesh = _tessellate_step(path)
        self._refresh()

    def clear_step(self) -> None:
        self._step_path = None
        self._step_mesh = None
        self._refresh()

    def _apply_mode(self) -> None:
        if self._mode == MODE_SPLIT:
            self._stack.setCurrentWidget(self._split_page)
        else:
            self._stack.setCurrentWidget(self._single_page)

    def _show_mesh(
        self,
        plotter: QtInteractor,
        mesh: Optional[pv.PolyData],
        color: str,
        reset_camera: bool = True,
    ) -> None:
        plotter.clear()
        plotter.add_axes()
        if mesh is not None and mesh.n_points > 0:
            plotter.add_mesh(mesh, color=color, show_edges=True, opacity=1.0)
            if reset_camera:
                plotter.reset_camera()
        plotter.render()

    def _refresh(self) -> None:
        if self._mode == MODE_STL:
            self._show_mesh(self._single_plotter, self._stl_mesh, "#6fa8dc")
        elif self._mode == MODE_STEP:
            self._show_mesh(self._single_plotter, self._step_mesh, "#82c785")
        else:
            self._show_mesh(self._left_plotter, self._stl_mesh, "#6fa8dc")
            self._show_mesh(self._right_plotter, self._step_mesh, "#82c785")
            try:
                self._left_plotter.link_views_across_plots([self._right_plotter])
            except Exception:
                # Older pyvista may not support linking across interactors.
                pass
