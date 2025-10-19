import numpy as np
import matplotlib.path
import matplotlib.collections
import matplotlib.transforms

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
    def size(self) -> list[str]:
        if isinstance(self.collection, matplotlib.collections._CollectionWithSizes):  # type: ignore
            return [f"{s}" for s in self.collection.get_sizes()]
        return []

    @property
    def offset(self) -> list[str]:
        return [
            typst.ndarray(offset)
            for offset in np.array(self.collection.get_offsets(), dtype=float)
        ]

    @property
    def transform(self) -> str:
        axes = self.collection.axes
        if axes is None:
            raise ValueError(f"The collection {self.index} is not part of an Axes")

        transform = self.collection.get_transform()
        if transform == axes.transData:
            return "transform"

        matrix = np.array(transform.get_matrix(), dtype=float)
        scale = np.diag(matrix[:2, :2])
        shift = matrix[:2, 2]
        return "point => " + typst.transform(
            list(scale), list(shift), unit=["1pt", "-1pt"]
        )

    @property
    def compute_scale(self) -> str:
        axes = self.collection.axes
        if axes is None:
            raise ValueError(f"The collection {self.index} is not part of an Axes")

        transform = self.collection.get_transform()
        if transform == axes.transData:
            return "compute-scale"

        return "size => calc.sqrt(size)"

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
        if offset_transform == axes.transData:
            return "transform"

        offset_matrix = np.array(offset_transform.get_matrix(), dtype=float)  # type: ignore
        offset_scale = np.diag(offset_matrix[:2, :2])
        offset_shift = offset_matrix[:2, 2]

        dpi = axes.figure.dpi
        return "point => " + typst.transform(
            list(offset_scale / dpi),
            list(offset_shift / dpi),
            unit=["72pt", "-72pt"],
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
        if len(size := self.size) > 1:
            data["sizes"] = typst.array(size, inline=False)
        if len(offset := self.offset) > 1:
            data["offsets"] = typst.array(offset, inline=False)
        if len(facecolor := self.facecolor) > 1:
            data["fills"] = typst.array(facecolor, inline=False)

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
    def definition(self):
        path = self.path
        path = path[0] if len(path) == 1 else "none"
        size = self.size
        size = size[0] if len(size) == 1 else "none"
        offset = self.offset
        offset = offset[0] if len(offset) == 1 else "none"
        fill = self.facecolor
        fill = fill[0] if len(fill) == 1 else "none"
        stroke = self.stroke
        stroke = stroke if stroke is not None else "none"

        keys = [
            "path",
            "size",
            "offset",
            "fill",
            "stroke",
            "data",
            "transform",
            "compute-scale",
            "offset-transform",
        ]
        return (
            f"let data-{self.index} = {self.data}\n"
            + f"let path-{self.index} = {path}\n"
            + f"let size-{self.index} = {size}\n"
            + f"let offset-{self.index} = {offset}\n"
            + f"let fill-{self.index} = {fill}\n"
            + f"let stroke-{self.index} = {stroke}\n"
            + f"let transform-{self.index} = {self.transform}\n"
            + f"let compute-scale-{self.index} = {self.compute_scale}\n"
            + f"let offset-transform-{self.index} = {self.offset_transform}\n"
            + f"let collection-{self.index} = "
            + typst.dictionary({key: f"{key}-{self.index}" for key in keys})
        )

    @property
    def draw(self):
        return typst.function(
            "draw.collection", body=f"..collection-{self.index}", inline=True
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
