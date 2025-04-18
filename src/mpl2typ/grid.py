import textwrap
import matplotlib as mpl

from .util import function, compute_gutter


def template(index: int, left: float, right: float, top: float, bottom: float):
    s = ""
    s += "let padding = (\n"
    s += f"  left: {left * 100:.3g}%,\n"
    s += f"  right: {right * 100:.3g}%,\n"
    s += f"  top: {top * 100:.3g}%,\n"
    s += f"  bottom: {bottom * 100:.3g}%,\n"
    s += ")\n\n"

    place = function(
        "place",
        dict(dx="padding.left", dy="padding.top"),
    )

    block = function(
        "block",
        dict(
            width="100% - padding.right - padding.left",
            height="100% - padding.top - padding.bottom",
            stroke="green",
        ),
    )

    def wrapper(body: str):
        return (
            f"#let grid-{index}() = {{\n"
            + textwrap.indent(s, "  ")
            + textwrap.indent(place(block(body)), "  ")
            + "\n}\n\n"
        )

    return wrapper


class Grid:
    def __init__(
        self,
        index: int,
        grid: mpl.gridspec.GridSpec,
        axes: list[mpl.axes.Axes],
    ):
        self.index = index
        self.grid = grid
        self.axes = axes

        self.column_gutter = compute_gutter(self.wspace, self.grid.ncols)
        self.row_gutter = compute_gutter(self.hspace, self.grid.nrows)

        self.cells: list[dict] = []
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

    def parse(self):
        # find the outer bounding box of all axes
        x0, x1, y0, y1 = [], [], [], []

        for ax in self.axes:
            position = ax.get_position()
            x0.append(position.x0)
            x1.append(position.x1)
            y0.append(position.y0)
            y1.append(position.y1)

            sps = ax.get_subplotspec()
            x = sps.colspan.start
            y = sps.rowspan.start
            colspan = sps.colspan.stop - x
            rowspan = sps.rowspan.stop - y
            self.cells.append(dict(x=x, y=y, colspan=colspan, rowspan=rowspan))

        self.padding = dict(
            left=min(x0),
            right=1 - max(x1),
            top=1 - max(y1),
            bottom=min(y0),
        )

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

        return template(
            self.index,
            self.padding["left"],
            self.padding["right"],
            self.padding["top"],
            self.padding["bottom"],
        )(grid(",\n".join(body)))
