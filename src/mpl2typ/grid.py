import matplotlib as mpl

from .util import make_body, function, compute_gutter, block
from .axes import Axes


class Cell:
    def __init__(self, x: int, y: int, colspan: int, rowspan: int):
        self.x = x
        self.y = y
        self.colspan = colspan
        self.rowspan = rowspan
        self.axes: list[Axes] = []

    def export(self):
        axes = [f"axes-{axes.index}()" for axes in self.axes]
        body = function(
            "block",
            dict(
                width="100%",
                height="100%",
                stroke="red",
            ),
        )(make_body(axes))

        return function(
            "grid.cell",
            dict(x=self.x, y=self.y, colspan=self.colspan, rowspan=self.rowspan),
        )(body)


class Grid:
    def __init__(
        self,
        index: int,
        grid: mpl.gridspec.GridSpec,
        axes: list[Axes],
    ):
        self.index = index
        self.grid = grid
        self.axes = axes

        self.column_gutter = compute_gutter(self.wspace, self.grid.ncols)
        self.row_gutter = compute_gutter(self.hspace, self.grid.nrows)

        self.cells: list[Cell] = []
        self.padding: dict[str, float] = dict(left=0, right=0, top=0, bottom=0)
        self.parse()

    @property
    def columns(self):
        return self.grid.get_width_ratios()

    @property
    def rows(self):
        return self.grid.get_height_ratios()

    @property
    def wspace(self):
        return self.grid.get_subplot_params().wspace

    @property
    def hspace(self):
        return self.grid.get_subplot_params().hspace

    def _add_axes(self, axes: Axes):
        for cell in self.cells:
            if cell.x == axes.cell["x"] and cell.y == axes.cell["y"]:
                cell.axes.append(axes)
                return

        cell = Cell(**axes.cell)
        cell.axes.append(axes)
        self.cells.append(cell)

    def parse(self):
        # find the outer bounding box of all axes
        x0, x1, y0, y1 = [], [], [], []

        for axes in self.axes:
            position = axes.position
            x0.append(position.x0)
            x1.append(position.x1)
            y0.append(position.y0)
            y1.append(position.y1)
            self._add_axes(axes)

        self.padding = dict(
            left=min(x0),
            right=1 - max(x1),
            top=1 - max(y1),
            bottom=min(y0),
        )

    def export(self):
        columns = ", ".join([f"{col}fr" for col in self.columns])
        rows = ", ".join([f"{row}fr" for row in self.rows])
        column_gutter = f"{round(self.column_gutter * 100, 3)}%"
        row_gutter = f"{round(self.row_gutter * 100, 3)}%"

        grid = function(
            "grid",
            {
                "columns": f"({columns})",
                "rows": f"({rows})",
                "column-gutter": column_gutter,
                "row-gutter": row_gutter,
            },
        )

        body = []
        for cell in self.cells:
            body.append(cell.export())

        return block(
            f"grid-{self.index}",
            self.padding,
        )(grid(",\n".join(body)))
