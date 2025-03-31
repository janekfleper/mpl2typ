# https://matplotlib.org/stable/gallery/lines_bars_and_markers/marker_reference.html
MARKERS = {
    ".": "circle(\n  radius: d / 2,\n  fill: {fill},\n  stroke: {stroke}\n)",
    "o": "circle(\n  radius: d,\n  fill: {fill},\n  stroke: {stroke}\n)",
    "v": "polygon(\n  (-d, -d), (0pt, d), (d, -d),\n  fill: {fill},\n  stroke: {stroke}\n)",
    "^": "polygon(\n  (0pt, -d), (-d, d), (d, d),\n  fill: {fill},\n  stroke: {stroke}\n)",
    "<": "polygon(\n  (d, -d), (-d, 0pt), (d, d),\n  fill: {fill},\n  stroke: {stroke}\n)",
    ">": "polygon(\n  (-d, -d), (-d, d), (d, 0pt),\n  fill: {fill},\n  stroke: {stroke}\n)",
    "8": "polygon(\n  (-d/2, -d), (-d, -d/2), (-d, d/2), (-d/2, d), (d/2, d), (d, d/2), (d, -d/2), (d/2, -d),\n  fill: {fill},\n  stroke: {stroke}\n)",
}


def get_stroke(line):
    alpha = line.get_alpha()
    color = line.get_color()
    if alpha is not None:
        color += f"{int(alpha * 255):x}"
    color = f'color.rgb("{color}")'

    capstyle = line.get_dash_capstyle()
    if capstyle == "projecting":
        capstyle = "square"  # this is the equivalent cap style in Typst
    joinstyle = line.get_dash_joinstyle()

    offset, pattern = line._unscaled_dash_pattern
    if pattern is None:
        dash = '"solid"'
    else:
        array = ", ".join([f"{step} * thickness" for step in pattern])
        phase = f"{offset} * thickness"
        dash = f"(array: ({array}), phase: {phase})"

    args = (
        f"paint: {color}",
        "thickness: thickness",
        f'cap: "{capstyle}"',
        f'join: "{joinstyle}"',
        f"dash: {dash}",
    )

    return (
        line.get_linewidth(),
        f"stroke(\n  {',\n  '.join(args)},\n)",
    )


def get_marker(line):
    alpha = line.get_alpha()
    edgecolor = line.get_markeredgecolor()
    if edgecolor == "k":
        edgecolor = "#000000"
    facecolor = line.get_markerfacecolor()
    if facecolor == "k":
        facecolor = "#000000"
    if alpha is not None:
        edgecolor += f"{int(alpha * 255):x}"
        facecolor += f"{int(alpha * 255):x}"
    edgewidth = line.get_markeredgewidth()

    stroke = f'color.rgb("{edgecolor}") + {edgewidth}pt'
    return (
        line.get_markersize() / 2,
        MARKERS[line.get_marker()].format(
            fill=f'color.rgb("{facecolor}")',
            stroke=stroke,
        ),
    )
