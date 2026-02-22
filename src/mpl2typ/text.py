import matplotlib
import matplotlib.text
import matplotlib.axes
import matplotlib.transforms

from pypst import (
    Binding,
    Color,
    Content,
    Degree,
    Length,
    Place,
    Renderable,
    Rotate,
    Text as PypstText,
)

from .typst import color_from_mpl, Drawable, Function


def relativ_fontsize(fontsize: float) -> str:
    delta = fontsize - matplotlib.rcParams["font.size"]
    fontsize: str = Length(1, "em").render()
    if delta > 0:
        fontsize += " + " + Length(delta, "pt").render()
    elif delta < 0:
        fontsize += " - " + Length(abs(delta), "pt").render()
    return fontsize


class Text(Drawable):
    def __init__(
        self,
        text: matplotlib.text.Text,
        axes: "mpl2typ.axes.Axes",
        name: str,
        prefix: str = "text",
    ):
        self._name = name
        self.text = text
        self.axes = axes
        self._prefix = prefix

    @property
    def name(self) -> str:
        return self._prefix + "-" + self._name

    @property
    def zorder(self) -> float:
        return self.text.zorder

    @property
    def position(self) -> str | tuple[str, str]:
        return self.axes.transform_point(
            self.text.get_position(),
            self.text.get_transform(),
        )

    @property
    def fontsize(self) -> str:
        return relativ_fontsize(float(self.text.get_fontsize()))

    @property
    def color(self) -> Color:
        return color_from_mpl(
            str(self.text.get_color()),
            self.text.get_alpha(),
        )

    @property
    def alignment(self) -> str:
        horizontal = self.text.get_horizontalalignment()
        vertical = self.text.get_verticalalignment()
        if "center" in vertical:
            vertical = "horizon"
        elif vertical == "baseline":
            vertical = "bottom"

        return f"{horizontal} + {vertical}"

    def inner(self, body: str | Renderable) -> str | Renderable:
        rotation = self.text.get_rotation()
        if rotation:
            if self.text.get_rotation_mode() == "anchor":
                return Rotate(
                    angle=Degree(-rotation),
                    body=Place(alignment=self.alignment, body=body),
                )
            else:  # "default" or None
                return Place(
                    alignment=self.alignment,
                    body=Rotate(angle=Degree(-rotation), reflow=True, body=body),
                )
        else:
            return Place(
                alignment=self.alignment,
                body=body,
            )

    @property
    def definition(self) -> Binding:
        bottom_edge = (
            '"descender"'
            if self.text.get_verticalalignment() in ["center", "bottom"]
            else None
        )

        text = PypstText(
            size=self.fontsize,
            fill=self.color,
            bottom_edge=bottom_edge,
            body=Content(self.text.get_text()),
        )
        return Binding(
            name=self.name,
            value=dict(position=self.position, body=self.inner(text)),
        )

    @property
    def execution(self) -> Function:
        return Function(name="draw.text", body=f"..{self.name}")
