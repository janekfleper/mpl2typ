import textwrap

import numpy as np
import matplotlib as mpl

from .util import boolean, array, dictionary, block
from .line import get_stroke, get_marker
from .text import Text

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

    title = Title(ax)
    s += textwrap.indent(title.export(), "  ")

    for i, line in enumerate(ax.lines):
        thickness, stroke = get_stroke(line)
        s += textwrap.indent(f"let thickness = {thickness}pt\n", "  ")
        s += textwrap.indent(f"let stroke-{i} = {stroke}\n\n", "  ")

        if line.get_marker() == "None":
            s += textwrap.indent(f"let marker-{i} = none\n\n", "  ")
        else:
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
        s += f"  draw-line(data-{i}, stroke: stroke-{i})\n"
        s += f"  draw-marker(data-{i}, marker: marker-{i})\n"
    s += "\n"

    axis = Axis(ax)
    s += textwrap.indent(axis.export(), "  ")

    s += "}\n\n"
    return s


class Title:
    def __init__(self, ax: mpl.axes.Axes):
        self.center = ax.title if ax.get_title(loc="center") else None
        self.left = ax._left_title if ax.get_title(loc="left") else None
        self.right = ax._right_title if ax.get_title(loc="right") else None

        transform = np.linalg.inv(ax.transAxes.get_matrix())
        offset = np.hstack([ax.titleOffsetTrans.get_matrix()[:2, 2], np.zeros(1)])
        self.offset = tuple((transform @ offset)[:2])

    def export(self):
        s = ""
        if self.center is not None:
            title = Text("title", self.center, offset=self.offset)
            s += title.export() + "\n\n"
        if self.left is not None:
            title = Text("title-left", self.left, offset=self.offset)
            s += title.export() + "\n\n"
        if self.right is not None:
            title = Text("title-right", self.right, offset=self.offset)
            s += title.export() + "\n\n"
        return s


class Axis:
    def __init__(self, ax: mpl.axes.Axes):
        xaxis_major_ticks = ax.xaxis.get_major_ticks()
        self.xaxis_major = dict(
            locs=self.get_tick_locs(xaxis_major_ticks),
            labels=self.get_tick_labels(xaxis_major_ticks),
            tick_style=self.get_tick_style(xaxis_major_ticks[0], "x"),
            label_style=self.get_tick_label_style(xaxis_major_ticks[0]),
            params=ax.xaxis.get_tick_params(which="major"),
        )

        yaxis_major_ticks = ax.yaxis.get_major_ticks()
        self.yaxis_major = dict(
            locs=self.get_tick_locs(yaxis_major_ticks),
            labels=self.get_tick_labels(yaxis_major_ticks),
            tick_style=self.get_tick_style(yaxis_major_ticks[0], "y"),
            label_style=self.get_tick_label_style(yaxis_major_ticks[0]),
            params=ax.yaxis.get_tick_params(which="major"),
        )

    def get_tick_locs(self, ticks: list[mpl.axis.XTick]):
        return array([f"{tick.get_loc()}" for tick in ticks])

    def get_tick_labels(self, ticks: list[mpl.axis.XTick]):
        return array([f'"{tick.label1.get_text()}"' for tick in ticks])

    def get_tick_style(self, tick: mpl.axis.XTick, axis: str):
        line = tick.tick1line
        return dictionary(
            dict(
                direction=f'"{tick.get_tickdir()}"',
                line=dictionary(
                    dict(
                        length=f"{line.get_markersize()}pt",
                        angle=f"{90 if axis == 'x' else 0}deg",
                        stroke=f"{line.get_color()} + {line.get_markeredgewidth()}pt",
                    )
                ),
            )
        )

    def get_tick_label_style(self, tick: mpl.axis.XTick):
        text = tick.label1
        return dictionary(
            dict(
                pad=f"{tick.get_pad()}pt",
                rotation=f"{-text.get_rotation()}deg",
                text=dictionary(
                    dict(
                        size=f"{text.get_fontsize()}pt",
                        fill=f"{text.get_color()}",
                    )
                ),
            )
        )

    def export(self):
        s = ""
        s += "let xaxis-major-ticks = (\n"
        s += f"  locs: {self.xaxis_major['locs']}.map(x => (x, 0)).map(transform).map(point => point.at(0)),\n"
        s += f"  labels: {self.xaxis_major['labels']},\n"
        s += f"  tick-style: {self.xaxis_major['tick_style']},\n"
        s += f"  label-style: {self.xaxis_major['label_style']},\n"
        s += ")\n"

        tick_bottom = self.xaxis_major["params"]["bottom"]
        label_bottom = self.xaxis_major["params"]["labelbottom"]
        tick_top = self.xaxis_major["params"]["top"]
        label_top = self.xaxis_major["params"]["labeltop"]

        if tick_bottom or label_bottom:
            s += f"draw-xaxis-ticks(bottom, show-ticks: {boolean(tick_bottom)}, show-labels: {boolean(label_bottom)}, ..xaxis-major-ticks)\n"
        if tick_top or label_top:
            s += f"draw-xaxis-ticks(top, show-ticks: {boolean(tick_top)}, show-labels: {boolean(label_top)}, ..xaxis-major-ticks)\n"
        s += "\n"

        s += "let yaxis-major-ticks = (\n"
        s += f"  locs: {self.yaxis_major['locs']}.map(y => (0, y)).map(transform).map(point => point.at(1)),\n"
        s += f"  labels: {self.yaxis_major['labels']},\n"
        s += f"  tick-style: {self.yaxis_major['tick_style']},\n"
        s += f"  label-style: {self.yaxis_major['label_style']},\n"
        s += ")\n"

        tick_left = self.yaxis_major["params"]["left"]
        label_left = self.yaxis_major["params"]["labelleft"]
        tick_right = self.yaxis_major["params"]["right"]
        label_right = self.yaxis_major["params"]["labelright"]

        if tick_left or label_left:
            s += f"draw-yaxis-ticks(left, show-ticks: {boolean(tick_left)}, show-labels: {boolean(label_left)}, ..yaxis-major-ticks)\n"
        if tick_right or label_right:
            s += f"draw-yaxis-ticks(right, show-ticks: {boolean(tick_right)}, show-labels: {boolean(label_right)}, ..yaxis-major-ticks)\n"

        return s


class Axes:
    def __init__(self, index: int, ax: mpl.axes.Axes, standalone: bool = False):
        self.index = index
        self.ax = ax
        self.standalone = standalone

    @property
    def position(self):
        return self.ax.get_position()

    @property
    def padding(self):
        """
        Compute the padding from the position of the axes.

        This is used for standalone axes that have to be placed manually.
        """
        position = self.position
        return dict(
            left=position.x0,
            right=1 - position.x1,
            top=1 - position.y1,
            bottom=position.y0,
        )

    @property
    def cell(self):
        sps = self.ax.get_subplotspec()
        x = sps.colspan.start
        y = sps.rowspan.start
        colspan = sps.colspan.stop - x
        rowspan = sps.rowspan.stop - y
        return dict(x=x, y=y, colspan=colspan, rowspan=rowspan)

    def export(self):
        s = template(self.index, self.ax)
        if self.standalone:
            s += block(
                f"other-axes-{self.index}",
                self.padding,
            )(f"axes-{self.index}()")
        return s
