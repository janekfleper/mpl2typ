import numpy as np
import matplotlib.lines

from . import typst

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


class Stroke:
    def __init__(self, line: matplotlib.lines.Line2D):
        self.line = line

    @property
    def color(self) -> str:
        return f'color.rgb("{self.line.get_color()}")'

    @property
    def thickness(self) -> str:
        return f"{self.line.get_linewidth()}pt"

    @property
    def capstyle(self) -> str:
        capstyle = self.line.get_dash_capstyle()
        if capstyle == "projecting":
            capstyle = "square"  # this is the equivalent cap style in Typst
        return f'"{capstyle}"'

    @property
    def joinstyle(self) -> str:
        return f'"{self.line.get_dash_joinstyle()}"'

    @property
    def dash(self) -> str:
        offset, pattern = self.line._dash_pattern
        if pattern is None:
            return '"solid"'
        else:
            array = typst.array(typst.length(pattern, "pt"))
            phase = f"{offset}pt"
            return f"(array: {array}, phase: {phase})"

    def export(self) -> str:
        return typst.function(
            "stroke",
            named=dict(
                paint=self.color,
                thickness=self.thickness,
                cap=self.capstyle,
                join=self.joinstyle,
                dash=self.dash,
            ),
        )


class Marker:
    def __init__(self, line: matplotlib.lines.Line2D):
        self.line = line

    @property
    def size(self) -> str:
        return f"{self.line.get_markersize() / 2}pt"

    @property
    def face_color(self) -> str:
        color = self.line.get_markerfacecolor()
        if color == "k":
            color = "#000000"
        if (alpha := self.line.get_alpha()) is not None:
            color += f"{int(alpha * 255):x}"
        return f'color.rgb("{color}")'

    @property
    def edge_color(self) -> str:
        color = self.line.get_markeredgecolor()
        if color == "k":
            color = "#000000"
        if (alpha := self.line.get_alpha()) is not None:
            color += f"{int(alpha * 255):x}"
        return f'color.rgb("{color}")'

    @property
    def edge_width(self) -> str:
        return f"{self.line.get_markeredgewidth()}pt"

    @property
    def stroke(self) -> str:
        return f"{self.edge_color} + {self.edge_width}"

    def export(self) -> str:
        if self.line.get_marker() == "None":
            return "none"
        return MARKERS[self.line.get_marker()].format(
            fill=self.face_color,
            stroke=self.stroke,
        )


class Line2D:
    def __init__(self, index: int, line: matplotlib.lines.Line2D):
        self.index = index
        self.line = line
        self.stroke = Stroke(line)
        self.marker = Marker(line)

    @property
    def data(self) -> str:
        points = np.array(self.line.get_xydata())
        data = typst.array([f"({x}, {y})" for x, y in points], inline=False)
        return data + ".map(point => transform(point))"

    @property
    def definition(self) -> str:
        return (
            f"let stroke-{self.index} = {self.stroke.export()}\n\n"
            + f"let d = {self.marker.size}\n"
            + f"let marker-{self.index} = {self.marker.export()}\n\n"
            + f"let data-{self.index} = {self.data}\n"
        )

    @property
    def draw(self) -> str:
        return (
            f"draw-line(data-{self.index}, stroke: stroke-{self.index})\n"
            + f"draw-marker(data-{self.index}, marker: marker-{self.index})\n"
        )
