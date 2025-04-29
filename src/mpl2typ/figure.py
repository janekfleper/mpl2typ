import pathlib
import matplotlib as mpl

from . import typst
from .axes import Axes
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


#let draw-xaxis-ticks(alignment, show-ticks: true, show-labels: true, ..args) = {
  let (tick-style, label-style, locs, labels) = args.named()
  if labels == () { labels = locs.len() * ("",) }
  set line(..tick-style.line)
  set text(..label-style.text)

  let (tick-alignment, tick-dy) = if tick-style.direction == "in" {
    (if alignment == bottom { bottom } else { top }, 0pt)
  } else if tick-style.direction == "out" {
    (if alignment == bottom { top } else { bottom }, tick-style.line.length)
  } else if tick-style.direction == "inout" {
    (horizon, tick-style.line.length / 2)
  } else {
    panic("Unknown tick direction '" + tick-style.direction + "'")
  }

  let label-alignment = center + if alignment == bottom { top } else { bottom }
  let label-dy = label-style.pad + tick-dy
  if alignment == top { label-dy = -label-dy }

  place(
    alignment,
    block(
      width: 100%,
      locs
        .zip(labels)
        .map(tick => {
          let (loc, label) = tick
          if (loc < 0%) or (loc > 100%) { return }
          place(
            dx: loc,
            {
              if show-ticks { place(tick-alignment, line()) }
              if show-labels {
                let body = rotate(label-style.rotation, reflow: true, label)
                place(label-alignment, dy: label-dy, body)
              }
            },
          )
        })
        .join([]),
    ),
  )
}

#let draw-yaxis-ticks(alignment, show-ticks: true, show-labels: true, ..args) = {
  let (tick-style, label-style, locs, labels) = args.named()
  if labels == () { labels = locs.len() * ("",) }
  set line(..tick-style.line)
  set text(..label-style.text)

  let (tick-alignment, tick-dx) = if tick-style.direction == "in" {
    (if alignment == left { left } else { right }, 0pt)
  } else if tick-style.direction == "out" {
    (if alignment == left { right } else { left }, tick-style.line.length)
  } else if tick-style.direction == "inout" {
    (horizon, tick-style.line.length / 2)
  } else {
    panic("Unknown tick direction '" + tick-style.direction + "'")
  }

  let label-alignment = horizon + if alignment == left { right } else { left }
  let label-dx = label-style.pad + tick-dx
  if alignment == left { label-dx = -label-dx }

  place(
    alignment,
    block(
      height: 100%,
      locs
        .zip(labels)
        .map(tick => {
          let (loc, label) = tick
          if (loc < 0%) or (loc > 100%) { return }
          place(
            dy: loc,
            {
              if show-ticks { place(tick-alignment, line()) }
              if show-labels {
                let body = place(label-alignment, label)
                place(dx: label-dx, rotate(label-style.rotation, body))
              }
            },
          )
        })
        .join([]),
    ),
  )
}
"""


def template(width: float, height: float):
    s = ""
    s += f"#let width = {width}cm\n"
    s += f"#let height = {height}cm\n\n"

    block = typst.function(
        "#block",
        named=dict(
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
        self.grids: list[Grid] = []
        self.other_axes: list[Axes] = []
        self.parse()

    @property
    def width(self):
        return self.fig.get_size_inches()[0] * 2.54

    @property
    def height(self):
        return self.fig.get_size_inches()[1] * 2.54

    def parse(self):
        grid_axes = []
        gridspecs = []
        for i, ax in enumerate(self.fig.get_axes()):
            gs = ax.get_gridspec()
            if gs is None:
                self.other_axes.append(Axes(i, ax, standalone=True))
            elif gs not in gridspecs:
                gridspecs.append(gs)
                grid_axes.append([Axes(i, ax)])
            else:
                grid_axes[gridspecs.index(gs)].append(Axes(i, ax))

        for i in range(len(gridspecs)):
            self.grids.append(Grid(i, gridspecs[i], grid_axes[i]))

    def export(self, path: str | pathlib.Path):
        with open(path, "w") as f:
            f.write("#set page(width: auto, height: auto, margin: 0.9mm)\n")
            f.write(header)
            f.write("\n\n")

            figure = template(
                width=self.width,
                height=self.height,
            )

            children = []
            for grid in self.grids:
                for ax in grid.axes:
                    f.write(ax.export() + "\n")
                f.write(grid.export() + "\n")
                children.append(f"grid-{grid.index}()")

            for ax in self.other_axes:
                f.write(ax.export() + "\n")
                children.append(f"other-axes-{ax.index}()")

            f.write(figure(typst.make_body(children)))
