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
    def offsets(self):
        """
        Get the offsets in data coordinates

        According to the Matplotlib documentation, the offsets are applied to
        the lines/paths/patches in screen (pixel) coordinates after rendering.
        All the internal transformations of the lines/paths/patches are already
        applied before the offsets are taken into account.
        If the offset is [0, 0] and there is no offset transformation, nothing
        has to be done and the lines/paths/patches can be placed directly.
        If an offset has to be applied, we have to compute the offset in data
        coordinates to make it work with the transform to relative coordinates
        in Typst.

        Applying the offset transform to the offsets will return the offsets
        in units of pixels. We therefore need to use the axes transform to get
        the offsets in relative axes coordinates, and then we need the limits
        transform to get the offsets in data coordinates. Only the scales of
        the latter two (inverse) transforms are applied. Also including the
        translations would return wrong offsets.
        """
        offsets = np.array(self.collection.get_offsets(), dtype=float)
        offset_transform = self.collection.get_offset_transform()
        if isinstance(offset_transform, matplotlib.transforms.IdentityTransform):
            return offsets

        axes = self.collection.axes
        if axes is None:
            raise ValueError(f"The collection {self.index} is not part of an Axes")

        axes_transform = np.array(axes.transAxes.get_matrix(), dtype=float)  # type: ignore
        axes_scale = np.diag(axes_transform[:2, :2])
        limits_transform = np.array(axes.transLimits.get_matrix(), dtype=float)  # type: ignore
        limits_scale = np.diag(limits_transform[:2, :2])
        offsets = np.array(offset_transform.transform(offsets), dtype=float)  # type: ignore
        return offsets / axes_scale / limits_scale

    @property
    def edgecolor(self) -> str | None:
        edgecolor = self.collection.get_edgecolor()
        if len(edgecolor) == 1:
            return typst.function(
                "color.rgb",
                pos=typst.ratio(edgecolor[0]),
                inline=True,
            )
        return None

    @property
    def edgecolors(self) -> list[str] | None:
        edgecolors = self.collection.get_edgecolor()
        if len(edgecolors) <= 1:
            return None
        return [
            typst.function(
                "color.rgb",
                pos=typst.ratio(color),
                inline=True,
            )
            for color in edgecolors
        ]

    @property
    def facecolor(self) -> str | None:
        facecolor = self.collection.get_facecolor()
        if len(facecolor) == 1:
            return typst.function(
                "color.rgb",
                pos=typst.ratio(facecolor[0]),
                inline=True,
            )
        return None

    @property
    def facecolors(self) -> list[str] | None:
        facecolors = self.collection.get_facecolor()
        if len(facecolors) <= 1:
            return None
        return [
            typst.function(
                "color.rgb",
                pos=typst.ratio(color),
                inline=True,
            )
            for color in facecolors
        ]

    @property
    def linewidth(self) -> str | None:
        linewidth = self.collection.get_linewidth()
        if isinstance(linewidth, (float, int)):
            return f"{linewidth}pt"
        if len(linewidth) == 1:
            return f"{linewidth[0]}pt"
        return None

    @property
    def linewidths(self) -> list[str] | None:
        linewidths = self.collection.get_linewidth()
        if isinstance(linewidths, (float, int)) or len(linewidths) <= 1:
            return None
        return [f"{lw}pt" for lw in linewidths]

    @property
    def linestyle(self) -> str | None:
        linestyle = self.collection.get_linestyle()
        if isinstance(linestyle, (str, float)):
            return linestyle
        if len(linestyle) == 1:
            offset, pattern = linestyle[0]  # type: ignore
            return typst.dash(offset, pattern)
        return None

    @property
    def linestyles(self) -> list[str] | None:
        linestyles = self.collection.get_linestyle()
        if isinstance(linestyles, (str, float)) or len(linestyles) <= 1:
            return None
        return [typst.dash(offset, pattern) for offset, pattern in linestyles]  # type: ignore

    @property
    @abstractmethod
    def stroke(self) -> str | None:
        pass

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
    def stroke(self) -> str | None:
        named: dict[str, str] = {}
        if (edgecolor := self.edgecolor) is not None:
            named["paint"] = edgecolor
        if (linewidth := self.linewidth) is not None:
            named["thickness"] = linewidth
        if (linestyle := self.linestyle) is not None:
            named["dash"] = linestyle

        if not named:
            return None
        return typst.dictionary(
            named,
            inline=False,
        )

    @property
    def strokes(self) -> str | None:
        strokes: dict[str, str] = {}
        if (edgecolors := self.edgecolors) is not None:
            strokes["paint"] = typst.array(edgecolors, inline=False)
        if (linewidths := self.linewidths) is not None:
            strokes["thickness"] = typst.array(linewidths, inline=False)
        if (linestyles := self.linestyles) is not None:
            strokes["dash"] = typst.array(linestyles, inline=False)

        if not strokes:
            return None
        return typst.dictionary(strokes, inline=False)

    @property
    def definition(self):
        data: dict[str, str] = {}

        paths = self.collection.get_paths()
        if len(paths) == 1:
            path = f"{typst.ndarray(np.array(paths[0].vertices, dtype=float))}"
        else:
            path = "none"
            data["paths"] = typst.array(
                [typst.ndarray(np.array(path.vertices, dtype=float)) for path in paths],
                inline=False,
            )

        offsets = self.offsets
        if len(offsets) == 1:
            offset = f"{typst.ndarray(offsets[0])}"
        else:
            offset = "none"
            data["offsets"] = typst.array(
                [typst.ndarray(offset) for offset in offsets],
                inline=False,
            )

        if (strokes := self.strokes) is not None:
            data["strokes"] = strokes

        return (
            f"let path-{self.index} = {path}\n"
            + f"let offset-{self.index} = {offset}\n"
            + f"let stroke-{self.index} = {self.stroke}\n"
            + f"let data-{self.index} = {typst.dictionary(data, inline=False)}\n"
        )

    @property
    def draw(self):
        return f"draw.line-collection(data-{self.index}, path: path-{self.index}, offset: offset-{self.index}, stroke: stroke-{self.index}, transform)\n"


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
