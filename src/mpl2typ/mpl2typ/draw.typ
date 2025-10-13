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

#let draw-line(points, offset, stroke) = {
  let (first, ..other) = points
  let (dx, dy) = offset
  place(
    dx: dx,
    dy: -dy,
    curve(
      stroke: stroke,
      curve.move(first),
      ..other.map(curve.line),
    ),
  )
}

#let update-stroke(i, props) = {
  if "strokes" not in props.keys() { return (:) }
  let strokes = props.at("strokes")

  if "paint" in strokes.keys() {
    let paint = strokes.at("paint")
    (paint: paint.at(calc.rem-euclid(i, paint.len())))
  }
  if "thickness" in strokes.keys() {
    let thickness = strokes.at("thickness")
    (thickness: thickness.at(calc.rem-euclid(i, thickness.len())))
  }
  if "dash" in strokes.keys() {
    let dash = strokes.at("dash")
    (dash: dash.at(calc.rem-euclid(i, dash.len())))
  }
}

#let line-collection(data, path: none, offset: none, fill: none, stroke: none, transform, offset-transform) = {
  if offset != none {
    if path != none {
      let (..props) = data
      let stroke = stroke + update-stroke(0, props)
      draw-line(path.map(transform), offset-transform(offset), stroke)
    } else {
      let (paths, ..props) = data
      for (i, path) in paths.enumerate() {
        let stroke = stroke + update-stroke(i, props)
        draw-line(path.map(transform), offset-transform(offset), stroke)
      }
    }
  } else {
    let (offsets, ..data) = data
    for (i, offset) in offsets.enumerate() {
      if path != none {
        let stroke = stroke + update-stroke(i, data)
        draw-line(path.map(transform), offset-transform(offset), stroke)
      } else {
        let (paths, ..props) = data
        let path = paths.at(calc.rem-euclid(i, paths.len()))
        let stroke = stroke + update-stroke(i, props)
        draw-line(path.map(transform), offset-transform(offset), stroke)
      }
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
