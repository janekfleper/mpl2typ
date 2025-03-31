import textwrap

import matplotlib as mpl

from .line import get_stroke, get_marker

axes_header = """
  let xscale = 1 / (xlim.at(1) - xlim.at(0)) * 100%
  let yscale = -1 / (ylim.at(1) - ylim.at(0)) * 100%
  let xshift = 50% - (xlim.at(0) + xlim.at(1)) / 2 * xscale
  let yshift = 50% - (ylim.at(0) + ylim.at(1)) / 2 * yscale

  let transform(point) = {
    let (x, y) = point
    return (x * xscale + xshift, y * yscale + yshift)
  }
"""


def axes_template(ax: mpl.axes.Axes, index: int):
    xlim = f"({ax.get_xlim()[0]}, {ax.get_xlim()[1]})"
    ylim = f"({ax.get_ylim()[0]}, {ax.get_ylim()[1]})"

    s = f"#let axes-{index}(xlim: {xlim}, ylim: {ylim}) = {{"
    s += axes_header + "\n"

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
