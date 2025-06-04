import textwrap
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeVar, Generic

import matplotlib.axes
import matplotlib.axis
import matplotlib.lines
import matplotlib.collections

from . import typst
from .lines import Stroke, Line2D
from .collections import PathCollection, QuadMesh
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
    def tick_angle(self) -> str:
        pass

    @property
    @abstractmethod
    def draw_function(self) -> str:
        pass

    @property
    @abstractmethod
    def grid_function(self) -> str:
        pass

    @property
    @abstractmethod
    def tick_positions(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def label_positions(self) -> list[str]:
        pass

    @property
    def tick_style(self):
        tick = self.ticks[0]
        line = tick.tick1line
        stroke = f"{typst.color(str(line.get_color()), line.get_alpha())} + {line.get_markeredgewidth()}pt"
        return typst.dictionary(
            dict(
                direction=f'"{tick.get_tickdir()}"',
                line=typst.dictionary(
                    dict(
                        length=f"{line.get_markersize()}pt",
                        angle=self.tick_angle,
                        stroke=stroke,
                    ),
                    inline=True,
                ),
            ),
            inline=True,
        )

    @property
    def grid_style(self):
        line = self.ticks[0].gridline
        return typst.dictionary(dict(stroke=Stroke(line).export()), inline=True)

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
                        fill=typst.color(str(text.get_color()), text.get_alpha()),
                    ),
                    inline=True,
                ),
            ),
            inline=True,
        )

    @property
    def definition(self):
        items = {
            "locs": self.locs,
            "labels": self.labels,
            "tick-style": self.tick_style,
            "label-style": self.label_style,
        }
        if self.params.gridOn:
            items["grid-style"] = self.grid_style
        return f"let {self.name} = " + typst.dictionary(items)

    @property
    def draw(self):
        named = {
            "show-ticks": typst.array(self.tick_positions),
            "show-labels": typst.array(self.label_positions),
        }

        s = typst.function(
            self.draw_function,
            named=named,
            body=f"..{self.name}, transform",
            inline=True,
        )
        if self.params.gridOn:
            s += "\n"
            s += typst.function(
                self.grid_function,
                body=f"..{self.name}, transform",
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
        keys = ["bottom", "top", "labelbottom", "labeltop", "gridOn"]
        params = {k: v for k, v in params.items() if k in keys}
        self.params = XTickParams(**params)

    @property
    def tick_angle(self) -> str:
        return "90deg"

    @property
    def draw_function(self) -> str:
        return "axes.xaxis-ticks"

    @property
    def grid_function(self) -> str:
        return "axes.xaxis-grid"

    @property
    def tick_positions(self) -> list[str]:
        pos: list[str] = []
        if self.params.bottom:
            pos.append("bottom")
        if self.params.top:
            pos.append("top")
        return pos

    @property
    def label_positions(self) -> list[str]:
        pos: list[str] = []
        if self.params.labelbottom:
            pos.append("bottom")
        if self.params.labeltop:
            pos.append("top")
        return pos


class YTicks(Ticks[YTickParams]):
    def __init__(
        self,
        name: str,
        ticks: Sequence[matplotlib.axis.Tick],
        params: Mapping[str, bool],
    ):
        super().__init__(name, ticks)
        keys = ["left", "right", "labelleft", "labelright", "gridOn"]
        params = {k: v for k, v in params.items() if k in keys}
        self.params = YTickParams(**params)

    @property
    def tick_angle(self) -> str:
        return "0deg"

    @property
    def draw_function(self) -> str:
        return "axes.yaxis-ticks"

    @property
    def grid_function(self) -> str:
        return "axes.yaxis-grid"

    @property
    def tick_positions(self) -> list[str]:
        pos: list[str] = []
        if self.params.left:
            pos.append("left")
        if self.params.right:
            pos.append("right")
        return pos

    @property
    def label_positions(self) -> list[str]:
        pos: list[str] = []
        if self.params.labelleft:
            pos.append("left")
        if self.params.labelright:
            pos.append("right")
        return pos


class Axis:
    def __init__(self, ax: matplotlib.axes.Axes):
        self.ax = ax
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

    @property
    def transform(self):
        return self.ax.transAxes.inverted()

    @property
    def xlabel(self):
        if self.ax.get_xlabel():
            xlabel = Text("xaxis-label", self.ax.xaxis.get_label(), self.transform)
            return xlabel.export()
        return ""

    @property
    def ylabel(self):
        if self.ax.get_ylabel():
            ylabel = Text("yaxis-label", self.ax.yaxis.get_label(), self.transform)
            return ylabel.export()
        return ""

    @property
    def xoffset(self):
        xaxis_offset_text = self.ax.xaxis.get_offset_text()
        if xaxis_offset_text.get_text():
            xoffset = Text("xaxis-offset", xaxis_offset_text, self.transform)
            return xoffset.export()
        return ""

    @property
    def yoffset(self):
        yaxis_offset_text = self.ax.yaxis.get_offset_text()
        if yaxis_offset_text.get_text():
            yoffset = Text("yaxis-offset", yaxis_offset_text, self.transform)
            return yoffset.export()
        return ""

    @property
    def labels(self):
        s = ""
        if xlabel := self.xlabel:
            s += xlabel + "\n"
        if ylabel := self.ylabel:
            s += ylabel + "\n"
        return s

    @property
    def offsets(self):
        s = ""
        if xoffset := self.xoffset:
            s += xoffset + "\n"
        if yoffset := self.yoffset:
            s += yoffset + "\n"
        return s

    def export(self) -> str:
        definitions: list[str] = []
        draws: list[str] = []
        for ticks in self.xticks + self.yticks:
            definitions.append(ticks.definition)
            draws.append(ticks.draw)

        return (
            self.labels
            + self.offsets
            + "\n".join(definitions)
            + "\n"
            + "\n".join(draws)
            + "\n"
        )


class Axes:
    def __init__(self, index: int, ax: matplotlib.axes.Axes, standalone: bool = False):
        self.index = index
        self.ax = ax
        self.standalone = standalone

        self.title = Title(ax)
        self.axis = Axis(ax)

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

    @property
    def xlim(self):
        return f"({self.ax.get_xlim()[0]}, {self.ax.get_xlim()[1]})"

    @property
    def ylim(self):
        return f"({self.ax.get_ylim()[0]}, {self.ax.get_ylim()[1]})"

    @property
    def data(self):
        definitions: list[str] = []
        draws: list[str] = []
        for i, child in enumerate(self.ax.get_children()):
            if isinstance(child, matplotlib.lines.Line2D):
                line = Line2D(i, child)
                definitions.append(line.definition)
                draws.append(line.draw)
            elif isinstance(child, matplotlib.collections.PathCollection):
                collection = PathCollection(i, child)
                definitions.append(collection.definition)
                draws.append(collection.draw)
            elif isinstance(child, matplotlib.collections.QuadMesh):
                collection = QuadMesh(i, child)
                definitions.append(collection.definition)
                draws.append(collection.draw)
        return "\n".join(definitions) + "\n" + "\n".join(draws) + "\n"

    def export(self):
        s = f"#let axes-{self.index}(xlim: {self.xlim}, ylim: {self.ylim}) = {{"
        s += header + "\n"
        s += textwrap.indent(self.title.export(), "  ")
        s += textwrap.indent(self.data, "  ")
        s += textwrap.indent(self.axis.export(), "  ")
        s += "}\n\n"

        if self.standalone:
            s += typst.block(
                f"other-axes-{self.index}",
                self.padding,
                f"axes-{self.index}()",
            )
        return s
