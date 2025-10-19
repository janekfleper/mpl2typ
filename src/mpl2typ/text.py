import matplotlib.text
import matplotlib.axes
import matplotlib.transforms

from . import typst


class Text:
    def __init__(self, name: str, text: matplotlib.text.Text, ax: matplotlib.axes.Axes):
        self.name = name
        self.text = text
        self.ax = ax

    @property
    def position(self) -> str:
        transform = self.text.get_transform()
        if transform == self.ax.transData:
            x, y = self.text.get_position()
            return f"transform({typst.array([str(x), str(y)])})"

        x, y = self.ax.transAxes.inverted().transform_point(  # type: ignore
            transform.transform_point(self.text.get_position())  # type: ignore
        )
        dx = f"{round(x * 100, 3)}%"
        dy = f"{round((1 - y) * 100, 3)}%"
        return f"({dx}, {dy})"

    @property
    def fontsize(self) -> float:
        return float(self.text.get_fontsize())

    @property
    def color(self) -> str:
        return typst.color(str(self.text.get_color()), self.text.get_alpha())

    @property
    def alignment(self) -> str:
        horizontal = self.text.get_horizontalalignment()
        vertical = self.text.get_verticalalignment()
        if "center" in vertical:
            vertical = "horizon"
        elif vertical == "baseline":
            vertical = "bottom"

        return f"{horizontal} + {vertical}"

    def inner(self, body: str) -> str:
        rotation = self.text.get_rotation()
        if rotation:
            if self.text.get_rotation_mode() == "anchor":
                return f"rotate(-{rotation}deg, place({self.alignment}, {body}))"
            else:  # "default" or None
                return f"place({self.alignment}, rotate(-{rotation}deg, reflow: true, {body}))"
        else:
            return f"place({self.alignment}, {body})"

    @property
    def definition(self) -> str:
        kwargs = dict(size=f"{self.fontsize}pt", fill=self.color)
        if self.text.get_verticalalignment() in ["center", "bottom"]:
            kwargs["bottom-edge"] = '"descender"'

        text = typst.function(
            "text",
            named=kwargs,
            body=f"[{self.text.get_text()}]",
            inline=True,
        )
        return f"let text-{self.name} = {typst.dictionary(dict(position=self.position, body=self.inner(text)))}"

    @property
    def draw(self) -> tuple[str, float]:
        return (
            typst.function(
                "draw.text",
                body=f"..text-{self.name}",
                inline=True,
            ),
            self.text.zorder,
        )

    def export(self) -> str:
        return f"let text-{self.name} = " + self.definition + "\n" + self.draw[0]
