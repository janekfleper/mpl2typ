import numpy as np
import matplotlib.lines

from . import typst

# https://matplotlib.org/stable/gallery/lines_bars_and_markers/marker_reference.html
MARKERS = {
    ".": "markers.point",
    "o": "markers.circle",
    "v": "markers.triangle-down",
    "^": "markers.triangle-up",
    "<": "markers.triangle-left",
    ">": "markers.triangle-right",
    "8": "markers.octagon",
}


class Stroke:
    def __init__(self, line: matplotlib.lines.Line2D):
        self.line = line

    @property
    def color(self) -> str:
        return typst.color(str(self.line.get_color()), self.line.get_alpha())

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
        if self.line.get_linestyle() in ["none", "None", " ", ""]:
            return "none"
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
        return typst.color(str(self.line.get_markerfacecolor()), self.line.get_alpha())

    @property
    def edge_color(self) -> str:
        return typst.color(str(self.line.get_markeredgecolor()), self.line.get_alpha())

    @property
    def edge_width(self) -> str:
        return f"{self.line.get_markeredgewidth()}pt"

    @property
    def stroke(self) -> str:
        return f"{self.edge_color} + {self.edge_width}"

    def export(self) -> str:
        marker = self.line.get_marker()
        if marker in ["none", "None", " ", ""]:
            return "none"
        if marker not in MARKERS:
            raise ValueError(f"Unknown marker '{marker}'")

        return typst.function(
            MARKERS[marker],
            pos=[self.size],
            named=dict(
                fill=self.face_color,
                stroke=self.stroke,
            ),
        )


class Line2D:
    def __init__(self, index: int, line: matplotlib.lines.Line2D):
        self.index = index
        self.line = line
        self.stroke = Stroke(line)
        self.marker = Marker(line)

    @property
    def data(self) -> str:
        points = np.array(self.line.get_path().vertices)
        return typst.array([f"({x}, {y})" for x, y in points], inline=False)

    @property
    def definition(self) -> str:
        return (
            f"let stroke-{self.index} = {self.stroke.export()}\n\n"
            + f"let marker-{self.index} = {self.marker.export()}\n\n"
            + f"let data-{self.index} = {self.data}\n"
        )

    @property
    def draw(self) -> str:
        return f"draw.line(data-{self.index}, stroke: stroke-{self.index}, marker: marker-{self.index}, transform)\n"
