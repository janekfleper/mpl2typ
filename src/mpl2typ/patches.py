import matplotlib.patches

from . import typst


class Patch:
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
    def fill(self) -> str:
        return typst.color(self.patch.get_facecolor())

    @property
    def stroke(self) -> str:
        return typst.stroke(
            self.patch.get_edgecolor(),
            self.patch.get_linewidth(),
            self.patch.get_linestyle(),
        )


class Rectangle(Patch):
    @property
    def points(self) -> tuple[tuple[float, float], tuple[float, float]]:
        x, y = self.patch.get_xy()
        width, height = self.patch.get_width(), self.patch.get_height()
        return (x, y + height), (x + width, y)

    @property
    def definition(self) -> str:
        points = self.points
        return f"let {self.name} = " + typst.dump(
            dict(
                p0=typst.array(points[0]),
                p1=typst.array(points[1]),
                fill=self.fill,
                stroke=self.stroke,
                transform="transform",
            )
        )

    @property
    def draw(self) -> tuple[str, float]:
        return (
            typst.function("draw.rectangle", body=f"..{self.name}", inline=True),
            self.patch.zorder,
        )
