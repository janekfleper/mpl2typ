import matplotlib
import matplotlib.text
import matplotlib.axes
import matplotlib.transforms

from . import typst


def relativ_fontsize(fontsize: float) -> str:
    delta = fontsize - matplotlib.rcParams["font.size"]
    fontsize = typst.length(1, "em")
    if delta > 0:
        fontsize += " + " + typst.length(delta, "pt")
    elif delta < 0:
        fontsize += " - " + typst.length(abs(delta), "pt")
    return fontsize


class Text:
    def __init__(
        self,
        text: matplotlib.text.Text,
        axes: "typst.axes.Axes",
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
    def position(self) -> str | tuple[str, str]:
        return self.axes.transform_point(
            self.text.get_position(),
            self.text.get_transform(),
        )

    @property
    def fontsize(self) -> str:
        return relativ_fontsize(float(self.text.get_fontsize()))

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
                return typst.function(
                    "rotate",
                    pos=[typst.degree(-rotation)],
                    body=typst.function(
                        "place",
                        pos=[self.alignment],
                        body=body,
                    ),
                )
            else:  # "default" or None
                return typst.function(
                    "place",
                    pos=[self.alignment],
                    body=typst.function(
                        "rotate",
                        pos=[typst.degree(-rotation)],
                        named=dict(reflow="true"),
                        body=body,
                    ),
                )
        else:
            return typst.function(
                "place",
                pos=[self.alignment],
                body=body,
            )

    @property
    def definition(self) -> str:
        kwargs = dict(size=self.fontsize, fill=self.color)
        if self.text.get_verticalalignment() in ["center", "bottom"]:
            kwargs["bottom-edge"] = '"descender"'

        text = typst.function(
            "text",
            named=kwargs,
            body=typst.content(self.text.get_text()),
            inline=True,
        )
        return f"let {self.name} = {typst.dump(dict(position=self.position, body=self.inner(text)))}"

    @property
    def draw(self) -> tuple[str, float]:
        return (
            typst.function(
                "draw.text",
                body=f"..{self.name}",
                inline=True,
            ),
            self.text.zorder,
        )

    def export(self) -> str:
        return f"let {self.name} = " + self.definition + "\n" + self.draw[0]
