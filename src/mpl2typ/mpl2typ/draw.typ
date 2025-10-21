#let place(position, body) = {
  std.place(top + left, dx: position.at(0), dy: position.at(1), body)
}

// This is just a wrapper around the place function for now...
#let text(position: none, body: none) = {
  assert.ne(position, none, message: "Parameter position must not be none")
  place(position, body)
}

#let line(data: (), stroke: none, marker: none, transform: none) = {
  assert.ne(transform, none, message: "Parameter transform must not be none")
  let points = data.map(transform)

  if stroke != none {
    let (first, ..other) = points
    std.place(
      top + left,
      curve(
        stroke: stroke,
        curve.move(first),
        ..other.map(point => curve.line(point)),
      ),
    )
  }

  if marker != none {
    for point in points { place(point, marker) }
  }
}

#let draw-line(points, offset, fill, stroke) = {
  let (first, ..other) = points
  place(
    offset,
    curve(
      fill: fill,
      stroke: stroke,
      curve.move(first),
      ..other.map(curve.line),
    ),
  )
}

#let rescale(point, scale: scale) = point.map(x => x * scale)

#let _get-prop(i, prop) = {
  if type(prop) != array {
    return prop
  } else if (prop == none) or (prop.len() == 0) {
    none
  } else if prop.len() > 1 {
    prop.at(calc.rem-euclid(i, prop.len()))
  } else {
    prop.at(0)
  }
}

#let _get-stroke(i, stroke) = (
  paint: _get-prop(i, stroke.paint),
  thickness: _get-prop(i, stroke.thickness),
  dash: _get-prop(i, stroke.dash),
)

#let collection(
  data: (:),
  fill: none,
  stroke: none,
  transform: none,
  compute-scale: none,
  offset-transform: none,
) = {
  assert.ne(transform, none, message: "Parameter transform must not be none")
  assert.ne(offset-transform, none, message: "Parameter offset-transform must not be none")
  if compute-scale == none { compute-scale = size => size }

  let path = data.remove("path", default: ())
  let size = data.remove("size", default: ())
  let offset = data.remove("offset", default: ())
  let length = calc.max(path.len(), offset.len())

  for i in range(length) {
    let _path = _get-prop(i, path)
    let _size = _get-prop(i, size)
    let _offset = _get-prop(i, offset)
    let _fill = _get-prop(i, fill)
    let _stroke = _get-stroke(i, stroke)

    if _size != none { _path = _path.map(rescale.with(scale: compute-scale(_size))) }
    draw-line(_path.map(transform), offset-transform(_offset), _fill, _stroke)
  }
}

#let quad-mesh(data: (:), colormap: none, transform: none) = {
  assert.ne(colormap, none, message: "Parameter colormap must not be none")
  assert.ne(transform, none, message: "Parameter transform must not be none")
  let vertices = data.remove("vertices", default: ())
  let values = data.remove("values", default: ())

  for (i, row) in values.enumerate() {
    for (j, value) in row.enumerate() {
      let color = colormap(value)
      std.place(
        top + left,
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
