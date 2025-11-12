import textwrap
from typing import Any, overload
from collections.abc import Mapping, Sequence

import numpy as np
import numpy.typing as npt

COLORS = {
    "k": "black",
    "w": "white",
    "r": "red",
    "b": "blue",
    "g": "green",
    (0.0, 0.0, 0.0, 1.0): "black",
    (1.0, 1.0, 1.0, 1.0): "white",
    (1.0, 0.0, 0.0, 1.0): "red",
    (0.0, 1.0, 0.0, 1.0): "green",
    (0.0, 0.0, 1.0, 1.0): "blue",
}


def make_body(elements: Sequence[str]) -> str:
    """
    Join elements into a valid Typst body

    If the list is empty, "none" is returned to get an empty body.
    If the list contains a single element, it is returned as is.
    Otherwise, the elements are wrapped in curly braces.

    Parameters
    ----------
    elements: list[str]
        The elements to join

    Returns
    -------
    str
    """
    if not elements:
        return "none"
    elif len(elements) == 1:
        return elements[0]
    else:
        return "{\n" + textwrap.indent("\n".join(elements), "  ") + "\n}"


def boolean(value: bool) -> str:
    return "true" if value else "false"


def array(elements: Sequence[str], squeeze: bool = False, inline: bool = True) -> str:
    if not elements:
        return "()"
    elif len(elements) == 1:
        return elements[0] if squeeze else f"({elements[0]},)"

    newline = "" if inline else "\n"
    separator = ", " if inline else ",\n"
    indent = "" if inline else "  "

    return (
        f"({newline}"
        + textwrap.indent(separator.join(elements), indent)
        + f"{separator if not inline else ''})"
    )


def ndarray(a: npt.NDArray[Any]) -> str:
    if np.ndim(a) == 1:
        return np.array2string(a, separator=", ").replace("[", "(").replace("]", ")")
    return "(\n" + textwrap.indent(",\n".join([ndarray(_a) for _a in a]), "  ") + ",\n)"


def dictionary(elements: Mapping[str, str], inline: bool = False) -> str:
    if not elements:
        return "(:)"

    newline = "" if inline else "\n"
    separator = ", " if inline else ",\n"
    indent = "" if inline else "  "

    return (
        f"({newline}"
        + textwrap.indent(
            separator.join([f"{k}: {v}" for k, v in elements.items()]),
            indent,
        )
        + f"{separator if not inline else ''})"
    )


@overload
def length(
    values: int | float,
    unit: str,
    *,
    scale: int | float | None = ...,
    digits: int | None = ...,
) -> str: ...


@overload
def length(
    values: Sequence[int | float],
    unit: str,
    *,
    scale: int | float | None = ...,
    digits: int | None = ...,
) -> list[str]: ...


@overload
def length(
    values: Mapping[str, int | float],
    unit: str,
    *,
    scale: int | float | None = ...,
    digits: int | None = ...,
) -> dict[str, str]: ...


def length(
    values: int | float | Sequence[int | float] | Mapping[str, int | float],
    unit: str,
    *,
    scale: int | float | None = None,
    digits: int | None = 3,
) -> str | list[str] | dict[str, str]:
    if isinstance(values, Mapping):
        return dict(
            zip(
                values.keys(),
                length(list(values.values()), unit=unit, scale=scale, digits=digits),
            )
        )
    elif isinstance(values, (int, float)):
        if scale is not None:
            values = values * scale
        if digits is not None:
            values = round(values, digits)
        return f"{values}{unit}"

    if scale is not None:
        values = [v * scale for v in values]
    if digits is not None:
        values = [round(v, digits) for v in values]
    return [f"{v}{unit}" for v in values]


@overload
def fraction(
    values: int | float,
    scale: int | float | None = ...,
    digits: int = ...,
) -> str: ...


@overload
def fraction(
    values: Sequence[int | float],
    scale: int | float | None = ...,
    digits: int = ...,
) -> list[str]: ...


@overload
def fraction(
    values: Mapping[str, int | float],
    scale: int | float | None = ...,
    digits: int = ...,
) -> dict[str, str]: ...


def fraction(
    values: int | float | Sequence[int | float] | Mapping[str, int | float],
    scale: int | float | None = None,
    digits: int = 3,
) -> str | list[str] | dict[str, str]:
    return length(values, "fr", scale=scale, digits=digits)


@overload
def ratio(
    values: int | float,
    scale: int | float = ...,
    digits: int = ...,
) -> str: ...


@overload
def ratio(
    values: Sequence[int | float],
    scale: int | float = ...,
    digits: int = ...,
) -> list[str]: ...


@overload
def ratio(
    values: Mapping[str, int | float],
    scale: int | float = ...,
    digits: int = ...,
) -> dict[str, str]: ...


def ratio(
    values: int | float | Sequence[int | float] | Mapping[str, int | float],
    scale: int | float = 100,
    digits: int = 3,
) -> str | list[str] | dict[str, str]:
    return length(values, "%", scale=scale, digits=digits)


