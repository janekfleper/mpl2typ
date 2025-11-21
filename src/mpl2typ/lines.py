import numpy as np
import numpy.typing as npt
import matplotlib.lines

from . import typst

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


class Stroke:
    def __init__(self, line: matplotlib.lines.Line2D):
        self.line = line

    @property
    def color(self) -> str:
        return typst.color(self.line.get_color(), self.line.get_alpha())

    @property
    def thickness(self) -> str:
        return typst.length(self.line.get_linewidth(), "pt")

    @property
    def capstyle(self) -> str:
        capstyle = self.line.get_dash_capstyle()
        if capstyle == "projecting":
            capstyle = "square"  # this is the equivalent cap style in Typst
        return typst.string(capstyle)

    @property
    def joinstyle(self) -> str:
        return typst.string(self.line.get_dash_joinstyle())

    @property
    def dash(self) -> str | dict[str, str]:
        offset, pattern = self.line._dash_pattern
        if pattern is None:
            return typst.string("solid")
        else:
            return dict(array=typst.length(pattern, "pt"), phase=f"{offset}pt")

    def export(self) -> str | dict[str, str]:
        if self.line.get_linestyle() in ["none", "None", " ", ""]:
            return "none"
        return dict(
            paint=self.color,
            thickness=self.thickness,
            cap=self.capstyle,
            join=self.joinstyle,
            dash=self.dash,
        )


class Marker:
    def __init__(self, line: matplotlib.lines.Line2D):
        self.line = line

    @property
    def size(self) -> str:
        return typst.length(self.line.get_markersize() / 2, "pt")

    @property
    def face_color(self) -> str:
        return typst.color(self.line.get_markerfacecolor(), self.line.get_alpha())

    @property
    def edge_color(self) -> str:
        return typst.color(self.line.get_markeredgecolor(), self.line.get_alpha())

    @property
    def edge_width(self) -> str:
        return typst.length(self.line.get_markeredgewidth(), "pt")

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
        self.stroke = Stroke(line)
        self.marker = Marker(line)

    @property
    def name(self) -> str:
        return self._prefix + "-" + self._name

    @property
    def data(self) -> npt.NDArray[np.float64]:
        return np.array(self.line.get_path().vertices)

    @property
    def definition(self) -> str:
        return (
            f"let stroke-{self.name} = {typst.dump(self.stroke.export())}\n"
            + f"let marker-{self.name} = {typst.dump(self.marker.export())}\n"
            + f"let {self.name} = "
            + typst.dictionary(
                dict(
                    data=f'data.at("{self.name}")',
                    stroke=f"stroke-{self.name}",
                    marker=f"marker-{self.name}",
                    transform="transform",
                )
            )
        )

    @property
    def draw(self) -> tuple[str, float]:
        return (
            typst.function("draw.line", body=f"..{self.name}", inline=True),
            self.line.zorder,
        )
