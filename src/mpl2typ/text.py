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
    def alignment(self) -> str:
        horizontal = self.text.get_horizontalalignment()
        vertical = self.text.get_verticalalignment()
        if "center" in vertical:
            vertical = "horizon"
        elif vertical == "baseline":
            vertical = "bottom"

        return f"{horizontal} + {vertical}"

    def export(self) -> str:
        """Exports the Text object to a Typst `place` command string."""
        x, y = self.position
        dx = f"{(x + self.offset[0]) * 100}%"
        dy = f"{(1 - y - self.offset[1]) * 100}%"
        body = self.text.get_text()
        color = self.text.get_color()
        fontsize = self.text.get_fontsize()

        outer = function(
            "place",
            dict(dx=dx, dy=dy),
        )

        inner = f"place({self.alignment}, {self.name})"
        s = f"let {self.name} = text(size: {fontsize}pt, fill: {color}, {body})"
        s += f"\n{outer(inner)}"
        return s
