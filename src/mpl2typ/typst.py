import textwrap
from typing import Callable


def make_body(elements: list[str]) -> str:
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


def array(elements: list[str], squeeze: bool = False) -> str:
    if len(elements) == 1:
        return elements[0] if squeeze else f"({elements[0]},)"
    return f"({', '.join(elements)})"


def dictionary(elements: dict[str, str], inline: bool = False) -> str:
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


def function(
    name: str,
    *,
    pos: list[str] | tuple[str, ...] | None = None,
    named: dict[str, str] | None = None,
    comment: str = "",
    inline: bool = False,
) -> Callable[[str], str]:
    if pos is None:
        pos = []
    if named is None:
        named = {}
    args = list(pos) + [f"{k}: {v}" for k, v in named.items()]

    newline = "" if inline else "\n"
    separator = ", " if inline else ",\n"
    indent = "" if inline else "  "

    def wrapper(body: str):
        return (
            f"{'// ' + comment + '\n' if comment and inline else ''}"
            + f"{name}({' // ' + comment if comment and not inline else ''}{newline}"
            + textwrap.indent(separator.join(args), indent)
            + separator
            + textwrap.indent(body, indent)
            + f"{newline})"
        )

    return wrapper


def block(name: str, padding: dict[str, float]):
    s = ""
    s += "let padding = (\n"
    s += f"  left: {round(padding['left'] * 100, 3)}%,\n"
    s += f"  right: {round(padding['right'] * 100, 3)}%,\n"
    s += f"  top: {round(padding['top'] * 100, 3)}%,\n"
    s += f"  bottom: {round(padding['bottom'] * 100, 3)}%,\n"
    s += ")\n\n"

    place = function(
        "place",
        named=dict(dx="padding.left", dy="padding.top"),
    )

    block = function(
        "block",
        named=dict(
            width="100% - padding.right - padding.left",
            height="100% - padding.top - padding.bottom",
            stroke="green",
        ),
    )

    def wrapper(body: str):
        return (
            f"#let {name}() = {{\n"
            + textwrap.indent(s, "  ")
            + textwrap.indent(place(block(body)), "  ")
            + "\n}\n\n"
        )

    return wrapper
