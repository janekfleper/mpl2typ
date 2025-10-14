import numpy as np
import matplotlib.path
import matplotlib.collections
import matplotlib.transforms
import textwrap
from abc import abstractmethod

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
    for segment, code in path.iter_segments():  # type: ignore
        if code == path.CLOSEPOLY:
            components.append("curve.close()")
            continue

        segment[1::2] *= -1  # flip the y-coordinates
        points = [
            typst.array(typst.length(list(point), " * s"), inline=True)
            for point in np.array(segment, dtype=float).reshape(-1, 2)
        ]
        if code == path.MOVETO:
            function = "curve.move"
        elif code == path.LINETO:
            function = "curve.line"
        elif code == path.CURVE3:
            function = "curve.quad"
        elif code == path.CURVE4:
            function = "curve.cubic"
        else:
            raise ValueError(f"Unknown path code: {code}")
        components.append(typst.function(function, pos=points, inline=True))

    return components


class Collection:
    def __init__(self, index: int, collection: matplotlib.collections.Collection):
        self.index = index
        self.collection = collection

    @property
    def path(self) -> list[str]:
        return [
            typst.ndarray(np.array(path.vertices, dtype=float))
            for path in self.collection.get_paths()
        ]

    @property
    def offset(self) -> list[str]:
        return [
            typst.ndarray(offset)
            for offset in np.array(self.collection.get_offsets(), dtype=float)
        ]

    @property
    def offset_transform(self) -> str:
        """
        Set up the offset transformation function

        According to the Matplotlib documentation, the offsets are applied to
        the lines/paths/patches in screen (pixel) coordinates after rendering.
        All the internal transformations of the lines/paths/patches are already
        applied before the offsets are taken into account.
        If the offset is [0, 0] and there is no offset transformation, nothing
        has to be done and the lines/paths/patches can be placed directly.
        If an offset has to be applied, we transform it to the unit points (pt)
        to replicate the Matplotlib behavior.

        Matplotlib itself is slightly inconsistent here since the DPI depends
        on the file format of the figure that is saved. For vector formats, the
        DPI is (always) 72, whereas for raster formats, the DPI can be set in
        the figure (defaults to 100). This can lead to a mismatch between the
        offsets in different file formats if the offset transformation does not
        already take the DPI into account.
        """
        axes = self.collection.axes
        if axes is None:
            raise ValueError(f"The collection {self.index} is not part of an Axes")

        offset_transform = self.collection.get_offset_transform()
        offset_matrix = np.array(offset_transform.get_matrix(), dtype=float)  # type: ignore
        offset_scale = np.diag(offset_matrix[:2, :2])
        offset_shift = offset_matrix[:2, 2]

        dpi = axes.figure.dpi
        return typst.transform(
            list(offset_scale / dpi),
            list(offset_shift / dpi),
            unit=["72pt", "72pt"],
        )

    @property
    def edgecolor(self) -> list[str]:
        return [
            typst.function("color.rgb", pos=typst.ratio(color), inline=True)
            for color in self.collection.get_edgecolor()
        ]

    @property
    def facecolor(self) -> list[str]:
        return [
            typst.function("color.rgb", pos=typst.ratio(color), inline=True)
            for color in self.collection.get_facecolor()
        ]

    @property
    def linewidth(self) -> list[str]:
        linewidth = self.collection.get_linewidth()
        if isinstance(linewidth, (float, int)):
            return [f"{linewidth}pt"]
        return [f"{lw}pt" for lw in linewidth]

    @property
    def linestyle(self) -> list[str]:
        linestyle = self.collection.get_linestyle()
        if isinstance(linestyle, (str, float)):
            return [f"{linestyle}"]
        return [typst.dash(offset, pattern) for offset, pattern in linestyle]  # type: ignore

    @property
    def stroke(self) -> str | None:
        named: dict[str, str] = {}
        if len(edgecolor := self.edgecolor) == 1:
            named["paint"] = edgecolor[0]
        if len(linewidth := self.linewidth) == 1:
            named["thickness"] = linewidth[0]
        if len(linestyle := self.linestyle) == 1:
            named["dash"] = linestyle[0]

        if not named:
            return None
        return typst.dictionary(named, inline=False)

    @property
    def data(self) -> str:
        data: dict[str, str] = {}

        if len(path := self.path) > 1:
            data["paths"] = typst.array(path, inline=False)
        if len(offset := self.offset) > 1:
            data["offsets"] = typst.array(offset, inline=False)

        strokes: dict[str, str] = {}
        if len(edgecolors := self.edgecolor) > 1:
            strokes["paint"] = typst.array(edgecolors, inline=False)
        if len(linewidths := self.linewidth) > 1:
            strokes["thickness"] = typst.array(linewidths, inline=False)
        if len(linestyles := self.linestyle) > 1:
            strokes["dash"] = typst.array(linestyles, inline=False)
        if strokes:
            data["strokes"] = typst.dictionary(strokes, inline=False)

        return typst.dictionary(data, inline=False)

    @property
    @abstractmethod
    def definition(self) -> str:
        pass

    @property
    @abstractmethod
    def draw(self) -> str:
        pass


