import textwrap
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeVar, Generic

import matplotlib.axes
import matplotlib.axis

from . import typst
from .line import Line2D
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


@dataclass
class XTickParams:
    bottom: bool
    labelbottom: bool
    top: bool
    labeltop: bool
    gridOn: bool


@dataclass
class YTickParams:
    left: bool
    labelleft: bool
    right: bool
    labelright: bool
    gridOn: bool


TickParams = TypeVar("TickParams", XTickParams, YTickParams)


def template(index: int, ax: matplotlib.axes.Axes):
    xlim = f"({ax.get_xlim()[0]}, {ax.get_xlim()[1]})"
    ylim = f"({ax.get_ylim()[0]}, {ax.get_ylim()[1]})"

    s = f"#let axes-{index}(xlim: {xlim}, ylim: {ylim}) = {{"
    s += header + "\n"

    title = Title(ax)
    s += textwrap.indent(title.export(), "  ")

    transform = ax.transAxes.inverted()
    if ax.get_xlabel():
        xlabel = Text("xaxis-label", ax.xaxis.get_label(), transform)
        s += textwrap.indent(xlabel.export(), "  ") + "\n\n"
    if ax.get_ylabel():
        ylabel = Text("yaxis-label", ax.yaxis.get_label(), transform)
        s += textwrap.indent(ylabel.export(), "  ") + "\n\n"
    xaxis_offset_text = ax.xaxis.get_offset_text()
    if xaxis_offset_text.get_text():
        xoffset = Text("xaxis-offset", xaxis_offset_text, transform)
        s += textwrap.indent(xoffset.export(), "  ") + "\n\n"
    yaxis_offset_text = ax.yaxis.get_offset_text()
    if yaxis_offset_text.get_text():
        yoffset = Text("yaxis-offset", yaxis_offset_text, transform)
        s += textwrap.indent(yoffset.export(), "  ") + "\n\n"

    definitions: list[str] = []
    draws: list[str] = []
    for i, _line in enumerate(ax.lines):
        line = Line2D(i, _line)
        definitions.append(line.definition)
        draws.append(line.draw)

    s += textwrap.indent("\n".join(definitions) + "\n", "  ")
    s += textwrap.indent("\n".join(draws) + "\n", "  ")

    axis = Axis(ax)
    s += textwrap.indent(axis.export(), "  ")

    s += "}\n\n"
    return s


class Title:
    def __init__(self, ax: matplotlib.axes.Axes):
        transform = ax.transAxes.inverted()
        self.center = (
            Text("title", ax.title, transform) if ax.get_title(loc="center") else None
        )
        self.left = (
            Text("title-left", ax._left_title, transform)  # type: ignore
            if ax.get_title(loc="left")
            else None
        )
        self.right = (
            Text("title-right", ax._right_title, transform)  # type: ignore
            if ax.get_title(loc="right")
            else None
        )

    def export(self):
        s = ""
        if self.center is not None:
            s += self.center.export() + "\n\n"
        if self.left is not None:
            s += self.left.export() + "\n\n"
        if self.right is not None:
            s += self.right.export() + "\n\n"
        return s


class Ticks(ABC, Generic[TickParams]):
    def __init__(
        self,
        name: str,
        ticks: Sequence[matplotlib.axis.Tick],
    ):
        self.name = name
        self.ticks = ticks
        self.params: TickParams

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

    @property
    def definition(self):
        return f"let {self.name} = " + typst.dictionary(
            {
                "locs": f"{self.locs}.{self.transform_function}",
                "labels": self.labels,
                "tick-style": self.tick_style,
                "label-style": self.label_style,
            },
        )

    @property
    def draw(self):
        s = ""
        for position, show in self.positions.items():
            if show["ticks"] or show["labels"]:
                pos = [position]
                named = {
                    "show-ticks": typst.boolean(show["ticks"]),
                    "show-labels": typst.boolean(show["labels"]),
                }
                s += typst.function(
                    self.draw_function,
                    pos=pos,
                    named=named,
                    body=f"..{self.name}",
                    inline=True,
                )
        return s


class XTicks(Ticks[XTickParams]):
    def __init__(
        self,
        name: str,
        ticks: Sequence[matplotlib.axis.Tick],
        params: Mapping[str, bool],
    ):
        super().__init__(name, ticks)
        self.params = XTickParams(**params)

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
            bottom=dict(ticks=self.params.bottom, labels=self.params.labelbottom),
            top=dict(ticks=self.params.top, labels=self.params.labeltop),
        )


class YTicks(Ticks[YTickParams]):
    def __init__(
        self,
        name: str,
        ticks: Sequence[matplotlib.axis.Tick],
        params: Mapping[str, bool],
    ):
        super().__init__(name, ticks)
        self.params = YTickParams(**params)

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
            left=dict(ticks=self.params.left, labels=self.params.labelleft),
            right=dict(ticks=self.params.right, labels=self.params.labelright),
        )


class Axis:
    def __init__(self, ax: matplotlib.axes.Axes):
        self.xticks: list[XTicks] = []
        self.yticks: list[YTicks] = []

        if ticks := ax.xaxis.get_major_ticks():
            params = ax.xaxis.get_tick_params(which="major")
            self.xticks.append(XTicks("xaxis-major-ticks", ticks, params))
        if ticks := ax.xaxis.get_minor_ticks():
            params = ax.xaxis.get_tick_params(which="minor")
            self.xticks.append(XTicks("xaxis-minor-ticks", ticks, params))
        if ticks := ax.yaxis.get_major_ticks():
            params = ax.yaxis.get_tick_params(which="major")
            self.yticks.append(YTicks("yaxis-major-ticks", ticks, params))
        if ticks := ax.yaxis.get_minor_ticks():
            params = ax.yaxis.get_tick_params(which="minor")
            self.yticks.append(YTicks("yaxis-minor-ticks", ticks, params))

    def export(self) -> str:
        definitions: list[str] = []
        draws: list[str] = []
        for ticks in self.xticks + self.yticks:
            definitions.append(ticks.definition)
            draws.append(ticks.draw)

        return "\n".join(definitions) + "\n" + "\n".join(draws) + "\n"


class Axes:
    def __init__(self, index: int, ax: matplotlib.axes.Axes, standalone: bool = False):
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
        if sps is None:
            raise ValueError("Axes is not part of a grid")
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
                f"axes-{self.index}()",
            )
        return s
