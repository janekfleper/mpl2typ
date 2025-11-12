import matplotlib.text
import matplotlib.axes
import matplotlib.transforms

from . import typst


class Text:
    def __init__(
        self,
        name: str,
        text: matplotlib.text.Text,
        axes: "typst.axes.Axes",
        prefix: str = "text",
    ):
        self.name = name
        self.text = text
        self.axes = axes
        self.prefix = prefix

    @property
    def position(self) -> str:
        return self.axes.transform_point(
            self.text.get_position(),
            self.text.get_transform(),
        )

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
        return f"let {self.prefix}-{self.name} = {typst.dump(dict(position=self.position, body=self.inner(text)))}"

    @property
    def draw(self) -> tuple[str, float]:
        return (
            typst.function(
                "draw.text",
                body=f"..{self.prefix}-{self.name}",
                inline=True,
            ),
            self.text.zorder,
        )

    def export(self) -> str:
        return (
            f"let {self.prefix}-{self.name} = " + self.definition + "\n" + self.draw[0]
        )
