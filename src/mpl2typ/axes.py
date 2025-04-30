import textwrap
from abc import ABC, abstractmethod

import numpy as np
import matplotlib as mpl

from . import typst
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


class Ticks(ABC):
    def __init__(self, name: str, ticks: list[mpl.axis.Tick], params: dict):
        self.name = name
        self.ticks = ticks
        self.params = params

    @property
    def locs(self):
        return typst.array([f"{tick.get_loc()}" for tick in self.ticks])

    @property
    def labels(self):
        return typst.array([f'"{tick.label1.get_text()}"' for tick in self.ticks])

    @property
    @abstractmethod
    def line_angle(self) -> str:
        pass

    @property
    @abstractmethod
    def draw_function(self) -> str:
        pass

    @property
    @abstractmethod
    def transform_function(self) -> str:
        pass

    @property
    @abstractmethod
    def positions(self) -> dict[str, dict[str, bool]]:
        pass

    @property
    def tick_style(self):
        tick = self.ticks[0]
        line = tick.tick1line
        return typst.dictionary(
            dict(
                direction=f'"{tick.get_tickdir()}"',
                line=typst.dictionary(
                    dict(
                        length=f"{line.get_markersize()}pt",
                        angle=self.line_angle,
                        stroke=f"{line.get_color()} + {line.get_markeredgewidth()}pt",
                    ),
                    inline=True,
                ),
            ),
            inline=True,
        )

    @property
    def label_style(self):
        tick = self.ticks[0]
        text = self.ticks[0].label1
        return typst.dictionary(
            dict(
                pad=f"{tick.get_pad()}pt",
                rotation=f"{-text.get_rotation()}deg",
                text=typst.dictionary(
                    dict(
                        size=f"{text.get_fontsize()}pt",
                        fill=f"{text.get_color()}",
                    ),
                    inline=True,
                ),
            ),
            inline=True,
        )

    def export(self):
        s = ""
        if not self.ticks:
            return s

        s += f"let {self.name} = "
        s += typst.dictionary(
            {
                "locs": f"{self.locs}.{self.transform_function}",
                "labels": self.labels,
                "tick-style": self.tick_style,
                "label-style": self.label_style,
            },
        )
        s += "\n"

        calls = []
        for pos, show in self.positions.items():
            if show["ticks"] or show["labels"]:
                calls.append(
                    typst.function(
                        self.draw_function,
                        pos=[pos],
                        named={
                            "show-ticks": typst.boolean(show["ticks"]),
                            "show-labels": typst.boolean(show["labels"]),
                        },
                        inline=True,
                    )(f"..{self.name}")
                )

        if calls:
            s += "\n".join(calls)
            s += "\n"

        return s


class XTicks(Ticks):
    @property
    def line_angle(self) -> str:
        return "90deg"

    @property
    def draw_function(self) -> str:
        return "draw-xaxis-ticks"

    @property
    def transform_function(self) -> str:
        return "map(x => (x, 0)).map(transform).map(point => point.at(0))"

    @property
    def positions(self) -> dict[str, dict[str, bool]]:
        return dict(
            bottom=dict(ticks=self.params["bottom"], labels=self.params["labelbottom"]),
            top=dict(ticks=self.params["top"], labels=self.params["labeltop"]),
        )


class YTicks(Ticks):
    @property
    def line_angle(self) -> str:
        return "0deg"

    @property
    def draw_function(self) -> str:
        return "draw-yaxis-ticks"

    @property
    def transform_function(self) -> str:
        return "map(y => (0, y)).map(transform).map(point => point.at(1))"

    @property
    def positions(self) -> dict[str, dict[str, bool]]:
        return dict(
            left=dict(ticks=self.params["left"], labels=self.params["labelleft"]),
            right=dict(ticks=self.params["right"], labels=self.params["labelright"]),
        )


class Axis:
    def __init__(self, ax: mpl.axes.Axes):
        xaxis_major_ticks = ax.xaxis.get_major_ticks()
        yaxis_major_ticks = ax.yaxis.get_major_ticks()

        self.xticks = XTicks(
            "xaxis-major-ticks",
            xaxis_major_ticks,
            ax.xaxis.get_tick_params(which="major"),
        )
        self.yticks = YTicks(
            "yaxis-major-ticks",
            yaxis_major_ticks,
            ax.yaxis.get_tick_params(which="major"),
        )

    def export(self):
        s = ""
        s += self.xticks.export()
        s += self.yticks.export()
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
            s += typst.block(
                f"other-axes-{self.index}",
                self.padding,
            )(f"axes-{self.index}()")
        return s
