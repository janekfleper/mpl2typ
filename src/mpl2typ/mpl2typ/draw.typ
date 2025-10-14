#let line(points, stroke: none, marker: none, transform) = {
  points = points.map(transform)

  if stroke != none {
    let (first, ..other) = points
    place(
      curve(
        stroke: stroke,
        curve.move(first),
        ..other.map(point => curve.line(point)),
      ),
    )
  }

  if marker != none {
    let dx = if marker.has("height") { marker.height / 2 } else { 0pt }
    let dy = if marker.has("width") { marker.width / 2 } else { 0pt }
    for point in points {
      place(dx: point.at(0) - dx, dy: point.at(1) - dy, marker)
    }
  }
}

#let draw-line(points, offset, fill, stroke) = {
  let (first, ..other) = points
  let (dx, dy) = offset
  place(
    dx: dx,
    dy: -dy,
    curve(
      fill: fill,
      stroke: stroke,
      curve.move(first),
      ..other.map(curve.line),
    ),
  )
}

#let update-stroke(i, props) = {
  if "paint" in props.keys() {
    let paint = props.at("paint")
    (paint: paint.at(calc.rem-euclid(i, paint.len())))
  }
  if "thickness" in props.keys() {
    let thickness = props.at("thickness")
    (thickness: thickness.at(calc.rem-euclid(i, thickness.len())))
  }
  if "dash" in props.keys() {
    let dash = props.at("dash")
    (dash: dash.at(calc.rem-euclid(i, dash.len())))
  }
}

#let line-collection(
  data: (:),
  path: none,
  offset: none,
  fill: none,
  stroke: none,
  transform: none,
  offset-transform: none,
) = {
  assert(transform != none, message: "Parameter transform must not be none")
  assert(offset-transform != none, message: "Parameter offset-transform must not be none")

  if data == (:) { return draw-line(path.map(transform), offset-transform(offset), fill, stroke) }

  let paths = data.remove("paths", default: ())
  let offsets = data.remove("offsets", default: ())
  let length = calc.max(paths.len(), offsets.len())
  let fills = data.remove("fills", default: ())
  let strokes = data.remove("strokes", default: (:))

  if length == 0 {
    draw-line(
      path.map(transform),
      offset-transform(offset),
      fill + fills.at(0, default: none),
      stroke + update-stroke(0, strokes),
    )
  } else {
    for i in range(length) {
      let offset = if offsets.len() > 0 { offsets.at(calc.rem-euclid(i, offsets.len())) } else { offset }
      let path = if paths.len() > 0 { paths.at(calc.rem-euclid(i, paths.len())) } else { path }
      let fill = if fills.len() > 0 { fills.at(calc.rem-euclid(i, fills.len())) } else { fill }
      let stroke = stroke + update-stroke(i, strokes)
      draw-line(path.map(transform), offset-transform(offset), fill, stroke)
    }
  }
}

#let path-collection(path, data, transform) = {
  for (offset, ..props) in data {
    let (x, y) = transform(offset)
    place(dx: x, dy: y, path(..props))
  }
}

#let quad-mesh(vertices, data, colormap, transform) = {
  for (i, row) in data.enumerate() {
    for (j, value) in row.enumerate() {
      let color = colormap(value)
      place(
        curve(
          fill: color,
          curve.move(transform(vertices.at(i).at(j))),
          curve.line(transform(vertices.at(i).at(j + 1))),
          curve.line(transform(vertices.at(i + 1).at(j + 1))),
          curve.line(transform(vertices.at(i + 1).at(j))),
          curve.close(),
        ),
      )
    }
  }
}
