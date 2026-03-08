from abc import abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt
import matplotlib.lines
from matplotlib.colors import get_named_colors_mapping

from pypst import (
    Binding,
    Block,
    Color,
    ColorPredefined,
    ColorRGB,
    ColorLuma,
    Dash,
    Functional,
    Place,
    Length,
    Quantity,
    Ratio,
    Renderable,
    Stroke as PypstStroke,
)
from pypst.color import PREDEFINED_COLORS
from pypst.utils import render, render_fenced

MPL_COLORS: dict[str, str | tuple[float, ...]] = get_named_colors_mapping()


def color_from_mpl(
    color: str | tuple[float, ...] | npt.NDArray[np.float64],
    alpha: int | float | None = None,
    simplify: bool = True,
) -> ColorPredefined | ColorRGB | ColorLuma:
    """
    Create a Typst color from a matplotlib color string or tuple.

    Args:
        color: A color string. Can be a matplotlib alias, a hex string,
            a float string, or a tuple of RGB/RGBA values in [0, 1].
        alpha: The alpha component.
        simplify: Simplify the color expression.

    Examples:
        >>> color_from_mpl("k")
        ColorPredefined("black")
        >>> color_from_mpl("red")
        ColorRGB(red=Ratio(1.0), green=Ratio(0.0), blue=Ratio(0.0), alpha=None)
        >>> color_from_mpl("#ff0000", alpha=0.9)
        ColorRGB(hex="#ff0000", alpha=Ratio(0.9))
        >>> color_from_mpl("0.5")
        ColorLuma(lightness=Ratio(0.5), alpha=None)
        >>> color_from_mpl((0.1, 0.1, 0.1), alpha=0.9, simplify=True)
        ColorLuma(lightness=Ratio(0.1), alpha=Ratio(0.9))
        >>> color_from_mpl((0.5, 0.6, 0.7, 0.8))
        ColorRGB(red=Ratio(0.5), green=Ratio(0.6), blue=Ratio(0.7), alpha=Ratio(0.8))
    """
    if isinstance(color, np.ndarray):
        color = tuple(color)

    if isinstance(color, str) and color in MPL_COLORS.keys():
        color = MPL_COLORS[color]

    if isinstance(color, str):
        if alpha is not None and isinstance(alpha, float):
            alpha: Ratio = Ratio(alpha)

        if color in PREDEFINED_COLORS:
            return ColorPredefined(color=color, alpha=alpha)
        elif color.startswith("#"):
            return ColorRGB(hex=f'"{color}"', alpha=alpha)
        else:
            return ColorLuma(Ratio(float(color)), alpha=alpha)

    if len(color) == 4 and color[3] < 1.0:
        if alpha is not None:
            raise ValueError("Color tuple already contains a finite alpha value.")
        alpha: Ratio | int = (
            Ratio(color[3]) if isinstance(color[3], float) else color[3]
        )
    elif isinstance(alpha, float):
        alpha: Ratio = Ratio(alpha)

    color = color[:3]
    if len(set(color)) == 1:
        return ColorLuma(lightness=Ratio(color[0]), alpha=alpha)
    return ColorRGB(
        red=Ratio(color[0]),
        green=Ratio(color[1]),
        blue=Ratio(color[2]),
        alpha=alpha,
    )


def dash_from_mpl(linestyle: str | tuple[float, tuple[float, ...] | None]) -> Dash:
    if isinstance(linestyle, str):
        return Dash(pattern=linestyle)
    elif isinstance(linestyle, tuple):
        phase, array = linestyle
        if array is None:
            return Dash()

        phase = Length(phase, "pt")
        array: tuple[Length, ...] = tuple([Length(a, "pt") for a in array])
        return Dash(array=array, phase=phase)


