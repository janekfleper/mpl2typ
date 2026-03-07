import numpy as np
import numpy.typing as npt
import matplotlib.path
import matplotlib.collections
import matplotlib.transforms

from pypst import Binding, Color, Image, Length, Ratio

from .typst import color_from_mpl, dash_from_mpl, Drawable, Function, Stroke, Transform


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
    components: list[str | Function] = []
    for segment, code in path.iter_segments():  # type: ignore
        if code == path.CLOSEPOLY:
            components.append("curve.close()")
            continue

        segment[1::2] *= -1  # flip the y-coordinates
        points = [
            Length(value=list(point), unit=" * s")
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
        components.append(Function(name=function, args=points))

    return components


class Collection:
    def __init__(
        self,
        collection: matplotlib.collections.Collection,
        axes,
        name: str,
        prefix: str = "collection",
    ):
        self.collection = collection
        self.axes = axes
        self._name = name
        self._prefix = prefix

    @property
    def name(self) -> str:
        return self._prefix + "-" + self._name

    @property
    def zorder(self) -> float:
        return self.collection.zorder

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
        return (
            "point => "
            + Transform(
                scale=list(scale),
                shift=list(shift),
                unit=[Length(1, "pt"), Length(-1, "pt")],
            ).render()
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
        return (
            "point => "
            + Transform(
                scale=list(offset_scale / dpi),
                shift=list(offset_shift / dpi),
                unit=[Length(72, "pt"), Length(-72, "pt")],
            ).render()
        )

    @property
    def fill(self) -> list[str | Function]:
        colors = [color_from_mpl(color) for color in self.collection.get_facecolor()]

        hatch = self.collection.get_hatch()
        if hatch is None:
            return colors

        color = color_from_mpl(self.collection._hatch_color)
        linewidth = Length(self.collection.get_hatch_linewidth(), "pt")
        stroke = Stroke(paint=color, thickness=linewidth)
        return [
            Function(
                name="hatch.hatch",
                kwargs=dict(pattern=hatch, stroke=stroke, fill=color),
            )
            for color in colors
        ]

    @property
    def edgecolor(self) -> list[Color]:
        return [color_from_mpl(color) for color in self.collection.get_edgecolor()]

    @property
    def linewidth(self) -> list[str | Length]:
        """
        The linewidths "inherit" the shape of the linestyles, and vice versa.
        If there are multiple linestyles but only a single linewidth, the
        properties should be returned accordingly.
        See https://stackoverflow.com/a/22240621 for the source of the loop.
        """
        linewidth = self.collection.get_linewidth()
        if isinstance(linewidth, (float, int)):
            return [Length(linewidth, "pt")]

        linewidths = [Length(lw, "pt") for lw in linewidth]
        if all(lw == linewidths[0] for lw in linewidths):
            return linewidths[:1]
        return linewidths

    @property
    def linestyle(self) -> list[str | dict[str, str]]:
        """
        If all linestyles are equal, only a single linestyle is returned. See
        the docstring of the ``linewidth`` property for the details.
        """
        linestyle = self.collection.get_linestyle()
        if isinstance(linestyle, (str, float)):
            return [f"{linestyle}"]

        linestyles = [dash_from_mpl(_linestyle) for _linestyle in linestyle]
        if all(lw == linestyles[0] for lw in linestyles):
            return linestyles[:1]
        return linestyles

    @property
    def stroke(self) -> dict[str, str] | None:
        edgecolor = self.edgecolor
        if len(edgecolor) == 1:
            edgecolor = edgecolor[0]
        linewidth = self.linewidth
        if len(linewidth) == 1:
            linewidth = linewidth[0]
        linestyle = self.linestyle
        if len(linestyle) == 1:
            linestyle = linestyle[0]
        return dict(paint=edgecolor, thickness=linewidth, dash=linestyle)

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
    def definition(self) -> tuple[Binding, ...]:
        return (
            Binding(name=f"fill-{self.name}", value=self.fill),
            Binding(name=f"stroke-{self.name}", value=self.stroke),
            Binding(name=f"transform-{self.name}", value=self.transform),
            Binding(name=f"compute-scale-{self.name}", value=self.compute_scale),
            Binding(name=f"offset-transform-{self.name}", value=self.offset_transform),
            Binding(
                name=f"{self.name}",
                value={
                    "data": f'data.at("{self.name}")',
                    "fill": f"fill-{self.name}",
                    "stroke": f"stroke-{self.name}",
                    "transform": f"transform-{self.name}",
                    "compute-scale": f"compute-scale-{self.name}",
                    "offset-transform": f"offset-transform-{self.name}",
                },
            ),
        )

    @property
    def execution(self) -> Function:
        return Function(name="draw.collection", body=f"..{self.name}")


class QuadMesh(Drawable):
    def __init__(
        self,
        collection: matplotlib.collections.QuadMesh,
        axes,
        name: str,
        prefix: str = "quad-mesh",
    ):
        self.collection = collection
        self.axes = axes
        self._name = name
        self._prefix = prefix

    @property
    def name(self) -> str:
        return self._prefix + "-" + self._name

    @property
    def zorder(self) -> float:
        return self.collection.zorder

    @property
    def rasterized(self) -> bool:
        return self.collection.get_rasterized()

    @property
    def gradient_function(self) -> Function:
        cmap = self.collection.get_cmap()
        return Function(name="gradient.linear", body=f"..color.map.{cmap.name}")

    @property
    def colormap_signature(self) -> Function:
        norm = self.collection.norm
        return Function(
            name=f"colormap-{self.name}",
            args=["v"],
            kwargs=dict(vmin=norm.vmin, vmax=norm.vmax),
        )

    @property
    def colormap_function(self) -> Function:
        return Function(
            name=f"gradient-{self.name}.sample",
            body="(v - vmin) / (vmax - vmin) * 100%",
        )

    @property
    def colormap(self) -> Binding:
        return Binding(name=self.colormap_signature, value=self.colormap_function)

    @property
    def vertices(self) -> npt.NDArray[np.float64]:
        return np.array(self.collection.get_coordinates(), dtype=float)

    @property
    def values(self) -> npt.NDArray[np.float64]:
        return np.array(self.collection.get_array(), dtype=float)

    @property
    def data(self) -> dict[str, npt.NDArray[np.float64]]:
        if self.rasterized:
            return dict()

        return {
            "vertices": self.vertices,
            "values": self.values,
        }

    @property
    def definition(self) -> Binding | tuple[Binding, ...]:
        if self.rasterized:
            return Binding(
                name=self.name,
                value=Image(
                    path=f"data/{self.axes.name}-{self.name}.png",
                    width=Ratio(1.0),
                    height=Ratio(1.0),
                )
                .render()
                .lstrip("#"),
            )

        return (
            Binding(name=f"gradient-{self.name}", value=self.gradient_function),
            Binding(name=self.colormap_signature, value=self.colormap_function),
            Binding(
                name=self.name,
                value=dict(
                    data=f'data.at("{self.name}")',
                    colormap=f"colormap-{self.name}",
                    transform="transform",
                ),
            ),
        )

    @property
    def execution(self) -> Function:
        if self.rasterized:
            return Function(
                name="std.place",
                args=["top + left"],
                body=self.name,
            )

        return Function(
            name="draw.quad-mesh",
            body=f"..{self.name}",
        )
