#let point(d, fill: none, stroke: none) = std.circle(radius: d / 2, fill: fill, stroke: stroke)

#let circle(d, fill: none, stroke: none) = std.circle(radius: d, fill: fill, stroke: stroke)

#let triangle-down(d, fill: none, stroke: none) = polygon(
  (-d, -d),
  (0pt, d),
  (d, -d),
  fill: fill,
  stroke: stroke,
)

#let triangle-up(d, fill: none, stroke: none) = polygon(
  (0pt, -d),
  (-d, d),
  (d, d),
  fill: fill,
  stroke: stroke,
)

#let triangle-left(d, fill: none, stroke: none) = polygon(
  (d, -d),
  (-d, 0pt),
  (d, d),
  fill: fill,
  stroke: stroke,
)

#let triangle-right(d, fill: none, stroke: none) = polygon(
  (-d, -d),
  (-d, d),
  (d, 0pt),
  fill: fill,
  stroke: stroke,
)

#let octagon(d, fill: none, stroke: none) = polygon(
  (-d / 2, -d),
  (-d, -d / 2),
  (-d, d / 2),
  (-d / 2, d),
  (d / 2, d),
  (d, d / 2),
  (d, -d / 2),
  (d / 2, -d),
  fill: fill,
  stroke: stroke,
)
