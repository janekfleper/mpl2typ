import textwrap
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeVar, Generic

import matplotlib.axes
import matplotlib.axis
import matplotlib.text
import matplotlib.lines
import matplotlib.collections

from . import typst
from .lines import Stroke, Line2D
from .collections import Collection, QuadMesh
from .legend import Legend
from .text import Text

header = """
  let xscale = 1 / (xlim.at(1) - xlim.at(0)) * 100%
  let yscale = 1 / (ylim.at(1) - ylim.at(0)) * 100%
  let xshift = 50% - (xlim.at(0) + xlim.at(1)) / 2 * xscale
  let yshift = 50% - (ylim.at(0) + ylim.at(1)) / 2 * yscale

  let transform(point) = {
    let (x, y) = point
    return (x * xscale + xshift, 100% - (y * yscale + yshift))
  }

  let compute-scale(size) = calc.sqrt(size) * dpi / 72
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
        self.center = (
            Text("title", ax.title, ax) if ax.get_title(loc="center") else None
        )
        self.left = (
            Text("title-left", ax._left_title, ax)  # type: ignore
            if ax.get_title(loc="left")
            else None
        )
        self.right = (
            Text("title-right", ax._right_title, ax)  # type: ignore
            if ax.get_title(loc="right")
            else None
        )

    @property
    def definition(self):
        definitions = []
        if self.center is not None:
            definitions.append(self.center.definition)
        if self.left is not None:
            definitions.append(self.left.definition)
        if self.right is not None:
            definitions.append(self.right.definition)
        return "\n".join(definitions)

    @property
    def draw(self) -> list[tuple[str, float]]:
        draws = []
        if self.center is not None:
            draws.append(self.center.draw)
        if self.left is not None:
            draws.append(self.left.draw)
        if self.right is not None:
            draws.append(self.right.draw)
        return draws

    def export(self) -> str:
        return self.definition + "\n" + "\n".join([draw[0] for draw in self.draw])


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
    def draw(self) -> tuple[str, float]:
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
        return (s, self.ticks[0].tick1line.zorder)


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
    def xlabel(self):
        if self.ax.get_xlabel():
            return Text("xaxis-label", self.ax.xaxis.get_label(), self.ax)

    @property
    def ylabel(self):
        if self.ax.get_ylabel():
            return Text("yaxis-label", self.ax.yaxis.get_label(), self.ax)

    @property
    def xoffset(self):
        xaxis_offset_text = self.ax.xaxis.get_offset_text()
        if xaxis_offset_text.get_text():
            return Text("xaxis-offset", xaxis_offset_text, self.ax)

    @property
    def yoffset(self):
        yaxis_offset_text = self.ax.yaxis.get_offset_text()
        if yaxis_offset_text.get_text():
            return Text("yaxis-offset", yaxis_offset_text, self.ax)

    @property
    def definition(self) -> str:
        definitions: list[str] = []
        if self.xlabel is not None:
            definitions.append(self.xlabel.definition)
        if self.ylabel is not None:
            definitions.append(self.ylabel.definition)
        if self.xoffset is not None:
            definitions.append(self.xoffset.definition)
        if self.yoffset is not None:
            definitions.append(self.yoffset.definition)
        for ticks in self.xticks + self.yticks:
            definitions.append(ticks.definition)
        return "\n".join(definitions)

    @property
    def draw(self) -> list[tuple[str, float]]:
        draws: list[tuple[str, float]] = []
        if self.xlabel is not None:
            draws.append(self.xlabel.draw)
        if self.ylabel is not None:
            draws.append(self.ylabel.draw)
        if self.xoffset is not None:
            draws.append(self.xoffset.draw)
        if self.yoffset is not None:
            draws.append(self.yoffset.draw)
        for ticks in self.xticks + self.yticks:
            draws.append(ticks.draw)
        return draws


class Axes:
    def __init__(self, index: int, ax: matplotlib.axes.Axes, standalone: bool = False):
        self.index = index
        self.ax = ax
        self.standalone = standalone

        self.title = Title(ax)
        self.axis = Axis(ax)

        if ax.legend_ is not None:
            self.legend = Legend(ax.legend_)
        else:
            self.legend = None

        self.definitions: list[str] = []
        self.draws: list[tuple[str, float]] = []

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

    def export_data(self):
        for i, child in enumerate(self.ax._children):  # type: ignore
            if isinstance(child, matplotlib.lines.Line2D):
                line = Line2D(i, child)
                self.definitions.append(line.definition)
                self.draws.append(line.draw)
            elif isinstance(child, matplotlib.collections.QuadMesh):
                collection = QuadMesh(i, child)
                self.definitions.append(collection.definition)
                self.draws.append(collection.draw)
            elif isinstance(child, matplotlib.collections.Collection):
                collection = Collection(i, child)
                self.definitions.append(collection.definition)
                self.draws.append(collection.draw)
            elif isinstance(child, matplotlib.text.Text):
                text = Text(f"text-{i}", child, self.ax)
                self.definitions.append(text.definition)
                self.draws.append(text.draw)

    def export(self):
        self.definitions.append(self.title.definition)
        self.draws.extend(self.title.draw)
        self.definitions.append(self.axis.definition)
        self.draws.extend(self.axis.draw)
        self.export_data()
        if self.legend is not None:
            self.definitions.append(self.legend.definition)
            self.draws.append(self.legend.draw)
        draws = [draw[0] for draw in sorted(self.draws, key=lambda x: x[1])]

        s = f"#let axes-{self.index}(xlim: {self.xlim}, ylim: {self.ylim}, dpi: {self.ax.figure.dpi}) = {{"
        s += header + "\n"
        s += textwrap.indent("\n\n".join(self.definitions), "  ") + "\n"
        s += textwrap.indent("\n".join(draws), "  ") + "\n"
        s += "}\n\n"

        if self.standalone:
            s += typst.block(
                f"other-axes-{self.index}",
                self.padding,
                f"axes-{self.index}()",
            )
        return s
