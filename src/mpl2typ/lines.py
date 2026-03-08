import numpy as np
import numpy.typing as npt
import matplotlib.lines

from pypst import Binding, Color, Length

from .typst import color_from_mpl, Drawable, Function, Stroke

# https://matplotlib.org/stable/gallery/lines_bars_and_markers/marker_reference.html
MARKERS = {
    ".": "markers.point",
    ",": "markers.pixel",
    "o": "markers.circle",
    "v": "markers.triangle-down",
    "^": "markers.triangle-up",
    "<": "markers.triangle-left",
    ">": "markers.triangle-right",
    "1": "markers.tri-down",
    "2": "markers.tri-up",
    "3": "markers.tri-left",
    "4": "markers.tri-right",
    "8": "markers.octagon",
    "s": "markers.square",
    "p": "markers.pentagon",
    "*": "markers.star",
    "h": "markers.hexagon1",
    "H": "markers.hexagon2",
    "+": "markers.plus",
    "x": "markers.x",
    "X": "markers.x-filled",
    "D": "markers.diamond",
    "d": "markers.thin-diamond",
    "|": "markers.vline",
    "_": "markers.hline",
    "P": "markers.plus-filled",
    0: "markers.tickleft",
    1: "markers.tickright",
    2: "markers.tickup",
    3: "markers.tickdown",
    4: "markers.caretleft",
    5: "markers.caretright",
    6: "markers.caretup",
    7: "markers.caretdown",
    8: "markers.caretleftbase",
    9: "markers.caretrightbase",
    10: "markers.caretupbase",
    11: "markers.caretdownbase",
}


class Marker:
    def __init__(self, line: matplotlib.lines.Line2D):
        self.line = line

    @property
    def size(self) -> Length:
        return Length(value=self.line.get_markersize() / 2, unit="pt")

    @property
    def face_color(self) -> Color:
        return color_from_mpl(
            color=self.line.get_markerfacecolor(),
            alpha=self.line.get_alpha(),
        )

    @property
    def edge_color(self) -> Color:
        return color_from_mpl(
            color=self.line.get_markeredgecolor(),
            alpha=self.line.get_alpha(),
        )

    @property
    def edge_width(self) -> Length:
        return Length(value=self.line.get_markeredgewidth(), unit="pt")

    @property
    def stroke(self) -> Stroke:
        return Stroke(
            paint=self.edge_color,
            thickness=self.edge_width,
        )

    def render(self) -> str:
        marker = self.line.get_marker()
        if marker in ["none", "None", " ", ""]:
            return "none"
        if marker not in MARKERS:
            raise ValueError(f"Unknown marker '{marker}'")

        return Function(
            name=MARKERS[marker],
            args=[self.size],
            kwargs=dict(fill=self.face_color, stroke=self.stroke),
        ).render()


class Line2D(Drawable):
    def __init__(
        self,
        line: matplotlib.lines.Line2D,
        axes,
        name: str,
        prefix: str = "line",
    ):
        self.line = line
        self.axes = axes
        self._name = name
        self._prefix = prefix
        self.stroke = Stroke.from_line(line)
        self.marker = Marker(line)

    @property
    def name(self) -> str:
        return self._prefix + "-" + self._name

    @property
    def zorder(self) -> float:
        return self.line.zorder

    @property
    def data(self) -> npt.NDArray[np.float64]:
        return np.array(self.line.get_path().vertices)

    @property
    def definition(self) -> tuple[Binding, ...]:
        return (
            Binding(name=f"stroke-{self.name}", value=self.stroke),
            Binding(name=f"marker-{self.name}", value=self.marker),
            Binding(
                name=self.name,
                value=dict(
                    data=f'data.at("{self.name}")',
                    stroke=f"stroke-{self.name}",
                    marker=f"marker-{self.name}",
                    transform="transform",
                ),
            ),
        )

    @property
    def execution(self) -> Function:
        return Function(name="draw.line", body=f"..{self.name}")
