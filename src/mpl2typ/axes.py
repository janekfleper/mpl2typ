import json
import pathlib
import textwrap
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeVar, Generic, Any

import numpy as np
import imageio.v3 as imageio

import matplotlib
import matplotlib.axes
import matplotlib.axis
import matplotlib.text
import matplotlib.inset
import matplotlib.lines
import matplotlib.patches
import matplotlib.collections

from pypst import Binding, Degree, Functional, Length, Ratio, Renderable

from .lines import Line2D
from .patches import Rectangle
from .collections import Collection, QuadMesh
from .legend import Legend
from .text import Text, relativ_fontsize
from .typst import (
    color_from_mpl,
    Drawable,
    DrawableCollection,
    Function,
    PlaceBlock,
    Stroke,
)


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


@dataclass
class AxesTitles(DrawableCollection):
    center: Text | None = None
    left: Text | None = None
    right: Text | None = None

    @classmethod
    def from_axes(cls, axes: "Axes"):
        ax = axes.ax
        center = (
            Text(
                text=ax.title,
                axes=axes,
                name="center",
                prefix="title",
            )
            if ax.get_title(loc="center")
            else None
        )
        left = (
            Text(
                text=ax._left_title,  # type: ignore
                axes=axes,
                name="left",
                prefix="title",
            )
            if ax.get_title(loc="left")
            else None
        )
        right = (
            Text(
                text=ax._right_title,  # type: ignore
                axes=axes,
                name="right",
                prefix="title",
            )
            if ax.get_title(loc="right")
            else None
        )
        return cls(center=center, left=left, right=right)

    @property
    def children(self) -> list[Drawable]:
        return [
            child for child in [self.center, self.left, self.right] if child is not None
        ]


class AxesTicks(ABC, Drawable, Generic[TickParams]):
    def __init__(
        self,
        ticks: Sequence[matplotlib.axis.Tick],
        name: str,
    ):
        self._name = name
        self.ticks = ticks
        self.params: TickParams

    @property
    def name(self) -> str:
        return self._name

    @property
    def zorder(self) -> float:
        return self.ticks[0].tick1line.zorder

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
        stroke = Stroke.from_mpl(line.get_color(), line.get_markeredgewidth())
        return dict(
            direction=f'"{tick.get_tickdir()}"',
            line=dict(
                length=Length(line.get_markersize(), "pt"),
                angle=self.tick_angle,
                stroke=stroke,
            ),
        )

    @property
    def grid_stroke(self) -> Stroke:
        line = self.ticks[0].gridline
        return Stroke.from_line(line)

    @property
    def label_style(self) -> dict[str, str | dict[str, str]]:
        tick = self.ticks[0]
        text = self.ticks[0].label1
        return dict(
            pad=Length(tick.get_pad(), "pt"),
            rotation=Degree(-text.get_rotation()),
            text=dict(
                size=relativ_fontsize(float(text.get_fontsize())),
                fill=color_from_mpl(text.get_color(), text.get_alpha()),
            ),
        )

    @property
    def definition(self) -> Binding:
        items = {
            "locs": self.locs,
            "labels": self.labels,
            "tick-style": self.tick_style,
            "label-style": self.label_style,
        }
        if self.params.gridOn:
            items["grid-style"] = dict(stroke=self.grid_stroke)
        return Binding(name=self.name, value=items)

    @property
    def execution(self) -> tuple[Function, ...]:
        named = {
            "show-ticks": self.tick_positions,
            "show-labels": self.label_positions,
        }

        body = f"..{self.name}, transform"
        s: list[Function] = []
        if self.params.gridOn:
            s.append(Function(self.grid_function, body=body))
        s.append(Function(self.draw_function, kwargs=named, body=body))
        return tuple(s)


class AxesXTicks(AxesTicks[XTickParams]):
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
    def tick_angle(self) -> Degree:
        return Degree(90)

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


class AxesYTicks(AxesTicks[YTickParams]):
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
    def tick_angle(self) -> Degree:
        return Degree(0)

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


