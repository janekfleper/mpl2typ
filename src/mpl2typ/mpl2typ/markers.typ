#let marker-top-left(body) = place(top + left, dx: 0pt, dy: 0pt, body)
#let marker-horizon-center(body) = place(horizon + center, dx: 0pt, dy: 0pt, body)

#let point(d, fill: none, stroke: none) = marker-horizon-center(std.circle(radius: d / 2, fill: fill, stroke: stroke))

#let circle(d, fill: none, stroke: none) = marker-horizon-center(std.circle(radius: d, fill: fill, stroke: stroke))

#let triangle-down(d, fill: none, stroke: none) = marker-top-left(
  polygon(
    (-d, -d),
    (0pt, d),
    (d, -d),
    fill: fill,
    stroke: stroke,
  ),
)

#let triangle-up(d, fill: none, stroke: none) = marker-top-left(
  polygon(
    (0pt, -d),
    (-d, d),
    (d, d),
    fill: fill,
    stroke: stroke,
  ),
)

#let triangle-left(d, fill: none, stroke: none) = marker-top-left(
  polygon(
    (d, -d),
    (-d, 0pt),
    (d, d),
    fill: fill,
    stroke: stroke,
  ),
)

#let triangle-right(d, fill: none, stroke: none) = marker-top-left(
  polygon(
    (-d, -d),
    (-d, d),
    (d, 0pt),
    fill: fill,
    stroke: stroke,
  ),
)

#let octagon(d, fill: none, stroke: none) = marker-horizon-center(
  polygon.regular(vertices: 8, size: 2 * d, fill: fill, stroke: stroke),
)

)
