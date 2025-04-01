import matplotlib as mpl

from .util import function, compute_gutter


class Grid:
    def __init__(self, grid: mpl.gridspec.GridSpec, axes: list[mpl.axes.Axes]):
        self.grid = grid
        self.axes = axes

        self.column_gutter = compute_gutter(self.wspace, self.grid.ncols)
        self.row_gutter = compute_gutter(self.hspace, self.grid.nrows)

        self.cells: list[dict] = []
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

    def parse(self):
        for ax in self.axes:
            sps = ax.get_subplotspec()
            x = sps.colspan.start
            y = sps.rowspan.start
            colspan = sps.colspan.stop - x
            rowspan = sps.rowspan.stop - y
            self.cells.append(dict(x=x, y=y, colspan=colspan, rowspan=rowspan))

    def export(self):
        columns = ", ".join([f"{col}fr" for col in self.columns])
        rows = ", ".join([f"{row}fr" for row in self.rows])
        column_gutter = f"{self.column_gutter * 100:.3g}%"
        row_gutter = f"{self.row_gutter * 100:.3g}%"

        grid = function(
            "grid",
            {
                "columns": f"({columns})",
                "rows": f"({rows})",
                "column-gutter": column_gutter,
                "row-gutter": row_gutter,
            },
        )

        axes = function(
            "block",
            dict(
                width="100%",
                height="100%",
                stroke="red",
            ),
        )

        body = []
        for i, cell in enumerate(self.cells):
            body.append(
                function(
                    "grid.cell",
                    dict(
                        x=cell["x"],
                        y=cell["y"],
                        colspan=cell["colspan"],
                        rowspan=cell["rowspan"],
                    ),
                )(axes(f"axes-{i}()")),
            )

        return grid(",\n".join(body))
