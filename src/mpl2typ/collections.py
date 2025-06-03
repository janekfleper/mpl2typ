import numpy as np
import matplotlib.path
import matplotlib.collections

import textwrap
from collections.abc import Sequence

from . import typst


def curve_components(path: matplotlib.path.Path):
    """
    Create curve components from a matplotlib path.

    Parameters
    ----------
    path : matplotlib.path.Path
        The path to convert to curve components.

    Returns
    -------
    components : list[str]

    Notes
    -----
    The y-position has to be inverted to match the Typst coordinate system.
    """
    components: list[str] = []
    for vertex, code in path.iter_segments():  # type: ignore
        if code == path.CLOSEPOLY:
            components.append("curve.close()")
            continue

        x, y = list(np.array(vertex, dtype=float))
        position = typst.array(typst.length([x, -y], " * s"), inline=True)
        if code == path.MOVETO:
            function = "curve.move"
        elif code == path.LINETO:
            function = "curve.line"
        else:
            continue
        components.append(typst.function(function, pos=[position], inline=True))

    return components


class PathCollection:
    def __init__(self, index: int, collection: matplotlib.collections.PathCollection):
        self.index = index
        self.collection = collection

    @property
    def linewidth(self) -> str:
        linewidth = self.collection.get_linewidth()
        if isinstance(linewidth, (Sequence, np.ndarray)):
            return f"{linewidth[0]}pt"
        return f"{linewidth}pt"

    @property
    def linestyle(self):
        offset, pattern = self.collection.get_linestyle()[0]  # type: ignore
        if not isinstance(offset, (str, int, np.integer, float)):
            raise TypeError(f"Unknown offset type '{type(offset)}'")  # type: ignore
        if not (isinstance(pattern, (str, Sequence)) or pattern is None):
            raise TypeError(f"Unknown pattern type '{type(pattern)}'")  # type: ignore
        pattern = list(np.array(pattern, dtype=float)) if pattern is not None else None
        return offset, pattern

    @property
    def facecolor(self) -> str:
        color = self.collection.get_facecolor()[0]
        return typst.function("color.rgb", pos=typst.ratio(color), inline=True)

    @property
    def edgecolor(self) -> str:
        color = self.collection.get_edgecolor()[0]
        return typst.function("color.rgb", pos=typst.ratio(color), inline=True)

    @property
    def stroke(self) -> str:
        offset, pattern = self.linestyle
        if pattern is None:
            return f"{self.linewidth} + {self.edgecolor}"

        dash = typst.dictionary(
            dict(
                array=typst.array(typst.length(pattern, "pt")),
                phase=f"{offset}pt",
            ),
            inline=True,
        )
        return typst.function(
            "stroke",
            named=dict(
                paint=self.edgecolor,
                thickness=self.linewidth,
                dash=dash,
            ),
        )

    @property
    def data(self):
        points: list[str] = []
        offsets = np.array(self.collection.get_offsets(), dtype=float)
        sizes = np.array(self.collection.get_sizes(), dtype=float)  # type: ignore
        for (x, y), size in zip(offsets, sizes):
            point = dict(offset=f"({x}, {y})", size=str(size))
            points.append(typst.dictionary(point, inline=True))
        return typst.array(points, inline=False)

    @property
    def definition(self):
        signature = typst.function(
            f"path-{self.index}",
            named=dict(size="0", scale="1pt", fill=self.facecolor, stroke=self.stroke),
            inline=False,
        )
        path = typst.function(
            "curve",
            pos=curve_components(self.collection.get_paths()[0]),
            named=dict(fill="fill", stroke="stroke"),
            inline=False,
        )

        s = f"let {signature} = {{\n"
        s += textwrap.indent("let s = calc.sqrt(size) * scale\n", "  ")
        s += textwrap.indent(path, "  ")
        s += "\n}\n\n"
        s += f"let data-{self.index} = {self.data}\n"
        return s

    @property
    def draw(self):
        return (
            f"draw-path-collection(path-{self.index}, data-{self.index}, transform)\n"
        )
