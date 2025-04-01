import pathlib
import matplotlib as mpl

from .util import function, compute_gutter
from .axes import axes_template


header = """
#let draw-marker(points, marker: none) = {
  if marker == none { return }

  let dx = if marker.has("height") { marker.height / 2 } else { 0pt }
  let dy = if marker.has("width") { marker.width / 2 } else { 0pt }
  points.map(point => place(dx: point.at(0) - dx, dy: point.at(1) - dy, marker)).join([])
}

#let draw-line(points, stroke: none) = {
  if stroke == none { return }

  let (first, ..points) = points
  place(
    curve(
      stroke: stroke,
      curve.move(first),
      ..points.map(point => curve.line(point)),
    ),
  )
}
"""


def figure(
    width: float,
    height: float,
    left: float,
    right: float,
    top: float,
    bottom: float,
):
    s = ""
    s += f"#let width = {width}cm\n"
    s += f"#let height = {height}cm\n"
    s += "#let padding = (\n"
    s += f"  left: {left * 100:.3g}%,\n"
    s += f"  right: {(1 - right) * 100:.3g}%,\n"
    s += f"  top: {(1 - top) * 100:.3g}%,\n"
    s += f"  bottom: {bottom * 100:.3g}%,\n"
    s += ")\n\n"

    figure_block = function(
        "#block",
        dict(
            width="width",
            height="height",
            stroke="blue",
        ),
    )

    figure_place = function(
        "place",
        dict(dx="padding.left", dy="padding.top"),
    )

    inner_block = function(
        "block",
        dict(
            width="100% - padding.right - padding.left",
            height="100% - padding.top - padding.bottom",
            stroke="green",
        ),
    )

    def wrapper(body: str):
        return s + figure_block(figure_place(inner_block(body)))

    return wrapper


class Figure:
    def __init__(self, fig: mpl.figure.Figure):
        self.fig = fig

    def export(self, path: str | pathlib.Path):
        width, height = self.fig.get_size_inches() * 2.54
        spacing = self.fig.subplotpars

        with open(path, "w") as f:
            f.write("#set page(width: auto, height: auto, margin: 0.9mm)\n")
            f.write(header)
            f.write("\n\n")

            figure_template = figure(
                width=width,
                height=height,
                left=spacing.left,
                right=spacing.right,
                top=spacing.top,
                bottom=spacing.bottom,
            )

            axes = function(
                "block",
                dict(
                    width="100%",
                    height="100%",
                    stroke="red",
                ),
            )

            grid = []
            gridspec = None
            other = []
            for ax in self.fig.get_axes():
                if ax.get_gridspec() is not None:
                    gridspec = ax.get_gridspec()
                    grid.append(ax)
                else:
                    other.append(ax)

            for i, ax in enumerate(grid):
                f.write(axes_template(ax, i))

            if gridspec is not None:
                nrows, ncols = gridspec.get_geometry()
                columns = ", ".join(["1fr"] * ncols)
                rows = ", ".join(["1fr"] * nrows)
                column_gutter = f"{compute_gutter(spacing.wspace, ncols) * 100:.3g}%"
                row_gutter = f"{compute_gutter(spacing.hspace, nrows) * 100:.3g}%"
                axes_grid = function(
                    "grid",
                    {
                        "columns": f"({columns})",
                        "rows": f"({rows})",
                        "column-gutter": column_gutter,
                        "row-gutter": row_gutter,
                    },
                )(",\n".join([axes(f"axes-{i}()") for i in range(len(grid))]))
                f.write(figure_template(axes_grid))