@dataclass
class Stroke(PypstStroke, Renderable):
    @classmethod
    def from_mpl(
        cls,
        edgecolor: str | tuple[float, ...],
        linewidth: float,
        linestyle: str | tuple[float, tuple[float, ...]] | None = None,
    ) -> "Stroke":
        """
        Create a Typst stroke from a matplotlib edgecolor, linewidth, and linestyle.

        Args:
            edgecolor: The edgecolor of the stroke.
            linewidth: The linewidth of the stroke.
            linestyle: The linestyle of the stroke.

        Examples:
            >>> Stroke.from_mpl("black", 1)
            Stroke(paint=ColorPredefined("black"), thickness=Length(1, "pt"))
            >>> Stroke.from_mpl("#ffff00", 0.9, (2, (3, 4, 5)))
            Stroke(
                paint=ColorRGB(hex="#ffff00"),
                thickness=Length(0.9, "pt"),
                dash=Dash(
                    array=Length((3, 4, 5), "pt"),
                    phase=Length(2, "pt"),
                ),
            )
        """
        return cls(
            paint=color_from_mpl(edgecolor),
            thickness=Length(linewidth, "pt"),
            dash=dash_from_mpl(linestyle),
        )

    @classmethod
    def from_line(cls, line: matplotlib.lines.Line2D) -> "Stroke":
        """
        Create a Typst stroke from a matplotlib line.

        Args:
            line: The matplotlib.lines.Line2D object.
        """
        if line.get_linestyle() in ["none", "None", " ", ""]:
            return cls()  # rendered as "none"

        color: Color = color_from_mpl(
            color=line.get_color(),
            alpha=line.get_alpha(),
        )
        thickness: Length = Length(value=line.get_linewidth(), unit="pt")

        capstyle = line.get_dash_capstyle()
        if capstyle == "projecting":
            capstyle = "square"  # this is the equivalent cap style in Typst
        joinstyle = line.get_dash_joinstyle()

        offset, array = line._dash_pattern
        if array is None:
            dash = Dash(pattern="solid")
        else:
            array: tuple[Length, ...] = tuple([Length(a, "pt") for a in array])
            dash = Dash(array=array, phase=Length(offset, "pt"))

        return cls(
            paint=color,
            thickness=thickness,
            cap=f'"{capstyle}"',
            join=f'"{joinstyle}"',
            dash=dash,
        )


@dataclass
class NDArray(Renderable):
    """
    A numpy array.

    Args:
        array: The numpy array.

    Examples:
        >>> NDArray(np.array([1, 3, 7])).render()
        '(1, 2, 3)'
        >>> NDArray(np.array([[1, 2, 3], [4, 5, 6]])).render()
        '((1, 2, 3), (4, 5, 6))'
    """

    array: npt.NDArray[Any]

    def render(self) -> str:
        return (
            np.array2string(self.array, separator=", ")
            .replace("[", "(")
            .replace("]", ")")
        )


@dataclass
class PlaceBlock(Renderable):
    name: str
    padding: dict[str, float]
    body: str | Renderable | Functional | None = None

    def render(self) -> str:
        # return render_sequence()
        padding = Binding(
            name="padding",
            value=Ratio(self.padding),
        )

        block = Block(
            width="100% - padding.right - padding.left",
            height="100% - padding.top - padding.bottom",
            stroke="none",
            fill="none",
            body=self.body,
        )

        place = Place(
            alignment="top + left",
            dx="padding.left",
            dy="padding.top",
            body=block,
        )

        return Binding(
            name=self.name + "()",
            value=render_fenced(body=(padding, place)).lstrip("#"),
        ).render()


@dataclass
class Function(Renderable):
    name: str
    args: list[str | Renderable] | None = None
    kwargs: dict[str, str | Renderable] | None = None
    body: str | Renderable | None = None

    def render(self) -> str:
        args = []
        if self.args is not None:
            args.extend(render(arg).lstrip("#") for arg in self.args)
        if self.kwargs is not None:
            args.extend(
                [f"{k}: {render(v).lstrip('#')}" for k, v in self.kwargs.items()]
            )
        if self.body is not None:
            args.append(render(self.body).lstrip("#"))
        return f"{self.name}({', '.join(args)})"


@dataclass
class Transform(Renderable):
    scale: tuple[float, ...] | tuple[str, ...] | None = None
    shift: tuple[float, ...] | tuple[str, ...] | None = None
    unit: tuple[str | Quantity, ...] | None = None

    def render(self) -> str:
        x = "x"
        y = "y"
        if self.scale is not None:
            x = f"x * {render(self.scale[0])}"
            y = f"y * {render(self.scale[1])}"
        if self.shift is not None:
            x = f"{x} + {render(self.shift[0])}"
            y = f"{y} + {render(self.shift[1])}"
        if self.unit is not None:
            x = f"({x}) * {render(self.unit[0])}"
            y = f"({y}) * {render(self.unit[1])}"
        transformed = f"({x}, {y})"

        point = Binding(name="(x, y)", value="point")
        return render_fenced(body=(point, transformed)).lstrip("#")


class Drawable:
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def zorder(self) -> float:
        pass

    @property
    @abstractmethod
    def definition(self) -> str | Binding | tuple[Binding, ...]:
        pass

    @property
    @abstractmethod
    def execution(self) -> str | Function | tuple[Function, ...]:
        pass


class DrawableCollection:
    @property
    @abstractmethod
    def children(self) -> list[Drawable]:
        pass
