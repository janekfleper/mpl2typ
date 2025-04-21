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


def function(
    name: str,
    args: dict[str, str],
    comment: str = "",
    inline: bool = False,
) -> Callable[[str], str]:
    newline = "" if inline else "\n"
    separator = ", " if inline else ",\n"
    indent = "" if inline else "  "

    def wrapper(body: str):
        return (
            f"{'// ' + comment + '\n' if comment and inline else ''}"
            + f"{name}({' // ' + comment if comment and not inline else ''}{newline}"
            + textwrap.indent(
                separator.join([f"{k}: {v}" for k, v in args.items()]), indent
            )
            + separator
            + textwrap.indent(body, indent)
            + f"{newline})"
        )

    return wrapper


def compute_gutter(space: float, n: int):
    return space / (n + (n - 1) * space)


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
        dict(dx="padding.left", dy="padding.top"),
    )

    block = function(
        "block",
        dict(
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
