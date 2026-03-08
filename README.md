# mpl2typ

A Python package to export Matplotlib figures to structured Typst files.

> [!WARNING]
> This package is far from stable and very much incomplete.

## Overview

What if you could create your figures with Matplotlib and then apply the final touches to your figures directly in Typst?
The drawing primitives built into Typst are capable rendering anything Matplotlib has to offer, we just need to translate the figure structure into Typst code.
This is exactly what `mpl2typ` does by parsing the figure structure and generating the corresponding Typst code.
As an example, the [GridSpec](https://matplotlib.org/stable/api/_as_gen/matplotlib.gridspec.GridSpec.html) layout of a figure is converted to a [grid](https://typst.app/docs/reference/layout/grid/) in Typst.
You can then adjust the grid spacing, apply show rules to the cells, or even completely rearrange the axes in the grid.

I initially developed this package for my own thesis where I wanted to have perfectly styled figures.
Since I had to prioritize the actual writing of my thesis over developing this package, I only added the specific features from Matplotlib that I actually needed.
Now that I have finished my thesis, I want to turn this into a proper package covering as much of Matplotlib as possible.

## Installation

Clone the repository and install the package with `uv`:

```bash
git clone https://github.com/janekfleper/mpl2typ.git
cd mpl2typ
uv sync
```

## Usage

```python
import matplotlib.pyplot as plt
import mpl2typ

header = """
#import "/mpl2typ/lib.typ": *

#set page(width: auto, height: auto, margin: 0.9em)
"""

fig, ax = plt.subplots()
ax.plot([0, 1, 2])
fig.show()
mpl2typ.Figure(fig).render("plot/", header=header)
```

## Examples

See the [examples](examples) directory for a notebook with many examples showing the current capabilities of `mpl2typ`.
The generated Typst files are also included in the examples directory.
Add the `mpl2typ/` directory to the root directory of your Typst project to compile the generated Typst files.

## Some comments about the package

### Structured figure exports

The structure of a Matplotlib figure is actually quite simple.
There is a root "figure" that contains axes on a grid or at arbitrary locations.
Each axes then has lines, collections, etc. to display the actual data, and usually an x-axis and a y-axis with ticks and labels.
Such a structure can be easily implemented with primitive Typst functions.
The root figure consists of an outer block and an inner block to create the outer padding of the figure.
The inner block will then contain all the axes.
If the figure uses a grid, the same is done in Typst.
Arbitrary axes positions and shapes can be created with `place()`.
It is also possible to have a grid and a few manually positioned axes, e.g. for insets.

Each axes will be a `block()` to create a new scope for the data, the x-axis, the y-axis, the legend etc.
By drawing exclusively in relative coordinates, everything will be correctly rescaled if you want to change the shape of an axes or the spacing of a grid.
E.g. the position (90%, 10%) will always have a distance of 10% to the top-right corner of an axes.
Non-positional sizes on the other hand will always use absolute units.
If your ticks to have a length of 4pt and the font size is 12pt, you want those sizes to be conserved when rescaling the axes.

The data will be kept in the original coordinate system, and each axes has a transformation function to compute the relative coordinates for the drawing.
When you change the limits of the x-axis or the y-axis, the transformation function will be updated to get the new relative coordinates.
You can also use the transformation function to place annotations in data coordinates inside the axes.
Whether this is a `block()` with a text annotation or an arrow to connect data points is up to you.

### Why not a custom Matplotlib backend?

Matplotlib can already create figures in a custom file format with a corresponding backend.
This is surprisingly simple, you just need to implement four methods to draw images, paths, meshs, and text.
For Typst such a backend is already available, see [mpl-typst](https://github.com/daskol/mpl-typst). The generation of the .typ file is super fast, as is the compilation.
And while the resulting figures look really great, the format of the generated code is not suitable for changes to the layout or the styling.
Everything is drawn in absolute/relative coordinates of the root block, and adjusting the limits of an axes would already require an unreasonable amount of work.
You would just do the changes in Matplotlib and generate a new figure.
Being able to apply the final touches to your figures directly in Typst would significantly improve your workflow.
This is where mpl2typ comes in!

### Why not a Typst package?

As you know there are two popular packages available to create plots directly in Typst, namely [cetz-plot](https://github.com/cetz-package/cetz-plot) and [lilaq](https://github.com/lilaq-project/lilaq).
While both projects are really impressive, they are (in my opinion) not suitable for large projects and/or external data.
Exporting your data to a .json file and creating your plots entirely in Typst is of course possible, but the scalability with the complexity of the figures is just not good.
The package has to figure out all the layouting and scaling, which requires context and a lot of computation, on every compilation.
Typst can certainly compensate some of the compilation time with its incremental approach, but a thesis with 10+ figures with multiple axes will still force the compiler onto its knees.
Letting Matplotlib (and numpy) take care of the heavy lifting and using Typst _only_ for the drawing scales really well on the other hand.
The Typst code generated by mpl2typ does not require any context and does not use any external packages by default.
The compilation is therefore as fast as you would expect it from native Typst.

## License

`mpl2typ` is licensed under the MIT License.
See the [LICENSE](LICENSE) file for more details.

## Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.