class Axis(DrawableCollection):
    def __init__(self, axes: "Axes"):
        self.axes = axes

    @property
    def ax(self) -> matplotlib.axes.Axes:
        return self.axes.ax

    @property
    def xlabel(self):
        if self.axes.ax.get_xlabel():
            return Text(
                text=self.ax.xaxis.get_label(),
                axes=self.axes,
                name="xaxis",
                prefix="label",
            )

    @property
    def ylabel(self):
        if self.axes.ax.get_ylabel():
            return Text(
                text=self.ax.yaxis.get_label(),
                axes=self.axes,
                name="yaxis",
                prefix="label",
            )

    @property
    def xoffset(self):
        xaxis_offset_text = self.ax.xaxis.get_offset_text()
        if xaxis_offset_text.get_text():
            return Text(
                text=xaxis_offset_text,
                axes=self.axes,
                name="xaxis",
                prefix="offset-label",
            )

    @property
    def yoffset(self):
        yaxis_offset_text = self.ax.yaxis.get_offset_text()
        if yaxis_offset_text.get_text():
            return Text(
                text=yaxis_offset_text,
                axes=self.axes,
                name="yaxis",
                prefix="offset-label",
            )

    @property
    def xticks(self) -> list[AxesXTicks]:
        xticks: list[AxesXTicks] = []
        if ticks := self.ax.xaxis.get_major_ticks():
            params = self.ax.xaxis.get_tick_params(which="major")
            xticks.append(AxesXTicks(ticks, "xaxis-major-ticks", params))
        if ticks := self.ax.xaxis.get_minor_ticks():
            params = self.ax.xaxis.get_tick_params(which="minor")
            xticks.append(AxesXTicks(ticks, "xaxis-minor-ticks", params))
        return xticks

    @property
    def yticks(self) -> list[AxesYTicks]:
        yticks: list[AxesYTicks] = []
        if ticks := self.ax.yaxis.get_major_ticks():
            params = self.ax.yaxis.get_tick_params(which="major")
            yticks.append(AxesYTicks(ticks, "yaxis-major-ticks", params))
        if ticks := self.ax.yaxis.get_minor_ticks():
            params = self.ax.yaxis.get_tick_params(which="minor")
            yticks.append(AxesYTicks(ticks, "yaxis-minor-ticks", params))
        return yticks

    @property
    def children(self) -> list[Drawable]:
        children: list[Drawable] = []
        if self.xlabel is not None:
            children.append(self.xlabel)
        if self.ylabel is not None:
            children.append(self.ylabel)
        if self.xoffset is not None:
            children.append(self.xoffset)
        if self.yoffset is not None:
            children.append(self.yoffset)
        children.extend(self.xticks)
        children.extend(self.yticks)
        return children


class AxesSpines(Drawable):
    def __init__(self, ax):
        self.spines = ax.spines
        self.transform = ax.transLimits

    @property
    def name(self) -> str:
        return "spines"

    @property
    def zorder(self) -> float:
        return self.spines.left.zorder

    def get_bounds(self, spine) -> str | Ratio:
        points = self.transform.transform_path(spine.get_path()).vertices
        if isinstance(spine.axis, matplotlib.axis.YAxis):
            return Ratio(1 - points[:, 1])
        elif isinstance(spine.axis, matplotlib.axis.XAxis):
            return Ratio(points[:, 0])
        else:
            raise TypeError(f"Unknown axis type {type(spine.axis)}")

    @staticmethod
    def get_stroke(spine) -> Stroke:
        return Stroke.from_mpl(
            edgecolor=spine.get_edgecolor(),
            linewidth=spine.get_linewidth(),
            linestyle=spine.get_linestyle(),
        )

    @property
    def definition(self) -> Binding:
        spines = {}
        for key in self.spines:
            spine = self.spines[key]
            if type(spine) is matplotlib.spines.Spine and spine.get_visible():
                spines[key] = dict(
                    bounds=self.get_bounds(spine), stroke=self.get_stroke(spine)
                )
        return Binding(name=self.name, value=spines)

    @property
    def execution(self) -> Function:
        return Function(name="axes.spines", body="spines")


