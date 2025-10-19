import matplotlib.legend
import matplotlib.lines
import matplotlib.container

from . import typst


# The "best" location is not supported (yet) in mpl2typ since matplotlib just
# uses the index 0 without actually specifying the location. I would assume
# that the location is only determined during the drawing process.
LOCATION = {
    0: "top + left",
    1: "top + right",
    2: "top + left",
    3: "bottom + left",
    4: "bottom + right",
    5: "horizon + right",
    6: "horizon + right",
    7: "horizon + left",
    8: "bottom + center",
    9: "top + center",
    10: "horizon + center",
}


class LegendHandlerLine2D:
    def __init__(
        self,
        handle: matplotlib.lines.Line2D,
        label: str,
        legend: matplotlib.legend.Legend,
        children,
    ):
        self.handle = handle
        self.label = label
        self.legend = legend
        self.children = children

        try:
            self.index = self.children.index(self.handle)
        except ValueError:
            self.index = None

    def export(self):
        return typst.function(
            "legend.line2d.with",
            named=dict(stroke=f"stroke-{self.index}", marker=f"marker-{self.index}"),
            inline=True,
        )


class LegendHandlerErrorbar:
    def __init__(
        self,
        handle: matplotlib.container.ErrorbarContainer,
        label: str,
        legend: matplotlib.legend.Legend,
        children,
    ):
        self.handle = handle
        self.label = label
        self.legend = legend
        self.children = children

    @property
    def data(self):
        line = self.handle.lines[0]
        try:
            index = self.children.index(line)
        except ValueError:
            index = None

        return typst.dictionary(
            dict(stroke=f"stroke-{index}", marker=f"marker-{index}"),
            inline=True,
        )

    @property
    def caps(self):
        lines = self.handle.lines[1]
        indices = []
        for line in lines:
            try:
                index = self.children.index(line)
            except ValueError:
                index = None
            indices.append(index)

        elements = dict()
        if indices and self.handle.has_xerr:
            if len(indices) == 1:
                elements["x"] = f"marker-{indices[0]}"
            else:
                left, right = indices[:2]
                elements["left"] = f"marker-{left}"
                elements["right"] = f"marker-{right}"
        if indices and self.handle.has_yerr:
            if len(indices) == 1:
                elements["y"] = f"marker-{indices[0]}"
            else:
                bottom, top = indices[-2:]
                elements["bottom"] = f"marker-{bottom}"
                elements["top"] = f"marker-{top}"

        return typst.dictionary(elements, inline=True)

    @property
    def bars(self):
        collections = self.handle.lines[2]
        indices = []
        for collection in collections:
            try:
                index = self.children.index(collection)
            except ValueError:
                index = None
            indices.append(index)

        elements = dict()
        if self.handle.has_xerr:
            elements["x"] = f"stroke-{indices[0]}"
        if self.handle.has_yerr:
            elements["y"] = f"stroke-{indices[-1]}"

        if not elements:
            return ""
        return typst.dictionary(elements, inline=True)

    def export(self):
        return typst.function(
            "legend.errorbar.with",
            named=dict(data=self.data, caps=self.caps, bars=self.bars),
        )


class Legend:
    def __init__(self, legend: matplotlib.legend.Legend):
        self.legend = legend
        self.ax = self.legend.axes

        self.items = []
        self.parse()

    def parse(self):
        for handle, label in zip(*self.ax.get_legend_handles_labels()):
            if isinstance(handle, matplotlib.lines.Line2D):
                self.items.append(
                    LegendHandlerLine2D(handle, label, self.legend, self.ax._children)
                )
            elif isinstance(handle, matplotlib.container.ErrorbarContainer):
                self.items.append(
                    LegendHandlerErrorbar(handle, label, self.legend, self.ax._children)
                )
            else:
                print(f"Unknown handle type {type(handle)}")

    @property
    def title(self) -> str:
        title = self.legend.get_title().get_text()
        if not title:
            return "none"
        return f"[{title}]"

    @property
    def style(self) -> dict:
        return {
            "location": LOCATION[self.legend._loc],
            "title": self.title,
            "columns": self.legend._ncols,
            "row-gutter": typst.length(self.legend.labelspacing, unit="em"),
            "item-gutter": typst.length(self.legend.handletextpad, unit="em"),
            "column-gutter": typst.length(self.legend.columnspacing, unit="em"),
            "handle-length": typst.length(self.legend.handlelength, unit="em"),
            "handle-height": typst.length(self.legend.handleheight, unit="em"),
        }

    @property
    def fill(self) -> str:
        return typst.color(self.legend.legendPatch.get_facecolor())

    @property
    def stroke(self) -> str:
        return typst.color(self.legend.legendPatch.get_edgecolor())

    @property
    def frame(self) -> dict:
        if not self.legend.get_frame_on():
            return dict()

        frame = self.legend.get_frame()
        style = frame.get_boxstyle()
        frame_kwargs = dict()
        if isinstance(style, matplotlib.patches.BoxStyle.Round):
            frame_kwargs["radius"] = (
                f"{style.rounding_size * frame.get_mutation_scale():.2f}pt"
            )
        return dict(
            fill=self.fill,
            stroke=self.stroke,
            frame=typst.function(
                "block.with",
                named=frame_kwargs,
                inline=True,
            ),
        )

    @property
    def definition(self) -> str:
        style = typst.dictionary(self.style | self.frame)
        items = [
            typst.dictionary(dict(handle=item.export(), label=f"[{item.label}]"))
            for item in self.items
        ]
        return (
            "let legend-style = "
            + style
            + "\n"
            + "let legend-items = "
            + typst.array(items, inline=False)
        )

    @property
    def draw(self) -> tuple[str, float]:
        return (
            typst.function(
                "legend.legend",
                body="..legend-style, ..legend-items",
                inline=True,
            ),
            self.legend.zorder,
        )

    def export(self) -> str:
        return self.definition + "\n" + self.draw[0]
