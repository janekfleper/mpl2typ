import json
import pathlib
import textwrap
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeVar, Generic, Any

import numpy as np
import matplotlib
import matplotlib.axes
import matplotlib.axis
import matplotlib.text
import matplotlib.inset
import matplotlib.lines
import matplotlib.collections

from . import typst
from .lines import Stroke, Line2D
from .collections import Collection, QuadMesh
from .legend import Legend
from .text import Text, relativ_fontsize


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


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
    def __init__(self, axes: "Axes"):
        ax = axes.ax
        self.center = (
            Text(ax.title, axes, "main", prefix="title")
            if ax.get_title(loc="center")
            else None
        )
        self.left = (
            Text(ax._left_title, axes, "left", prefix="title")  # type: ignore
            if ax.get_title(loc="left")
            else None
        )
        self.right = (
            Text(ax._right_title, axes, "right", prefix="title")  # type: ignore
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
        ticks: Sequence[matplotlib.axis.Tick],
        name: str,
    ):
        self.name = name
        self.ticks = ticks
        self.params: TickParams

    @property
    def locs(self) -> list[str]:
        return [str(tick.get_loc()) for tick in self.ticks]

    @property
    def labels(self) -> list[str]:
        labels = [tick.label1.get_text() for tick in self.ticks]
        if any([bool(label) for label in labels]):
            return [f"${label}$" for label in labels]
        return []

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
    def tick_style(self) -> dict[str, str | dict[str, str]]:
        tick = self.ticks[0]
        line = tick.tick1line
        stroke = (
            typst.color(line.get_color(), line.get_alpha())
            + " + "
            + typst.length(line.get_markeredgewidth(), "pt")
        )
        return dict(
            direction=typst.string(tick.get_tickdir()),
            line=dict(
                length=typst.length(line.get_markersize(), "pt"),
                angle=self.tick_angle,
                stroke=stroke,
            ),
        )

    @property
    def grid_style(self) -> dict[str, str]:
        line = self.ticks[0].gridline
        return dict(stroke=Stroke(line).export())

    @property
    def label_style(self) -> dict[str, str | dict[str, str]]:
        tick = self.ticks[0]
        text = self.ticks[0].label1
        return dict(
            pad=typst.length(tick.get_pad(), "pt"),
            rotation=typst.degree(-text.get_rotation()),
            text=dict(
                size=relativ_fontsize(float(text.get_fontsize())),
                fill=typst.color(str(text.get_color()), text.get_alpha()),
            ),
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
        return f"let {self.name} = " + typst.dump(items)

    @property
    def draw(self) -> tuple[str, float]:
        named = {
            "show-ticks": self.tick_positions,
            "show-labels": self.label_positions,
        }

        s = ""
        if self.params.gridOn:
            s += typst.function(
                self.grid_function,
                body=f"..{self.name}, transform",
                inline=True,
            )
            s += "\n"
        s += typst.function(
            self.draw_function,
            named=named,
            body=f"..{self.name}, transform",
            inline=True,
        )
        return (s, self.ticks[0].tick1line.zorder)


class XTicks(Ticks[XTickParams]):
    def __init__(
        self,
        ticks: Sequence[matplotlib.axis.Tick],
        name: str,
        params: Mapping[str, bool],
    ):
        super().__init__(ticks, name)
        keys = ["bottom", "top", "labelbottom", "labeltop", "gridOn"]
        params = {k: v for k, v in params.items() if k in keys}
        self.params = XTickParams(**params)

    @property
    def tick_angle(self) -> str:
        return typst.degree(90)

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
        ticks: Sequence[matplotlib.axis.Tick],
        name: str,
        params: Mapping[str, bool],
    ):
        super().__init__(ticks, name)
        keys = ["left", "right", "labelleft", "labelright", "gridOn"]
        params = {k: v for k, v in params.items() if k in keys}
        self.params = YTickParams(**params)

    @property
    def tick_angle(self) -> str:
        return typst.degree(0)

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
    def __init__(self, axes: "Axes"):
        self.axes = axes

    @property
    def ax(self) -> matplotlib.axes.Axes:
        return self.axes.ax

    @property
    def xlabel(self):
        if self.axes.ax.get_xlabel():
            return Text(self.ax.xaxis.get_label(), self.axes, "xaxis", prefix="label")

    @property
    def ylabel(self):
        if self.axes.ax.get_ylabel():
            return Text(self.ax.yaxis.get_label(), self.axes, "yaxis", prefix="label")

    @property
    def xoffset(self):
        xaxis_offset_text = self.ax.xaxis.get_offset_text()
        if xaxis_offset_text.get_text():
            return Text(xaxis_offset_text, self.axes, "xaxis", prefix="offset-label")

    @property
    def yoffset(self):
        yaxis_offset_text = self.ax.yaxis.get_offset_text()
        if yaxis_offset_text.get_text():
            return Text(yaxis_offset_text, self.axes, "yaxis", prefix="offset-label")

    @property
    def xticks(self) -> list[XTicks]:
        xticks: list[XTicks] = []
        if ticks := self.ax.xaxis.get_major_ticks():
            params = self.ax.xaxis.get_tick_params(which="major")
            xticks.append(XTicks(ticks, "xaxis-major-ticks", params))
        if ticks := self.ax.xaxis.get_minor_ticks():
            params = self.ax.xaxis.get_tick_params(which="minor")
            xticks.append(XTicks(ticks, "xaxis-minor-ticks", params))
        return xticks

    @property
    def yticks(self) -> list[YTicks]:
        yticks: list[YTicks] = []
        if ticks := self.ax.yaxis.get_major_ticks():
            params = self.ax.yaxis.get_tick_params(which="major")
            yticks.append(YTicks(ticks, "yaxis-major-ticks", params))
        if ticks := self.ax.yaxis.get_minor_ticks():
            params = self.ax.yaxis.get_tick_params(which="minor")
            yticks.append(YTicks(ticks, "yaxis-minor-ticks", params))
        return yticks

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


