// Collection of unfilled and filled markers from the marker reference
// https://matplotlib.org/stable/gallery/lines_bars_and_markers/marker_reference.html
//
// Markers created from TeX symbols and markers created from paths are not
// implemented (yet). Neither are advanved marker modifications with transform
// nor marker cap and join styles.
//
// All markers are wrapped in `marker-top-left()` or `marker-horizon-center()`
// to reference the markers by their center (according to matplotlib).

#let marker-top-left(body) = place(top + left, dx: 0pt, dy: 0pt, body)
#let marker-horizon-center(body) = place(horizon + center, dx: 0pt, dy: 0pt, body)

#let point(d, fill: none, stroke: none) = marker-horizon-center(std.circle(radius: d / 2, fill: fill, stroke: stroke))

#let pixel(d, fill: none, stroke: none) = marker-horizon-center(
  rect(
    width: 1pt,
    height: 1pt,
    fill: fill,
    stroke: stroke,
  ),
)

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

#let tri-up(d, fill: none, stroke: none) = marker-horizon-center({
  place(line(start: (0pt, 0pt), end: (0pt, -d), stroke: stroke))
  place(line(start: (0pt, 0pt), end: (d * 0.8, d * 0.5), stroke: stroke))
  place(line(start: (0pt, 0pt), end: (-d * 0.8, d * 0.5), stroke: stroke))
})

#let tri-down(d, fill: none, stroke: none) = marker-horizon-center({
  place(line(start: (0pt, 0pt), end: (0pt, d), stroke: stroke))
  place(line(start: (0pt, 0pt), end: (d * 0.8, -d * 0.5), stroke: stroke))
  place(line(start: (0pt, 0pt), end: (-d * 0.8, -d * 0.5), stroke: stroke))
})

#let tri-left(d, fill: none, stroke: none) = marker-horizon-center({
  place(line(start: (0pt, 0pt), end: (-d, 0pt), stroke: stroke))
  place(line(start: (0pt, 0pt), end: (d * 0.5, d * 0.8), stroke: stroke))
  place(line(start: (0pt, 0pt), end: (d * 0.5, -d * 0.8), stroke: stroke))
})

#let tri-right(d, fill: none, stroke: none) = marker-horizon-center({
  place(line(start: (0pt, 0pt), end: (d, 0pt), stroke: stroke))
  place(line(start: (0pt, 0pt), end: (-d * 0.5, d * 0.8), stroke: stroke))
  place(line(start: (0pt, 0pt), end: (-d * 0.5, -d * 0.8), stroke: stroke))
})

#let octagon(d, fill: none, stroke: none) = marker-horizon-center(
  polygon.regular(vertices: 8, size: 2 * d, fill: fill, stroke: stroke),
)

#let square(d, fill: none, stroke: none) = marker-horizon-center(
  rect(
    width: d * 2,
    height: d * 2,
    fill: fill,
    stroke: stroke,
  ),
)

#let pentagon(d, fill: none, stroke: none) = marker-horizon-center(
  polygon.regular(vertices: 5, size: 2 * d, fill: fill, stroke: stroke),
)

#let plus-filled(d, fill: none, stroke: none) = marker-top-left({
  let w = d / 3
  polygon(
    (-w, -d),
    (w, -d),
    (w, -w),
    (d, -w),
    (d, w),
    (w, w),
    (w, d),
    (-w, d),
    (-w, w),
    (-d, w),
    (-d, -w),
    (-w, -w),
    fill: fill,
    stroke: stroke,
  )
})

#let star(d, fill: none, stroke: none) = marker-top-left({
  import calc: sin, cos, pi
  let angle = 2 * pi / 5
  let inner = 0.381966
  let points = ()
  for i in range(5) {
    let a = -pi / 2 + i * angle
    points.push((d * cos(a), d * sin(a)))
    let b = -pi / 2 + i * angle + angle / 2
    points.push((d * inner * cos(b), d * inner * sin(b)))
  }
  polygon(..points, fill: fill, stroke: stroke)
})

#let hexagon1(d, fill: none, stroke: none) = marker-horizon-center({
  polygon.regular(vertices: 6, size: 2 * d, fill: fill, stroke: stroke)
})

#let hexagon2(d, fill: none, stroke: none) = marker-horizon-center({
  rotate(90deg, polygon.regular(vertices: 6, size: 2 * d, fill: fill, stroke: stroke))
})

