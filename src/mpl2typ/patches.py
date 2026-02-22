import matplotlib.patches

from pypst import Binding, Color

from .typst import color_from_mpl, Drawable, Function, Stroke


class Patch(Drawable):
    def __init__(
        self,
        patch: matplotlib.patches.Patch,
        axes,
        name: str,
        prefix: str = "patch",
    ):
        self.patch = patch
        self.axes = axes
        self._name = name
        self._prefix = prefix

    @property
    def name(self) -> str:
        return self._prefix + "-" + self._name

    @property
    def zorder(self) -> float:
        return self.patch.zorder

    @property
    def fill(self) -> Color:
        return color_from_mpl(self.patch.get_facecolor())

    @property
    def stroke(self) -> Stroke:
        return Stroke.from_mpl(
            edgecolor=self.patch.get_edgecolor(),
            linewidth=self.patch.get_linewidth(),
            linestyle=self.patch.get_linestyle(),
        )


class Rectangle(Patch):
    @property
    def points(self) -> tuple[tuple[float, float], tuple[float, float]]:
        x, y = self.patch.get_xy()
        width, height = self.patch.get_width(), self.patch.get_height()
        return (x, y + height), (x + width, y)

    @property
    def definition(self) -> Binding:
        points = self.points
        return Binding(
            name=f"{self.name}",
            value=dict(
                p0=points[0],
                p1=points[1],
                fill=self.fill,
                stroke=self.stroke,
                transform="transform",
            ),
        )

    @property
    def execution(self) -> Function:
        return Function(name="draw.rectangle", body=f"..{self.name}")