class Spines:
    def __init__(self, ax):
        self.spines = ax.spines
        self.transform = ax.transLimits

    def get_bounds(self, spine) -> str:
        points = self.transform.transform_path(spine.get_path()).vertices
        if isinstance(spine.axis, matplotlib.axis.YAxis):
            return typst.ratio(1 - points[:, 1])
        elif isinstance(spine.axis, matplotlib.axis.XAxis):
            return typst.ratio(points[:, 0])
        else:
            raise TypeError(f"Unknown axis type {type(spine.axis)}")

    @staticmethod
    def get_stroke(spine) -> str:
        return typst.stroke(
            spine.get_edgecolor(),
            spine.get_linewidth(),
            spine.get_linestyle(),
        )

    @property
    def definition(self):
        spines = {}
        for key in self.spines:
            spine = self.spines[key]
            if type(spine) is matplotlib.spines.Spine and spine.get_visible():
                spines[key] = dict(
                    bounds=self.get_bounds(spine), stroke=self.get_stroke(spine)
                )
        return "let spines = " + typst.dump(spines)

    @property
    def draw(self) -> tuple[str, float]:
        return (
            typst.function("axes.spines", body="spines", inline=True),
            self.spines.left.zorder,
        )


class AxesBase:
    def __init__(
        self,
        ax: matplotlib.axes.Axes,
        name: str,
        prefix: str = "axes",
        standalone: bool = False,
    ):
        self._name = name
        self.ax = ax
        self._prefix = prefix
        self.standalone = standalone

    @property
    def name(self) -> str:
        return self._prefix + "-" + self._name

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
    def patch(self) -> tuple[str, float]:
        fill = typst.color(self.ax.get_facecolor(), self.ax.get_alpha())
        patch = typst.function(
            "rect",
            named=dict(width="100%", height="100%", fill=fill, stroke="none"),
            inline=True,
        )
        return (
            typst.function("std.place", body=patch, inline=True),
            self.ax.patch.zorder,
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
        return dict(position=(x, y), shape=(colspan, rowspan))

    def transform_point(self, point, transform) -> str | tuple[str, str]:
        """
        Transform a point from any coordinates to relative axes coordinates.

        In Typst, the relative axes coordinates range from 0% to 100% in both
        directions, although the y-axis is inverted compared to matplotlib.
        """
        x, y = point
        if transform == self.ax.transData:
            return typst.function("transform", pos=[typst.array([x, y])], inline=True)
        elif transform == self.ax.transAxes:
            return typst.ratio((x, 1 - y))
        elif isinstance(transform, matplotlib.transforms.IdentityTransform):
            (x0, y0), (x1, y1) = self.ax.bbox.get_points()
            x = typst.ratio((x - x0) / (x1 - x0))
            y = typst.ratio((y1 - y) / (y1 - y0))
            return (x, y)
        elif isinstance(transform, matplotlib.transforms.BlendedAffine2D):
            if transform._x == self.ax.transAxes:
                x = typst.ratio(x)
            elif isinstance(transform._x, matplotlib.transforms.IdentityTransform):
                x0, x1 = self.ax.bbox.get_points()[:, 0]
                x = typst.ratio((x - x0) / (x1 - x0))
            if transform._y == self.ax.transAxes:
                y = typst.ratio(1 - y)
            elif isinstance(transform._y, matplotlib.transforms.IdentityTransform):
                y0, y1 = self.ax.bbox.get_points()[:, 1]
                y = typst.ratio((y1 - y) / (y1 - y0))
            return (x, y)
        else:
            x, y = self.ax.transAxes.inverted().transform_point(
                transform.transform_point(point)
            )
            return typst.ratio((x, 1 - y))


class Axes(AxesBase):
    def __init__(
        self,
        ax: matplotlib.axes.Axes,
        name: str,
        prefix: str = "axes",
        standalone: bool = False,
    ):
        super().__init__(ax, name, prefix, standalone)
        self.inset_axes: list[InsetAxes] = []

        self.title = Title(self)
        self.axis = Axis(self)
        self.spines = Spines(ax)
        self.legend = None

        self.children: list[Any] = []
        self.data: dict[str, Any] = {}
        self.definitions: list[str] = []
        self.draws: list[tuple[str, float]] = []
        self.parse()

    @property
    def xlim(self) -> list[str]:
        return typst.array(self.ax.get_xlim())

    @property
    def ylim(self) -> list[str]:
        return typst.array(self.ax.get_ylim())

    def parse(self):
        for i, _child in enumerate(self.ax._children):  # type: ignore
            if isinstance(_child, matplotlib.lines.Line2D):
                child = Line2D(_child, str(i))
            elif isinstance(_child, matplotlib.collections.QuadMesh):
                child = QuadMesh(_child, str(i))
            elif isinstance(_child, matplotlib.collections.Collection):
                child = Collection(_child, str(i))
            elif isinstance(_child, matplotlib.text.Text):
                child = Text(_child, self, str(i))
            elif isinstance(_child, matplotlib.inset.InsetIndicator):
                # InsetIndicators are handled in export_insets() for now...
                continue
            else:
                print("Unknown child type", type(_child))
                continue

            self.children.append(child)

        if self.ax.legend_ is not None:
            self.legend = Legend(self.ax.legend_, self)

    def export_insets(self):
        for ix in self.inset_axes:
            self.definitions.append(ix.definition)
            self.draws.append(ix.draw)

        for i, _child in enumerate(self.ax._children):  # type: ignore
            if isinstance(_child, matplotlib.inset.InsetIndicator):
                inset_axes = [ix for ix in self.inset_axes if ix.ax == _child._inset_ax]
                if len(inset_axes) == 1:
                    child = InsetIndicator(_child, inset_axes[0])
                    self.definitions.append(child.definition)
                    self.draws.append(child.draw)
                else:
                    message = f"Found {len(inset_axes)} inset axes for inset indicator {str(i)}"
                    print(message)

    def export(self, path: pathlib.Path) -> None:
        if title := self.title.definition:
            self.definitions.append(title)
            self.draws.extend(self.title.draw)

        self.draws.append(self.patch)
        self.definitions.append(self.spines.definition)
        self.draws.append(self.spines.draw)

        self.definitions.append(self.axis.definition)
        self.draws.extend(self.axis.draw)

        for child in self.children:
            self.definitions.append(child.definition)
            self.draws.append(child.draw)
            if hasattr(child, "data"):
                self.data[child.name] = child.data

        self.export_insets()

        if self.legend is not None:
            self.definitions.append(self.legend.definition)
            self.draws.append(self.legend.draw)

        draws = [draw[0] for draw in sorted(self.draws, key=lambda x: x[1])]

        if self.data:
            filename = path.joinpath("data", f"{self.name}.json")
            with open(filename, "w") as f:
                json.dump(self.data, f, indent=4, cls=NumpyEncoder)

        function = typst.function(
            self.name,
            named=dict(xlim=self.xlim, ylim=self.ylim, dpi=self.ax.figure.dpi),
            inline=True,
        )
        s = f"#let {function} = {{"
        s += header + "\n"
        if self.data:
            load_data = f'let data = json("data/{self.name}.json")\n\n'
            s += textwrap.indent(load_data, "  ")
        s += textwrap.indent("\n\n".join(self.definitions), "  ") + "\n\n"
        s += textwrap.indent("\n".join(draws), "  ") + "\n"
        s += "}\n\n"

        if self.standalone:
            s += typst.block(self.name, self.padding, f"{self.name}()")
        return s


class ColorbarAxes(AxesBase):
    def __init__(self, ax, name, prefix="colorbar", standalone=False):
        super().__init__(ax, name, prefix=prefix, standalone=standalone)
        self.cbar = ax._colorbar
        self.spines = Spines(ax)

    @property
    def lim(self) -> list[str]:
        lim = (
            self.ax.get_ylim()
            if self.cbar.orientation == "vertical"
            else self.ax.get_xlim()
        )
        return typst.array(lim)

    @property
    def header(self) -> str:
        if self.cbar.orientation == "vertical":
            transform: str = "(0, 100% - (y * scale + shift))"
        else:
            transform: str = "(x * scale + shift, 0)"

        return textwrap.dedent(f"""\
        let scale = 1 / (lim.at(1) - lim.at(0)) * 100%
        let shift = 50% - (lim.at(0) + lim.at(1)) / 2 * scale

        let transform(point) = {{
            let (x, y) = point
            return {transform}
        }}
        """)

    @property
    def label(self):
        label = None
        if self.cbar.orientation == "vertical" and self.ax.get_ylabel():
            label = self.ax.yaxis.get_label()
        elif self.cbar.orientation == "horizontal" and self.ax.get_xlabel():
            label = self.ax.xaxis.get_label()
        if label is not None:
            return Text(label, self, "colormap", prefix="label")

    @property
    def ticks(self):
        axis = self.ax.yaxis if self.cbar.orientation == "vertical" else self.ax.xaxis
        Ticks = YTicks if self.cbar.orientation == "vertical" else XTicks

        ticks = []
        if _ticks := axis.get_major_ticks():
            params = axis.get_tick_params(which="major")
            ticks.append(Ticks(_ticks, "colormap-major-ticks", params))
        if _ticks := axis.get_minor_ticks():
            params = axis.get_tick_params(which="minor")
            ticks.append(Ticks(_ticks, "colormap-minor-ticks", params))
        return ticks

    @property
    def gradient(self) -> str:
        angle = -90 if self.cbar.orientation == "vertical" else typst.degree(0)
        return typst.function(
            "std.gradient.linear",
            pos=[f"..color.map.{self.cbar.cmap.name}"],
            named=dict(angle=typst.degree(angle)),
            inline=True,
        )

    @property
    def rect(self) -> str:
        return typst.function(
            "rect",
            named=dict(width="100%", height="100%", fill="gradient", stroke="none"),
            inline=True,
        )

    @property
    def definition(self) -> str:
        definitions: list[str] = []
        if (label := self.label) is not None:
            definitions.append(label.definition)
        for ticks in self.ticks:
            definitions.append(ticks.definition)
        definitions.append(f"let gradient = {self.gradient}")
        return "\n".join(definitions)

    @property
    def draw(self) -> str:
        draws: list[tuple[str, float]] = []
        if (label := self.label) is not None:
            draws.append(label.draw)
        for ticks in self.ticks:
            draws.append(ticks.draw)
        draws.append((typst.function("std.place", body=self.rect, inline=True), 0))
        return "\n".join([draw[0] for draw in sorted(draws, key=lambda x: x[1])])

    def export(self, path: pathlib.Path) -> str:
        function = typst.function(self.name, named=dict(lim=self.lim), inline=True)
        s = f"#let {function} = {{" + "\n"
        s += textwrap.indent(self.header, "  ") + "\n\n"
        s += textwrap.indent(self.definition, "  ") + "\n\n"
        s += textwrap.indent(self.draw, "  ") + "\n"
        s += "}\n\n"

        if self.standalone:
            s += typst.block(self.name, self.padding, f"{self.name}()")
        return s


class InsetAxes(Axes):
    def __init__(self, ix, axes, name, prefix: str = "inset"):
        self.axes = axes
        super().__init__(ix, name, prefix, standalone=False)

    def transform_bounds(self, point) -> tuple[float, float]:
        return self.axes.ax.transAxes.inverted().transform_point(
            self.axes.ax.figure.transFigure.transform_point(point)
        )

    @property
    def position(self) -> tuple[float, float]:
        """
        The coordinates (x0, y1) use the upper left corner of the inset as the
        reference point, which is more aligned with the coordinates in Typst.
        """
        p0, p1 = self.ax.get_position().get_points()
        x0, y0 = self.transform_bounds(p0)
        x1, y1 = self.transform_bounds(p1)
        return (x0, 1 - y1)

    @property
    def shape(self) -> tuple[float, float]:
        p0, p1 = self.ax.get_position().get_points()
        x0, y0 = self.transform_bounds(p0)
        x1, y1 = self.transform_bounds(p1)
        return (x1 - x0, y1 - y0)

    @property
    def definition(self) -> str:
        properties = dict(
            position=typst.ratio(self.position),
            shape=typst.ratio(self.shape),
        )
        return f"let properties-{self.name} = " + typst.dump(properties)

    @property
    def draw(self) -> tuple[str, float]:
        return (
            typst.function(
                "axes.inset",
                body=f"..properties-{self.name}, {self.name}()",
                inline=True,
            ),
            self.ax.zorder,
        )


class InsetIndicator:
    def __init__(self, indicator, inset_axes):
        self.indicator = indicator
        self.inset_axes = inset_axes

    @property
    def name(self) -> str:
        return f"indicator-{self.inset_axes.name}"

    @property
    def target(self) -> dict[str, str | tuple[float, ...]]:
        rect = self.indicator.rectangle
        x, y = rect.xy
        width, height = rect.get_width(), rect.get_height()
        return dict(
            position=(x, y + height),
            shape=(width, height),
            transform="transform",
            stroke=typst.stroke(
                rect.get_edgecolor(),
                rect.get_linewidth(),
                rect.get_linestyle(),
            ),
        )

    @property
    def source(self) -> str:
        return f"properties-{self.inset_axes.name}"

    @property
    def connectors(self) -> dict[str, str | list[str]]:
        anchors = ["bottom + left", "top + left", "bottom + right", "top + right"]
        indices = []
        for i, connector in enumerate(self.indicator.connectors):
            if connector.get_visible():
                indices.append(i)

        return dict(
            anchors=[anchors[i] for i in indices],
            stroke=typst.stroke(
                connector.get_edgecolor(),
                connector.get_linewidth(),
                connector.get_linestyle(),
            ),
        )

    @property
    def definition(self) -> str:
        return f"let {self.name} = " + typst.dump(
            dict(
                target=self.target,
                source=self.source,
                connectors=self.connectors,
            )
        )

    @property
    def draw(self) -> tuple[str, float]:
        return (
            typst.function("axes.inset-indicator", body=f"..{self.name}", inline=True),
            self.indicator.zorder,
        )
