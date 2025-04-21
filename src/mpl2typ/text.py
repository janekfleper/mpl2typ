import matplotlib as mpl

from .util import function


class Text:
    def __init__(
        self,
        name: str,
        text: mpl.text.Text,
        offset: tuple[float, float] = (0, 0),
    ):
        self.name = name
        self.text = text
        self.offset = offset

    @property
    def position(self) -> tuple[float, float]:
        return self.text.get_position()

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
        dx = f"{round((x + self.offset[0]) * 100, 3)}%"
        dy = f"{round((1 - y - self.offset[1]) * 100, 3)}%"

        outer = function(
            "place",
            named=dict(dx=dx, dy=dy),
        )

        kwargs = dict(size=f"{self.fontsize}pt", fill=self.color)
        if self.text.get_verticalalignment() in ["center", "bottom"]:
            kwargs["bottom-edge"] = '"descender"'
        variable = f"let {self.name} = " + function(
            "text",
            named=kwargs,
            inline=True,
        )(self.text.get_text())

        return variable + "\n" + outer(self.inner(self.name))
