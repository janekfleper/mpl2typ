import pathlib

import matplotlib.figure
import matplotlib.gridspec

from . import typst
from .axes import Axes
from .grid import Grid


def template(width: float, height: float, body: str | None = None) -> str:
    s = ""
    s += f"#let width = {width}cm\n"
    s += f"#let height = {height}cm\n\n"

    block = typst.function(
        "#block",
        named=dict(
            width="width",
            height="height",
            stroke="blue",
        ),
        body=body,
    )

    return s + block


class Figure:
    def __init__(self, fig: matplotlib.figure.Figure):
        self.fig = fig
        self.grids: list[Grid] = []
        self.other_axes: list[Axes] = []
        self.parse()

    @property
    def width(self) -> float:
        return self.fig.get_figwidth() * 2.54

    @property
    def height(self) -> float:
        return self.fig.get_figheight() * 2.54

    def parse(self) -> None:
        grid_axes: list[list[Axes]] = []
        gridspecs: list[matplotlib.gridspec.GridSpec] = []
        for i, ax in enumerate(self.fig.get_axes()):
            gs = ax.get_gridspec()
            if gs is None:
                self.other_axes.append(Axes(str(i), ax, standalone=True))
            elif gs not in gridspecs:
                gridspecs.append(gs)
                grid_axes.append([Axes(str(i), ax)])
            else:
                grid_axes[gridspecs.index(gs)].append(Axes(str(i), ax))

        for i in range(len(gridspecs)):
            self.grids.append(Grid(str(i), gridspecs[i], grid_axes[i]))

    def export(self, path: str | pathlib.Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write('#import "/mpl2typ/lib.typ": *\n\n')
            f.write("#set page(width: auto, height: auto, margin: 0.9mm)\n")
            f.write("\n\n")

            children: list[str] = []
            for grid in self.grids:
                for ax in grid.axes:
                    f.write(ax.export() + "\n")
                f.write(grid.export() + "\n")
                children.append(f"{grid.prefix}-{grid.name}()")

            for ax in self.other_axes:
                f.write(ax.export() + "\n")
                children.append(f"standalone-{ax.prefix}-{ax.name}()")

            f.write(
                template(
                    width=self.width,
                    height=self.height,
                    body=typst.make_body(children),
                )
            )
