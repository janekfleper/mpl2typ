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

#let line-collection(data, stroke, transform) = {
  for (path, ..props) in data {
    let (first, ..other) = path.map(transform)
    place(
      curve(
        stroke: stroke + props,
        curve.move(first),
        ..other.map(curve.line),
      ),
    )
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
