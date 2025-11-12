#import "axes.typ"
#import "draw.typ"
#import "hatch.typ"
#import "markers.typ"
#import "legend.typ"

#let _default-colors = (
  color.rgb("#1f77b4"),
  color.rgb("#ff7f0e"),
  color.rgb("#2ca02c"),
  color.rgb("#d62728"),
  color.rgb("#9467bd"),
  color.rgb("#8c564b"),
  color.rgb("#e377c2"),
  color.rgb("#7f7f7f"),
  color.rgb("#bcbd22"),
)

#let colors(i) = _default-colors.at(calc.rem(i, _default-colors.len()))
