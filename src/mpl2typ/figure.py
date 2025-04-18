import pathlib
import matplotlib as mpl

from .util import function
from .axes import axes_template
from .grid import Grid


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


def template(width: float, height: float):
    s = ""
    s += f"#let width = {width}cm\n"
    s += f"#let height = {height}cm\n\n"

    block = function(
        "#block",
        dict(
            width="width",
            height="height",
            stroke="blue",
        ),
    )

    def wrapper(body: str):
        return s + block(body)

    return wrapper


class Figure:
    def __init__(self, fig: mpl.figure.Figure):
        self.fig = fig

    def export(self, path: str | pathlib.Path):
        width, height = self.fig.get_size_inches() * 2.54

        with open(path, "w") as f:
            f.write("#set page(width: auto, height: auto, margin: 0.9mm)\n")
            f.write(header)
            f.write("\n\n")

            figure = template(
                width=width,
                height=height,
            )

            grids = []
            gridspecs = []
            other = []
            for ax in self.fig.get_axes():
                gs = ax.get_gridspec()
                if gs is None:
                    other.append(ax)
                    continue
                elif gs not in gridspecs:
                    gridspecs.append(gs)
                    grids.append([ax])
                else:
                    grids[gridspecs.index(gs)].append(ax)

            if not gridspecs:
                return
            elif len(gridspecs) > 1:
                raise ValueError("Only one gridspec is supported for now")

            for i, ax in enumerate(grids[0]):
                f.write(axes_template(ax, i))

            grid = Grid(0, gridspecs[0], grids[0])
            f.write(grid.export() + "\n")
            f.write(figure("grid-0()"))
