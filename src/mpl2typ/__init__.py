import pathlib
import textwrap
from typing import Callable

import matplotlib as mpl

file_header = """
#let draw-marker(points, marker: none) = {
  if marker == none { return }

  let dx = marker.width / 2
  let dy = marker.height / 2
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

axes_header = """
  let xscale = 1 / (xlim.at(1) - xlim.at(0)) * 100%
  let yscale = -1 / (ylim.at(1) - ylim.at(0)) * 100%
  let xshift = 50% - (xlim.at(0) + xlim.at(1)) / 2 * xscale
  let yshift = 50% - (ylim.at(0) + ylim.at(1)) / 2 * yscale

  let transform(point) = {
    let (x, y) = point
    return (x * xscale + xshift, y * yscale + yshift)
  }

  let draw-marker = draw-marker.with(marker: circle(radius: 4pt, fill: red, stroke: black))
  let draw-line = draw-line.with(stroke: blue + 2pt)
"""


def function(
    name: str,
    args: dict[str, str],
    comment: str = "",
) -> Callable[[str], str]:
    def wrapper(body: str):
        return (
            f"{name}({' // ' + comment if comment else ''}\n"
            + textwrap.indent(",\n".join([f"{k}: {v}" for k, v in args.items()]), "  ")
            + ",\n"
            + textwrap.indent(body, "  ")
            + "\n)"
        )

    return wrapper


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
    s += f"#let height = {height}cm\n\n"

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
        dict(
            dx=f"{left * 100:.3g}%",
            dy=f"{(1 - top) * 100:.3g}%",
        ),
    )

    inner_block = function(
        "block",
        dict(
            width=f"{(right - left) * 100:.3g}%",
            height=f"{(top - bottom) * 100:.3g}%",
            stroke="green",
        ),
    )

    def wrapper(body: str):
        return s + figure_block(figure_place(inner_block(body)))

    return wrapper


def compute_gutter(space: float, n: int):
    return space / (n + (n - 1) * space)


def axes_template(ax: mpl.axes.Axes, index: int):
    xlim = f"({ax.get_xlim()[0]}, {ax.get_xlim()[1]})"
    ylim = f"({ax.get_ylim()[0]}, {ax.get_ylim()[1]})"

    s = f"#let axes-{index}(xlim: {xlim}, ylim: {ylim}) = {{"
    s += axes_header + "\n"

    for i, line in enumerate(ax.lines):
        points = line.get_xydata()
        s += f"  let data-{i} = (\n"
        for x, y in points:
            s += f"    ({x}, {y}),\n"
        s += "  ).map(point => transform(point))\n\n"

    for i, line in enumerate(ax.lines):
        s += f"  draw-line(data-{i})\n"
        s += f"  draw-marker(data-{i})\n"
    s += "}\n\n"
    return s


class TypstFigure:
    def __init__(self, fig: mpl.figure.Figure):
        self.fig = fig

    def export(self, path: str | pathlib.Path):
        width, height = self.fig.get_size_inches() * 2.54
        spacing = self.fig.subplotpars

        with open(path, "w") as f:
            f.write("#set page(width: auto, height: auto, margin: 0.9mm)\n")
            f.write(file_header)
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