@dataclass
class AxesPatch(Drawable):
    ax: matplotlib.axes.Axes

    @property
    def name(self) -> str:
        return "patch"

    @property
    def zorder(self) -> float:
        return self.ax.patch.zorder

    @property
    def definition(self) -> None:
        return None

    @property
    def execution(self) -> Function:
        rect = Function(
            name="rect",
            kwargs=dict(
                width="100%",
                height="100%",
                fill=color_from_mpl(
                    color=self.ax.get_facecolor(),
                    alpha=self.ax.get_alpha(),
                ),
            ),
        )
        return Function(name="std.place", body=rect)


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
        self.patch = AxesPatch(ax)

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
    def cell(self):
        sps = self.ax.get_subplotspec()
        if sps is None:
            raise ValueError("Axes is not part of a grid")
        x = sps.colspan.start
        y = sps.rowspan.start
        colspan = sps.colspan.stop - x
        rowspan = sps.rowspan.stop - y
        return dict(position=(x, y), shape=(colspan, rowspan))

    def transform_point(
        self,
        point,
        transform,
    ) -> str | Renderable | tuple[str | Renderable, str | Renderable]:
        """
        Transform a point from any coordinates to relative axes coordinates.

        In Typst, the relative axes coordinates range from 0% to 100% in both
        directions, although the y-axis is inverted compared to matplotlib.
        """
        x, y = point
        if transform == self.ax.transData:
            return Function(name="transform", args=[(x, y)])
        elif transform == self.ax.transAxes:
            return Ratio((x, 1 - y))
        elif isinstance(transform, matplotlib.transforms.IdentityTransform):
            (x0, y0), (x1, y1) = self.ax.bbox.get_points()
            x = Ratio((x - x0) / (x1 - x0))
            y = Ratio((y1 - y) / (y1 - y0))
            return (x, y)
        elif isinstance(transform, matplotlib.transforms.BlendedAffine2D):
            if transform._x == self.ax.transAxes:
                x = Ratio(x)
            elif isinstance(transform._x, matplotlib.transforms.IdentityTransform):
                x0, x1 = self.ax.bbox.get_points()[:, 0]
                x = Ratio((x - x0) / (x1 - x0))
            if transform._y == self.ax.transAxes:
                y = Ratio(1 - y)
            elif isinstance(transform._y, matplotlib.transforms.IdentityTransform):
                y0, y1 = self.ax.bbox.get_points()[:, 1]
                y = Ratio((y1 - y) / (y1 - y0))
            return (x, y)
        else:
            x, y = self.ax.transAxes.inverted().transform_point(
                transform.transform_point(point)
            )
            return Ratio((x, 1 - y))


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

        self.titles = AxesTitles.from_axes(self)
        self.axis = Axis(self)
        self.spines = AxesSpines(ax)
        self.legend = None

        self.children: list[Any] = []
        self.data: dict[str, Any] = {}
        self.definitions: list[Binding] = []
        self.executions: list[tuple[Function, float]] = []
        self.parse()

    @property
    def xlim(self) -> tuple[float, float]:
        return tuple(self.ax.get_xlim())

    @property
    def ylim(self) -> tuple[float, float]:
        return tuple(self.ax.get_ylim())

    def parse(self):
        for i, child in enumerate(self.ax._children):  # type: ignore
            if isinstance(child, matplotlib.lines.Line2D):
                Child = Line2D
            elif isinstance(child, matplotlib.collections.QuadMesh):
                Child = QuadMesh
            elif isinstance(child, matplotlib.collections.Collection):
                Child = Collection
            elif isinstance(child, matplotlib.text.Text):
                Child = Text
            elif isinstance(child, matplotlib.patches.Rectangle):
                Child = Rectangle
            elif isinstance(child, matplotlib.inset.InsetIndicator):
                # InsetIndicators are handled in export_insets() for now...
                continue
            else:
                print("Unknown child type", type(child))
                continue

            self.children.append(Child(child, self, name=str(i)))

        if self.ax.legend_ is not None:
            self.legend = Legend(self.ax.legend_, self)

    def export_insets(self):
        for ix in self.inset_axes:
            self.definitions.append(ix.definition)
            self.executions.append((ix.execution, ix.zorder))

        for i, _child in enumerate(self.ax._children):  # type: ignore
            if isinstance(_child, matplotlib.inset.InsetIndicator):
                inset_axes = [ix for ix in self.inset_axes if ix.ax == _child._inset_ax]
                if len(inset_axes) == 1:
                    child = InsetIndicator(_child, inset_axes[0])
                    self.definitions.append(child.definition)
                    self.executions.append((child.execution, child.zorder))
                else:
                    message = f"Found {len(inset_axes)} inset axes for inset indicator {str(i)}"
                    print(message)

    def render(self, path: pathlib.Path) -> str:
        for child in self.titles.children:
            self.definitions.append(child.definition)
            self.executions.append((child.execution, child.zorder))

        self.definitions.append(self.patch.definition)
        self.executions.append((self.patch.execution, self.patch.zorder))
        self.definitions.append(self.spines.definition)
        self.executions.append((self.spines.execution, self.spines.zorder))

        for child in self.axis.children:
            self.definitions.append(child.definition)
            self.executions.append((child.execution, child.zorder))

        for child in self.children:
            if isinstance(child, QuadMesh) and child.rasterized:
                image = (child.collection._facecolors * 255).astype(np.uint8)
                filename = path.joinpath("data", f"{self.name}-{child.name}.png")
                imageio.imwrite(filename, image, mode="RGBA")

            self.definitions.append(child.definition)
            self.executions.append((child.execution, child.zorder))
            if hasattr(child, "data"):
                self.data[child.name] = child.data

        self.export_insets()

        if self.legend is not None:
            self.definitions.append(self.legend.definition)
            self.executions.append((self.legend.execution, self.legend.zorder))

        definitions: list[str] = []
        for definition in self.definitions:
            # print(definition)
            if isinstance(definition, tuple):
                for d in definition:
                    if d is not None:
                        definitions.append(d.render().lstrip("#"))
            elif definition is not None:
                definitions.append(definition.render().lstrip("#"))

        executions: list[str] = []
        for execution, _ in sorted(self.executions, key=lambda x: x[1]):
            if isinstance(execution, tuple):
                for e in execution:
                    if e is not None:
                        executions.append(e.render())
            elif execution is not None:
                executions.append(execution.render())

        if self.data:
            filename = path.joinpath("data", f"{self.name}.json")
            with open(filename, "w") as f:
                json.dump(self.data, f, indent=4, cls=NumpyEncoder)

        function = Function(
            name=self.name,
            kwargs=dict(xlim=self.xlim, ylim=self.ylim, dpi=self.ax.figure.dpi),
        )
        s = f"#let {function.render()} = {{"
        s += header + "\n"
        if self.data:
            load_data = f'let data = json("data/{self.name}.json")\n\n'
            s += textwrap.indent(load_data, "  ")
        s += textwrap.indent("\n\n".join(definitions), "  ") + "\n\n"
        s += textwrap.indent("\n".join(executions), "  ") + "\n"
        s += "}\n\n"

        if self.standalone:
            s += PlaceBlock(
                name=self.name,
                padding=self.padding,
                body=f"{self.name}()",
            ).render()
        return s


