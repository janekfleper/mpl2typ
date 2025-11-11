import numpy as np
import numpy.typing as npt
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
    def __init__(
        self,
        name: str,
        collection: matplotlib.collections.Collection,
        prefix: str = "collection",
    ):
        self.name = name
        self.collection = collection
        self.prefix = prefix

    @property
    def path(self) -> list[npt.NDArray[np.float64]]:
        return [np.array(path.vertices) for path in self.collection.get_paths()]

    @property
    def size(self) -> npt.NDArray[np.float64]:
        if isinstance(self.collection, matplotlib.collections._CollectionWithSizes):  # type: ignore
            return self.collection.get_sizes()
        return np.array([])

    @property
    def offset(self) -> npt.NDArray[np.float64]:
        return np.array(self.collection.get_offsets())

    @property
    def transform(self) -> str:
        axes = self.collection.axes
        if axes is None:
            raise ValueError(f"The collection {self.name} is not part of an Axes")

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
            raise ValueError(f"The collection {self.name} is not part of an Axes")

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
            raise ValueError(f"The collection {self.name} is not part of an Axes")

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
    def fill(self) -> list[str]:
        colors = [
            typst.function("color.rgb", pos=typst.ratio(color), inline=True)
            for color in self.collection.get_facecolor()
        ]

        hatch = self.collection.get_hatch()
        if hatch is None:
            return colors

        color = typst.color(self.collection._hatch_color)
        linewidth = typst.length(self.collection.get_hatch_linewidth(), "pt")
        stroke = f"{color} + {linewidth}"
        return [
            typst.function(
                "hatch.hatch",
                named=dict(pattern=f'"{hatch}"', stroke=stroke, fill=color),
                inline=False,
            )
            for color in colors
        ]

    @property
    def edgecolor(self) -> list[str]:
        return [
            typst.function("color.rgb", pos=typst.ratio(color), inline=True)
            for color in self.collection.get_edgecolor()
        ]

    @property
    def linewidth(self) -> list[str]:
        """
        The linewidths "inherit" the shape of the linestyles, and vice versa.
        If there are multiple linestyles but only a single linewidth, the
        properties should be returned accordingly.
        See https://stackoverflow.com/a/22240621 for the source of the loop.
        """
        linewidth = self.collection.get_linewidth()
        if isinstance(linewidth, (float, int)):
            return [f"{linewidth}pt"]

        linewidths = [f"{lw}pt" for lw in linewidth]
        if all(lw == linewidths[0] for lw in linewidths):
            return linewidths[:1]
        return linewidths

    @property
    def linestyle(self) -> list[str]:
        """
        If all linestyles are equal, only a single linestyle is returned. See
        the docstring of the ``linewidth`` property for the details.
        """
        linestyle = self.collection.get_linestyle()
        if isinstance(linestyle, (str, float)):
            return [f"{linestyle}"]

        linestyles = [typst.dash(offset, pattern) for offset, pattern in linestyle]
        if all(lw == linestyles[0] for lw in linestyles):
            return linestyles[:1]
        return linestyles

    @property
    def stroke(self) -> dict[str, str]:
        return dict(
            paint=typst.array(self.edgecolor, squeeze=True, inline=False),
            thickness=typst.array(self.linewidth, squeeze=True, inline=False),
            dash=typst.array(self.linestyle, squeeze=True, inline=False),
        )

    @property
    def data(
        self,
    ) -> dict[str, list[npt.NDArray[np.float64]] | npt.NDArray[np.float64]]:
        return {
            "path": self.path,
            "size": self.size,
            "offset": self.offset,
        }

    @property
    def definition(self):
        return (
            f"let fill-{self.name} = {typst.array(self.fill, squeeze=True, inline=False)}\n"
            + f"let stroke-{self.name} = {typst.dictionary(self.stroke, inline=False)}\n"
            + f"let transform-{self.name} = {self.transform}\n"
            + f"let compute-scale-{self.name} = {self.compute_scale}\n"
            + f"let offset-transform-{self.name} = {self.offset_transform}\n"
            + f"let {self.prefix}-{self.name} = "
            + typst.dictionary(
                {
                    "data": f'data.at("{self.prefix}-{self.name}")',
                    "fill": f"fill-{self.name}",
                    "stroke": f"stroke-{self.name}",
                    "transform": f"transform-{self.name}",
                    "compute-scale": f"compute-scale-{self.name}",
                    "offset-transform": f"offset-transform-{self.name}",
                }
            )
        )

    @property
    def draw(self) -> tuple[str, float]:
        return (
            typst.function(
                "draw.collection", body=f"..{self.prefix}-{self.name}", inline=True
            ),
            self.collection.zorder,
        )


class QuadMesh:
    def __init__(
        self,
        name: str,
        collection: matplotlib.collections.QuadMesh,
        prefix: str = "quad-mesh",
    ):
        self.name = name
        self.collection = collection
        self.prefix = prefix

    @property
    def gradient(self) -> str:
        cmap = self.collection.get_cmap()
        return f"gradient.linear(..color.map.{cmap.name})"

    @property
    def colormap(self) -> str:
        norm = self.collection.norm
        signature = typst.function(
            f"colormap-{self.name}",
            pos=["v"],
            named=dict(vmin=norm.vmin, vmax=norm.vmax),
            inline=True,
        )
        return f"{signature} = gradient-{self.name}.sample((v - vmin) / (vmax - vmin) * 100%)"

    @property
    def vertices(self) -> npt.NDArray[np.float64]:
        return np.array(self.collection.get_coordinates(), dtype=float)

    @property
    def values(self) -> npt.NDArray[np.float64]:
        return np.array(self.collection.get_array(), dtype=float)

    @property
    def data(self) -> dict[str, npt.NDArray[np.float64]]:
        return {
            "vertices": self.vertices,
            "values": self.values,
        }

    @property
    def definition(self) -> str:
        return (
            f"let gradient-{self.name} = {self.gradient}\n"
            + f"let {self.colormap}\n"
            + f"let {self.prefix}-{self.name} = "
            + typst.dictionary(
                {
                    "data": f'data.at("{self.prefix}-{self.name}")',
                    "colormap": f"colormap-{self.name}",
                    "transform": "transform",
                }
            )
        )

    @property
    def draw(self) -> tuple[str, float]:
        return (
            typst.function(
                "draw.quad-mesh", body=f"..{self.prefix}-{self.name}", inline=True
            ),
            self.collection.zorder,
        )