class LineCollection(Collection):
    def __init__(self, index: int, collection: matplotlib.collections.LineCollection):
        super().__init__(index, collection)

    @property
    def definition(self):
        path = self.path
        path = path[0] if len(path) == 1 else "none"
        offset = self.offset
        offset = offset[0] if len(offset) == 1 else "none"
        stroke = self.stroke
        stroke = stroke if stroke is not None else "none"

        return (
            f"let path-{self.index} = {path}\n"
            + f"let offset-{self.index} = {offset}\n"
            + f"let offset-transform-{self.index}(point) = {self.offset_transform}\n"
            + f"let stroke-{self.index} = {stroke}\n"
            + f"let data-{self.index} = {self.data}\n"
        )

    @property
    def draw(self):
        return f"draw.line-collection(data-{self.index}, path: path-{self.index}, offset: offset-{self.index}, stroke: stroke-{self.index}, transform, offset-transform-{self.index})\n"


class PathCollection(Collection):
    def __init__(self, index: int, collection: matplotlib.collections.PathCollection):
        super().__init__(index, collection)

    @property
    def stroke(self) -> str:
        dash = self.linestyle
        if dash == '"solid"':
            return f"{self.linewidth} + {self.edgecolor}"

        named: dict[str, str] = {}
        if (edgecolor := self.edgecolor) is not None:
            named["paint"] = edgecolor
        if (linewidth := self.linewidth) is not None:
            named["thickness"] = linewidth
        if (dash := self.linestyle) is not None:
            named["dash"] = dash
        return typst.function("stroke", named=named)

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
        named: dict[str, str] = dict(size="0", scale="1pt")
        if (facecolor := self.facecolor) is not None:
            named["fill"] = facecolor
        named["stroke"] = self.stroke
        signature = typst.function(
            f"path-{self.index}",
            named=named,
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
            f"draw.path-collection(path-{self.index}, data-{self.index}, transform)\n"
        )


class QuadMesh:
    def __init__(self, index: int, collection: matplotlib.collections.QuadMesh):
        self.index = index
        self.collection = collection

    @property
    def colormap(self) -> str:
        norm = self.collection.norm
        cmap = self.collection.get_cmap()
        gradient = f"gradient.linear(..color.map.{cmap.name})"
        signature = typst.function(
            f"colormap-{self.index}",
            pos=["v"],
            named=dict(vmin=norm.vmin, vmax=norm.vmax),
            inline=True,
        )
        return (
            f"let gradient-{self.index} = {gradient}\n"
            + f"let {signature} = gradient-{self.index}.sample((v - vmin) / (vmax - vmin) * 99%)"
        )

    @property
    def vertices(self) -> str:
        return typst.ndarray(np.array(self.collection.get_coordinates(), dtype=float))

    @property
    def data(self) -> str:
        return typst.ndarray(np.array(self.collection.get_array(), dtype=float))  # type: ignore

    @property
    def definition(self) -> str:
        return (
            self.colormap
            + "\n"
            + f"let vertices-{self.index} = {self.vertices}\n"
            + f"let data-{self.index} = {self.data}\n"
        )

    @property
    def draw(self) -> str:
        return f"draw.quad-mesh(vertices-{self.index}, data-{self.index}, colormap-{self.index}, transform)\n"
