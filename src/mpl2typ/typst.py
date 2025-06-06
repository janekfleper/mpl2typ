import textwrap
from typing import Any, overload
from collections.abc import Mapping, Sequence

import numpy as np
import numpy.typing as npt

COLORS = {"k": "black"}


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
    newline = "" if inline else "\n"
    separator = ", " if inline else ",\n"
    indent = "" if inline else "  "

    if len(elements) == 1:
        return elements[0] if squeeze else f"({elements[0]},)"
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
    args = [f"{p}" for p in pos] + [f"{k}: {v}" for k, v in named.items()]
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
        named=dict(dx="padding.left", dy="padding.top"),
        body=inner,
    )

    return (
        f"#let {name}() = {{\n"
        + textwrap.indent(s, "  ")
        + textwrap.indent(place, "  ")
        + "\n}\n\n"
    )


def color(color: str, alpha: float | None = None) -> str:
    try:
        color = f"color.luma({round(float(color) * 100, 3)}%)"
    except ValueError:
        if color in COLORS:
            color = COLORS[color]
        elif color.startswith("#"):
            color = f'color.rgb("{color}")'

    if alpha is None:
        return color
    return f"{color}.transparentize({round((1 - alpha) * 100, 3)}%)"


def dash(pattern: str | None | Sequence[float], offset: float) -> str:
    if pattern is None:
        return '"solid"'
    elif isinstance(pattern, str):
        return pattern

    pattern = list(np.array(pattern, dtype=float))
    return dictionary(
        dict(array=array(length(pattern, "pt")), phase=f"{offset}pt"),
        inline=True,
    )
