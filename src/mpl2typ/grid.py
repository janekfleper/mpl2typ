import numpy as np
import numpy.typing as npt

import matplotlib.gridspec

from pypst import Fraction, Grid, Ratio

from .axes import Axes
from .typst import Function, PlaceBlock


class AxesCell:
    def __init__(self, position: tuple[int, int], shape: tuple[int, int]):
        self.position = position
        self.shape = shape
        self.axes: list[Axes] = []

    def export(self) -> str:
        axes = [f"{axes.name}()" for axes in self.axes]
        return Function(
            name="axes.cell",
            kwargs=dict(position=self.position, shape=self.shape),
            body=axes,
        ).render()


class AxesGrid:
    def __init__(
        self,
        grid: matplotlib.gridspec.GridSpec,
        axes: list[Axes],
        name: str,
        prefix: str = "grid",
    ):
        self._name = name
        self.grid = grid
        self.axes = axes
        self._prefix = prefix

        self.cells: list[AxesCell] = []
        self.padding: dict[str, float] = dict(left=0, right=0, top=0, bottom=0)
        self.parse()

    @property
    def name(self) -> str:
        return self._prefix + "-" + self._name

    @property
    def columns(self) -> list[float]:
        return list(np.array(self.grid.get_width_ratios()))

    @property
    def rows(self) -> list[float]:
        return list(np.array(self.grid.get_height_ratios()))

    def _add_axes(self, axes: Axes) -> None:
        for cell in self.cells:
            if cell.position == axes.cell["position"]:
                cell.axes.append(axes)
                return

        cell = AxesCell(**axes.cell)
        cell.axes.append(axes)
        self.cells.append(cell)

    def _parse_axes(
        self,
    ) -> tuple[
        npt.NDArray[np.float64],
        npt.NDArray[np.float64],
        npt.NDArray[np.float64],
        npt.NDArray[np.float64],
    ]:
        x0: list[float] = []
        x1: list[float] = []
        y0: list[float] = []
        y1: list[float] = []

        for axes in self.axes:
            position = axes.position
            x0.append(position.x0)
            x1.append(position.x1)
            y0.append(position.y0)
            y1.append(position.y1)
            self._add_axes(axes)

        return (
            np.unique(np.round(np.array(x0), 5)),
            np.unique(np.round(np.array(x1), 5)),
            np.unique(np.round(np.array(y0), 5)),
            np.unique(np.round(np.array(y1), 5)),
        )

    def parse(self):
        x0, x1, y0, y1 = self._parse_axes()
        xmin = x0.min()
        xmax = x1.max()
        ymin = y0.min()
        ymax = y1.max()

        self.padding = dict(
            left=xmin,
            right=1 - xmax,
            top=1 - ymax,
            bottom=ymin,
        )

        self.column_gutter = list((x0[1:] - x1[:-1]) / (xmax - xmin))
        self.row_gutter = list((y0[1:] - y1[:-1]) / (ymax - ymin))[::-1]

    def render(self) -> str:
        grid = Grid(
            columns=Fraction(self.columns),
            rows=Fraction(self.rows),
            column_gutter=Ratio(self.column_gutter),
            row_gutter=Ratio(self.row_gutter),
            children=self.cells,
        )

        return PlaceBlock(
            name=self.name,
            padding=self.padding,
            body=grid,
        ).render()