class ColorbarAxes(AxesBase):
    def __init__(self, ax, name, prefix="colorbar", standalone=False):
        super().__init__(ax, name, prefix=prefix, standalone=standalone)
        self.cbar = ax._colorbar
        self.spines = AxesSpines(ax)

    @property
    def lim(self) -> list[str]:
        lim = (
            self.ax.get_ylim()
            if self.cbar.orientation == "vertical"
            else self.ax.get_xlim()
        )
        return lim

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
        Ticks = AxesYTicks if self.cbar.orientation == "vertical" else AxesXTicks

        ticks = []
        if _ticks := axis.get_major_ticks():
            params = axis.get_tick_params(which="major")
            ticks.append(Ticks(_ticks, "colormap-major-ticks", params))
        if _ticks := axis.get_minor_ticks():
            params = axis.get_tick_params(which="minor")
            ticks.append(Ticks(_ticks, "colormap-minor-ticks", params))
        return ticks

    @property
    def gradient(self) -> str | Function:
        angle = -90 if self.cbar.orientation == "vertical" else typst.degree(0)
        return Function(
            name="std.gradient.linear",
            args=[f"..color.map.{self.cbar.cmap.name}"],
            kwargs=dict(angle=Degree(angle)),
        )

    @property
    def stroke(self) -> str | Stroke:
        spine = self.ax.spines.outline
        return Stroke.from_mpl(
            edgecolor=spine.get_edgecolor(),
            linewidth=spine.get_linewidth(),
            linestyle=spine.get_linestyle(),
        )

    @property
    def rect(self) -> str | Function:
        return Function(
            name="rect",
            kwargs=dict(width="100%", height="100%", fill="gradient", stroke="stroke"),
        )

    @property
    def definitions(self) -> list[Binding]:
        definitions: list[Binding] = []
        if (label := self.label) is not None:
            definitions.append(label.definition)
        for ticks in self.ticks:
            definitions.append(ticks.definition)
        definitions.append(Binding(name="gradient", value=self.gradient))
        definitions.append(Binding(name="stroke", value=self.stroke))
        return definitions

    @property
    def executions(self) -> list[tuple[Function, float]]:
        executions: list[tuple[Function, float]] = []
        if (label := self.label) is not None:
            executions.append((label.execution, label.zorder))
        for ticks in self.ticks:
            executions.append((ticks.execution, ticks.zorder))
        executions.append((Function(name="std.place", body=self.rect), 0))
        return [execution for execution in sorted(executions, key=lambda x: x[1])]

    def render(self, path: pathlib.Path) -> str:
        function = Function(name=self.name, kwargs=dict(lim=self.lim))
        s = Binding(
            name=function,
            value=Functional(
                body=(
                    self.header,
                    self.definitions,
                    self.executions,
                )
            ),
        ).render()

        if self.standalone:
            s += PlaceBlock(
                name=self.name,
                padding=self.padding,
                body=f"{self.name}()",
            ).render()
        return s


