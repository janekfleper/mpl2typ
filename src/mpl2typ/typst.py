import textwrap


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


def fractions(values: list[int | float]) -> str:
    return [f"{v}fr" for v in values]


def ratios(values: list[int | float], digits: int = 3) -> str:
    return [f"{round(v * 100, digits)}%" for v in values]


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
    body: str | None = None,
    comment: str = "",
    inline: bool = False,
) -> str:
    if pos is None:
        pos = []
    if named is None:
        named = {}

    args = list(pos) + [f"{k}: {v}" for k, v in named.items()]
    if body is not None:
        args.append(body)
    if not args:
        return f"{'// ' + comment + '\n' if comment else ''}" + f"{name}()"

    newline = "" if inline else "\n"
    separator = ", " if inline else ",\n"
    indent = "" if inline else "  "

    return (
        f"{'// ' + comment + '\n' if comment and inline else ''}"
        + f"{name}({' // ' + comment if comment and not inline else ''}{newline}"
        + textwrap.indent(separator.join(args), indent)
        + f"{separator})"
    )


def block(name: str, padding: dict[str, float], body: str | None = None):
    padding = {k: f"{round(v * 100, 3)}%" for k, v in padding.items()}
    s = "let padding = " + dictionary(padding, inline=True) + "\n\n"

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
