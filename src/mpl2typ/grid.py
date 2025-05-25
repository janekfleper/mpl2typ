import numpy as np
import numpy.typing as npt

import matplotlib.gridspec

from . import typst
from .axes import Axes


class Cell:
    def __init__(self, x: int, y: int, colspan: int, rowspan: int):
        self.x = x
        self.y = y
        self.colspan = colspan
        self.rowspan = rowspan
        self.axes: list[Axes] = []

    def export(self) -> str:
        axes = [f"axes-{axes.index}()" for axes in self.axes]
        body = typst.function(
            "block",
            named=dict(
                width="100%",
                height="100%",
                stroke="red",
            ),
            body=typst.make_body(axes),
        )

        return typst.function(
            "grid.cell",
            named=dict(
                x=self.x,
                y=self.y,
                colspan=self.colspan,
                rowspan=self.rowspan,
            ),
            body=body,
        )


class Grid:
    def __init__(
        self,
        index: int,
        grid: matplotlib.gridspec.GridSpec,
        axes: list[Axes],
    ):
        self.index = index
        self.grid = grid
        self.axes = axes

        self.cells: list[Cell] = []
        self.padding: dict[str, float] = dict(left=0, right=0, top=0, bottom=0)
        self.parse()

    @property
    def columns(self) -> list[float]:
        return list(np.array(self.grid.get_width_ratios()))

    @property
    def rows(self) -> list[float]:
        return list(np.array(self.grid.get_height_ratios()))

    def _add_axes(self, axes: Axes) -> None:
        for cell in self.cells:
            if cell.x == axes.cell["x"] and cell.y == axes.cell["y"]:
                cell.axes.append(axes)
                return

        cell = Cell(**axes.cell)
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
            np.unique(np.array(x0)),
            np.unique(np.array(x1)),
            np.unique(np.array(y0)),
            np.unique(np.array(y1)),
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

    def export(self):
        cells: list[str] = []
        for cell in self.cells:
            cells.append(cell.export())

        grid = typst.function(
            "grid",
            named={
                "columns": typst.array(typst.fraction(self.columns)),
                "rows": typst.array(typst.fraction(self.rows)),
                "column-gutter": typst.array(typst.ratio(self.column_gutter)),
                "row-gutter": typst.array(typst.ratio(self.row_gutter)),
            },
            body=",\n".join(cells) if cells else None,
        )

        return typst.block(
            f"grid-{self.index}",
            self.padding,
            grid,
        )
