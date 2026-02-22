import matplotlib.legend
import matplotlib.lines
import matplotlib.container

from pypst import Binding, Color, Content, Length

from .collections import Collection
from .lines import Line2D
from .typst import color_from_mpl, Drawable, Function


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
        legend: "Legend",
    ):
        self.handle = handle
        self.label = label
        self.legend = legend

        child = self.legend.match_handle(self.handle)
        if child is None:
            raise ValueError(f"Could not find handle {self.handle} in legend")
        self.name = child.name

    def render(self) -> str:
        return Function(
            name="legend.line2d.with",
            kwargs=dict(stroke=f"stroke-{self.name}", marker=f"marker-{self.name}"),
        ).render()


class LegendHandlerErrorbar:
    def __init__(
        self,
        handle: matplotlib.container.ErrorbarContainer,
        label: str,
        legend: "Legend",
    ):
        self.handle = handle
        self.label = label
        self.legend = legend

    @property
    def data(self) -> dict[str, str]:
        line = self.handle.lines[0]
        child = self.legend.match_handle(line)
        if child is None:
            raise ValueError(f"Could not find handle {line} in legend")
        return dict(stroke=f"stroke-{child.name}", marker=f"marker-{child.name}")

    @property
    def caps(self) -> dict[str, str]:
        lines = self.handle.lines[1]
        names = []
        for line in lines:
            child = self.legend.match_handle(line)
            if child is None:
                raise ValueError(f"Could not find handle {line} in legend")
            names.append(child.name)

        elements = dict()
        if names and self.handle.has_xerr:
            if len(names) == 1:
                elements["x"] = f"marker-{names[0]}"
            else:
                left, right = names[:2]
                elements["left"] = f"marker-{left}"
                elements["right"] = f"marker-{right}"
        if names and self.handle.has_yerr:
            if len(names) == 1:
                elements["y"] = f"marker-{names[0]}"
            else:
                bottom, top = names[-2:]
                elements["bottom"] = f"marker-{bottom}"
                elements["top"] = f"marker-{top}"

        return elements

    @property
    def bars(self) -> str | dict[str, str]:
        collections = self.handle.lines[2]
        names = []
        for collection in collections:
            child = self.legend.match_handle(collection)
            if child is None:
                raise ValueError(f"Could not find handle {collection} in legend")
            names.append(child.name)

        elements = dict()
        if self.handle.has_xerr:
            elements["x"] = f"stroke-{names[0]}"
        if self.handle.has_yerr:
            elements["y"] = f"stroke-{names[-1]}"

        if not elements:
            return ""
        return elements

    def render(self) -> str:
        return Function(
            name="legend.errorbar.with",
            kwargs=dict(data=self.data, caps=self.caps, bars=self.bars),
        ).render()


class Legend(Drawable):
    def __init__(
        self,
        legend: matplotlib.legend.Legend,
        axes: "mpl2typ.axes.Axes",
    ):
        self.legend = legend
        self.axes = axes

        self.items = []
        self.parse()

    @property
    def name(self) -> str:
        return "legend"

    @property
    def zorder(self) -> float:
        return self.legend.zorder

    def parse(self):
        for handle, label in zip(*self.axes.ax.get_legend_handles_labels()):
            if isinstance(handle, matplotlib.lines.Line2D):
                self.items.append(LegendHandlerLine2D(handle, label, self))
            elif isinstance(handle, matplotlib.container.ErrorbarContainer):
                self.items.append(LegendHandlerErrorbar(handle, label, self))
            else:
                print(f"Unknown handle type {type(handle)}")

    def match_handle(self, handle):
        if isinstance(handle, matplotlib.lines.Line2D):
            for child in self.axes.children:
                if not isinstance(child, Line2D):
                    continue
                if child.line == handle:
                    return child
        elif isinstance(handle, matplotlib.collections.Collection):
            for child in self.axes.children:
                if not isinstance(child, Collection):
                    continue
                if child.collection == handle:
                    return child
        return None

    @property
    def title(self) -> str | Content:
        title = self.legend.get_title().get_text()
        if not title:
            return "none"
        return Content(title)

    @property
    def style(self) -> dict[str, str | int | Length]:
        return {
            "location": LOCATION[self.legend._loc],
            "title": self.title,
            "columns": self.legend._ncols,
            "row-gutter": Length(self.legend.labelspacing, unit="em"),
            "item-gutter": Length(self.legend.handletextpad, unit="em"),
            "column-gutter": Length(self.legend.columnspacing, unit="em"),
            "handle-length": Length(self.legend.handlelength, unit="em"),
            "handle-height": Length(self.legend.handleheight, unit="em"),
        }

    @property
    def fill(self) -> Color:
        return color_from_mpl(color=self.legend.legendPatch.get_facecolor())

    @property
    def stroke(self) -> Color:
        return color_from_mpl(color=self.legend.legendPatch.get_edgecolor())

    @property
    def frame(self) -> dict[str, str | Color | Length | Function]:
        if not self.legend.get_frame_on():
            return dict()

        frame = self.legend.get_frame()
        style = frame.get_boxstyle()
        frame_kwargs = dict()
        if isinstance(style, matplotlib.patches.BoxStyle.Round):
            frame_kwargs["radius"] = Length(
                value=style.rounding_size * frame.get_mutation_scale(),
                unit="pt",
            )

        return dict(
            fill=self.fill,
            stroke=self.stroke,
            frame=Function(
                "block.with",
                kwargs=frame_kwargs,
            ),
        )

    @property
    def definition(self) -> tuple[Binding, ...]:
        style = self.style | self.frame
        items = [dict(handle=item, label=Content(item.label)) for item in self.items]
        return (
            Binding(name=f"{self.name}-style", value=style),
            Binding(name=f"{self.name}-items", value=items),
        )

    @property
    def execution(self) -> Function:
        return Function(
            name="legend.legend",
            body="..{self.name}-style, ..{self.name}-items",
        )