class InsetAxes(Axes):
    def __init__(self, inset_axes, parent_axes, name, prefix: str = "inset"):
        self.parent_axes = parent_axes
        super().__init__(inset_axes, name, prefix, standalone=False)

    @property
    def zorder(self) -> float:
        return self.ax.zorder

    def transform_bounds(self, point) -> tuple[float, float]:
        return self.parent_axes.ax.transAxes.inverted().transform_point(
            self.parent_axes.ax.figure.transFigure.transform_point(point)
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
    def definition(self) -> str | Binding:
        properties = dict(
            position=Ratio(self.position),
            shape=Ratio(self.shape),
        )
        return Binding(name=f"properties-{self.name}", value=properties)

    @property
    def execution(self) -> str | Function | list[Function]:
        return Function(
            name="axes.inset",
            body=f"..properties-{self.name}, {self.name}()",
        )


class InsetIndicator(Drawable):
    def __init__(self, indicator, inset_axes):
        self.indicator = indicator
        self.inset_axes = inset_axes

    @property
    def name(self) -> str:
        return f"indicator-{self.inset_axes.name}"

    @property
    def zorder(self) -> float:
        return self.indicator.zorder

    @property
    def target(self) -> dict[str, str | tuple[float, ...]]:
        rect = self.indicator.rectangle
        x, y = rect.xy
        width, height = rect.get_width(), rect.get_height()
        return dict(
            position=(x, y + height),
            shape=(width, height),
            transform="transform",
            stroke=Stroke.from_mpl(
                edgecolor=rect.get_edgecolor(),
                linewidth=rect.get_linewidth(),
                linestyle=rect.get_linestyle(),
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
            stroke=Stroke.from_mpl(
                edgecolor=connector.get_edgecolor(),
                linewidth=connector.get_linewidth(),
                linestyle=connector.get_linestyle(),
            ),
        )

    @property
    def definition(self) -> str | Binding:
        return Binding(
            name=self.name,
            value=dict(
                target=self.target,
                source=self.source,
                connectors=self.connectors,
            ),
        )

    @property
    def execution(self) -> str | Function | list[Function]:
        return Function(name="axes.inset-indicator", body=f"..{self.name}")
