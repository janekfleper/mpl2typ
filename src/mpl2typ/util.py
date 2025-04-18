import textwrap
from typing import Callable


def function(
    name: str,
    args: dict[str, str],
    comment: str = "",
) -> Callable[[str], str]:
    def wrapper(body: str):
        return (
            f"{name}({' // ' + comment if comment else ''}\n"
            + textwrap.indent(",\n".join([f"{k}: {v}" for k, v in args.items()]), "  ")
            + ",\n"
            + textwrap.indent(body, "  ")
            + "\n)"
        )

    return wrapper


def compute_gutter(space: float, n: int):
    return space / (n + (n - 1) * space)


def block(name: str, padding: dict[str, float]):
    s = ""
    s += "let padding = (\n"
    s += f"  left: {padding['left'] * 100:.3g}%,\n"
    s += f"  right: {padding['right'] * 100:.3g}%,\n"
    s += f"  top: {padding['top'] * 100:.3g}%,\n"
    s += f"  bottom: {padding['bottom'] * 100:.3g}%,\n"
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
