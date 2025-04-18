import textwrap

import matplotlib as mpl

from .line import get_stroke, get_marker

header = """
  let xscale = 1 / (xlim.at(1) - xlim.at(0)) * 100%
  let yscale = -1 / (ylim.at(1) - ylim.at(0)) * 100%
  let xshift = 50% - (xlim.at(0) + xlim.at(1)) / 2 * xscale
  let yshift = 50% - (ylim.at(0) + ylim.at(1)) / 2 * yscale

  let transform(point) = {
    let (x, y) = point
    return (x * xscale + xshift, y * yscale + yshift)
  }
"""


def template(index: int, ax: mpl.axes.Axes):
    xlim = f"({ax.get_xlim()[0]}, {ax.get_xlim()[1]})"
    ylim = f"({ax.get_ylim()[0]}, {ax.get_ylim()[1]})"

    s = f"#let axes-{index}(xlim: {xlim}, ylim: {ylim}) = {{"
    s += header + "\n"

    for i, line in enumerate(ax.lines):
        thickness, stroke = get_stroke(line)
        s += textwrap.indent(f"let thickness = {thickness}pt\n", "  ")
        s += textwrap.indent(f"let stroke-{i} = {stroke}\n\n", "  ")

        size, marker = get_marker(line)
        s += textwrap.indent(f"let d = {size}pt\n", "  ")
        s += textwrap.indent(f"let marker-{i} = {marker}\n\n", "  ")

    for i, line in enumerate(ax.lines):
        points = line.get_xydata()
        s += f"  let data-{i} = (\n"
        for x, y in points:
            s += f"    ({x}, {y}),\n"
        s += "  ).map(point => transform(point))\n\n"

    for i, line in enumerate(ax.lines):
        s += f"  draw-line(data-{i}, stroke:stroke-{i})\n"
        s += f"  draw-marker(data-{i}, marker:marker-{i})\n"
    s += "}\n\n"
    return s


class Axes:
    def __init__(self, index: int, ax: mpl.axes.Axes):
        self.index = index
        self.ax = ax

    @property
    def position(self):
        return self.ax.get_position()

    @property
    def cell(self):
        sps = self.ax.get_subplotspec()
        x = sps.colspan.start
        y = sps.rowspan.start
        colspan = sps.colspan.stop - x
        rowspan = sps.rowspan.stop - y
        return dict(i=self.index, x=x, y=y, colspan=colspan, rowspan=rowspan)

    def export(self):
        return template(self.index, self.ax)