#let plus(d, fill: none, stroke: none) = marker-horizon-center({
  place(line(start: (-d, 0pt), end: (d, 0pt), stroke: stroke))
  place(line(start: (0pt, -d), end: (0pt, d), stroke: stroke))
})

#let x(d, fill: none, stroke: none) = marker-horizon-center({
  place(line(start: (-d, -d), end: (d, d), stroke: stroke))
  place(line(start: (-d, d), end: (d, -d), stroke: stroke))
})

#let x-filled(d, fill: none, stroke: none) = marker-top-left({
  let w = d / 2
  polygon(
    (-w, -d),
    (0pt, -w),
    (w, -d),
    (d, -w),
    (w, 0pt),
    (d, w),
    (w, d),
    (0pt, w),
    (-w, d),
    (-d, w),
    (-w, 0pt),
    (-d, -w),
    fill: fill,
    stroke: stroke,
  )
})

#let diamond(d, fill: none, stroke: none) = marker-top-left(
  polygon(
    (0pt, -d),
    (d, 0pt),
    (0pt, d),
    (-d, 0pt),
    fill: fill,
    stroke: stroke,
  ),
)

#let thin-diamond(d, fill: none, stroke: none) = marker-top-left(
  polygon(
    (0pt, -d),
    (d * 0.6, 0pt),
    (0pt, d),
    (-d * 0.6, 0pt),
    fill: fill,
    stroke: stroke,
  ),
)

#let vline(d, fill: none, stroke: none) = marker-top-left(line(start: (0pt, -d), end: (0pt, d), stroke: stroke))

#let hline(d, fill: none, stroke: none) = marker-top-left(line(start: (-d, 0pt), end: (d, 0pt), stroke: stroke))

#let tickleft(d, fill: none, stroke: none) = marker-top-left(
  line(
    start: (0pt, 0pt),
    end: (-2 * d, 0pt),
    stroke: stroke,
  ),
)

#let tickright(d, fill: none, stroke: none) = marker-top-left(
  line(
    start: (0pt, 0pt),
    end: (2 * d, 0pt),
    stroke: stroke,
  ),
)

#let tickup(d, fill: none, stroke: none) = marker-top-left(
  line(
    start: (0pt, 0pt),
    end: (0pt, 2 * d),
    stroke: stroke,
  ),
)

#let tickdown(d, fill: none, stroke: none) = marker-top-left(
  line(
    start: (0pt, 0pt),
    end: (0pt, -2 * d),
    stroke: stroke,
  ),
)

#let caretleft(d, fill: none, stroke: none) = marker-top-left(
  polygon(
    (d * 1.5, -d),
    (0pt, 0pt),
    (d * 1.5, d),
    fill: fill,
    stroke: stroke,
  ),
)

#let caretright(d, fill: none, stroke: none) = marker-top-left(
  polygon(
    (-d * 1.5, -d),
    (0pt, 0pt),
    (-d * 1.5, d),
    fill: fill,
    stroke: stroke,
  ),
)

#let caretup(d, fill: none, stroke: none) = marker-top-left(
  polygon(
    (-d, d * 1.5),
    (0pt, 0pt),
    (d, d * 1.5),
    fill: fill,
    stroke: stroke,
  ),
)

#let caretdown(d, fill: none, stroke: none) = marker-top-left(
  polygon(
    (-d, -d * 1.5),
    (0pt, 0pt),
    (d, -d * 1.5),
    fill: fill,
    stroke: stroke,
  ),
)

#let caretleftbase(d, fill: none, stroke: none) = marker-top-left(
  polygon(
    (0pt, -d),
    (-d * 1.5, 0pt),
    (0pt, d),
    fill: fill,
    stroke: stroke,
  ),
)

#let caretrightbase(d, fill: none, stroke: none) = marker-top-left(
  polygon(
    (0pt, -d),
    (d * 1.5, 0pt),
    (0pt, d),
    fill: fill,
    stroke: stroke,
  ),
)

#let caretupbase(d, fill: none, stroke: none) = marker-top-left(
  polygon(
    (-d, 0pt),
    (0pt, -d * 1.5),
    (d, 0pt),
    fill: fill,
    stroke: stroke,
  ),
)

#let caretdownbase(d, fill: none, stroke: none) = marker-top-left(
  polygon(
    (-d, 0pt),
    (0pt, d * 1.5),
    (d, 0pt),
    fill: fill,
    stroke: stroke,
  ),
)
