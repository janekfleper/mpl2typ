import matplotlib as mpl

from . import typst


class Text:
    def __init__(
        self,
        name: str,
        text: mpl.text.Text,
        transform: mpl.transform.Affine2d,
    ):
        self.name = name
        self.text = text
        self.transform = transform

    @property
    def position(self) -> tuple[float, float]:
        return self.transform.transform_point(
            self.text.get_transform().transform_point(self.text.get_position())
        )

    @property
    def fontsize(self) -> float:
        return self.text.get_fontsize()

    @property
    def color(self) -> str:
        color = self.text.get_color()
        alpha = self.text.get_alpha()
        if alpha is not None:
            color += f".transparentize({round((1 - alpha) * 100, 3)}%)"
        return color

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

    def export(self) -> str:
        """Exports the Text object to a Typst `place` command string."""
        x, y = self.position
        dx = f"{round(x * 100, 3)}%"
        dy = f"{round((1 - y) * 100, 3)}%"

        outer = typst.function(
            "place",
            named=dict(dx=dx, dy=dy),
        )

        kwargs = dict(size=f"{self.fontsize}pt", fill=self.color)
        if self.text.get_verticalalignment() in ["center", "bottom"]:
            kwargs["bottom-edge"] = '"descender"'
        variable = f"let {self.name} = " + typst.function(
            "text",
            named=kwargs,
            inline=True,
        )(f"[{self.text.get_text()}]")

        return variable + "\n" + outer(self.inner(self.name))