def function(
    name: str,
    *,
    pos: Sequence[str | int | float] | None = None,
    named: Mapping[str, str | int | float] | None = None,
    body: str | None = None,
    comment: str = "",
    inline: bool = False,
) -> str:
    if pos is None:
        pos = []
    if named is None:
        named = {}

    comment = f"// {comment}\n" if comment else ""
    args = [f"{dump(p)}" for p in pos] + [f"{k}: {dump(v)}" for k, v in named.items()]
    if body is not None:
        args.append(body)
    if not args:
        return f"{comment}{name}()"

    newline = "" if inline else "\n"
    separator = ", " if inline else ",\n"
    indent = "" if inline else "  "

    return (
        f"{comment}{name}({newline}"
        + textwrap.indent(separator.join(args), indent)
        + f"{separator if not inline else ''})"
    )


def block(name: str, padding: dict[str, float], body: str | None = None):
    s = "let padding = " + dictionary(ratio(padding), inline=True) + "\n\n"

    inner = function(
        "block",
        named=dict(
            width="100% - padding.right - padding.left",
            height="100% - padding.top - padding.bottom",
            stroke="green",
        ),
        body=body,
    )

    place = function(
        "place",
        pos=["top + left"],
        named=dict(dx="padding.left", dy="padding.top"),
        body=inner,
    )

    return (
        f"#let {name}() = {{\n"
        + textwrap.indent(s, "  ")
        + textwrap.indent(place, "  ")
        + "\n}\n\n"
    )


def _color_from_str(color: str) -> str:
    if color in COLORS.values():
        return color
    elif color in COLORS:
        return COLORS[color]
    elif color.startswith("#"):
        return function("color.rgb", pos=[f'"{color}"'], inline=True)
    elif color.startswith("C"):
        return f"colors({color[1:]})"
    else:
        try:
            return function("color.luma", pos=[ratio(float(color))], inline=True)
        except ValueError:
            print(f"Unknown color '{color}', defaulting to black")
            return "black"


def _color_from_tuple(color: tuple[float, ...], simplify: bool = True) -> str:
    if simplify:
        if color in COLORS:
            return COLORS[color]
        elif len(set(color[:3])) == 1 and (len(color) == 3 or color[3] == 1.0):
            return function("color.luma", pos=[ratio(color[0])], inline=True)
    return function("color.rgb", pos=ratio(color), inline=True)


def color(
    color: str | tuple[float, ...], alpha: float | None = None, simplify: bool = True
) -> str:
    if isinstance(color, str):
        color = _color_from_str(color)
    elif isinstance(color, (tuple, list, np.ndarray)):
        color = _color_from_tuple(tuple(color), simplify=simplify)

    if alpha is None:
        return color
    return f"{color}.transparentize({ratio(1 - alpha)})"


def dash(
    offset: str | int | np.integer | float | Any,
    pattern: str | None | Sequence[float] | Any,
) -> str:
    if pattern is None:
        return '"solid"'
    elif isinstance(pattern, str):
        return pattern

    if not isinstance(pattern, Sequence):
        raise TypeError(f"Unknown pattern type '{type(pattern)}'")
    if not isinstance(offset, (str, int, np.integer, float)):
        raise TypeError(f"Unknown offset type '{type(offset)}'")

    pattern = np.array(pattern, dtype=float)
    return dict(array=length(pattern, "pt"), phase=f"{offset}pt")


def stroke(edgecolor, linewidth, linestyle):
    paint = color(edgecolor)
    thickness = length(linewidth, "pt")
    if linestyle == "solid":
        return f"{paint} + {thickness}"

    if isinstance(linestyle, (str, float)):
        _dash = f'"{linestyle}"'
    else:
        _dash = dash(*linestyle)
    return dict(paint=paint, thickness=thickness, dash=_dash)


def transform(
    scale: Sequence[float] | Sequence[str] | None = None,
    shift: Sequence[float] | Sequence[str] | None = None,
    unit: Sequence[str] | None = None,
):
    x = "x"
    y = "y"
    if scale is not None:
        x = f"x * {scale[0]}"
        y = f"y * {scale[1]}"
    if shift is not None:
        x = f"{x} + {shift[0]}"
        y = f"{y} + {shift[1]}"
    if unit is not None:
        x = f"({x}) * {unit[0]}"
        y = f"({y}) * {unit[1]}"
    transformed = f"({x}, {y})"
    body = "let (x, y) = point\n" + transformed
    return "{\n" + textwrap.indent(body, "  ") + "\n}"


def dump(obj, squeeze: bool = False):
    """
    Dump an object to a Typst string

    This function is equivalent to `json.dumps()` that turns any object into a
    valid string.

    Parameters
    ----------
    obj: any
        The object to dump
    squeeze: bool
        If True, lists and tuples are squeezed if they contain a single element

    Returns
    -------
    str
    """
    if isinstance(obj, np.ndarray):
        return ndarray(obj)
    elif isinstance(obj, (list, tuple)):
        elements = [dump(e, squeeze=squeeze) for e in obj]
        length = sum([len(e) for e in elements])
        return array(elements, squeeze=squeeze, inline=length < 80)
    elif isinstance(obj, dict):
        values = [dump(v, squeeze=squeeze) for v in obj.values()]
        length = sum([len(k) for k in obj.keys()]) + sum([len(v) for v in values])
        return dictionary(dict(zip(obj.keys(), values)), inline=length < 80)
    else:
        return str(obj)
