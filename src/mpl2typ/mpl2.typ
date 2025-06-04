#let draw-line(points, stroke: none, marker: none) = {
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


#let draw-path-collection(path, data, transform) = {
  for (offset, ..props) in data {
    let (x, y) = transform(offset)
    place(dx: x, dy: y, path(..props))
  }
}

#let draw-quad-mesh(vertices, data, colormap, transform) = {
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


#let draw-xaxis-ticks(show-ticks: (), show-labels: (), ..args) = {
  let (tick-style, label-style, locs, labels) = args.named()
  if labels == () { labels = locs.len() * ("",) }
  set text(..label-style.text)

  let (tick-alignment, tick-dy) = (
    "in": (bottom, 0pt),
    "out": (top, tick-style.line.length),
    "inout": (horizon, tick-style.line.length / 2),
  ).at(tick-style.direction)
  let tick-line = line(..tick-style.line)
  let tick-bottom = if bottom in show-ticks { place(tick-alignment, tick-line) } else { none }
  let tick-top = if top in show-ticks { place(tick-alignment.inv(), tick-line) } else { none }

  let label-alignment = center + top
  let label-dy = label-style.pad + tick-dy
  let label-rotate = rotate.with(label-style.rotation, reflow: true)
  let label-bottom = if bottom in show-labels {
    label => { place(label-alignment, dy: label-dy, label-rotate(label)) }
  } else {
    label => { none }
  }
  let label-top = if top in show-labels {
    label => { place(label-alignment.inv(), dy: -label-dy, label-rotate(label)) }
  } else {
    label => { none }
  }

  for tick in locs.zip(labels) {
    let (loc, label) = tick
    if (loc < 0%) or (loc > 100%) { continue }
    place(bottom, dx: loc, tick-bottom + label-bottom(label))
    place(top, dx: loc, tick-top + label-top(label))
  }
}

#let draw-yaxis-ticks(show-ticks: (), show-labels: (), ..args) = {
  let (tick-style, label-style, locs, labels) = args.named()
  if labels == () { labels = locs.len() * ("",) }
  set text(..label-style.text)

  let (tick-alignment, tick-dx) = (
    "in": (left, 0pt),
    "out": (right, tick-style.line.length),
    "inout": (center, tick-style.line.length / 2),
  ).at(tick-style.direction)
  let tick-line = line(..tick-style.line)
  let tick-left = if left in show-ticks { place(tick-alignment, tick-line) } else { none }
  let tick-right = if right in show-ticks { place(tick-alignment.inv(), tick-line) } else { none }

  let label-alignment = horizon + right
  let label-dx = label-style.pad + tick-dx
  let label-rotate = rotate.with(label-style.rotation)
  let label-left = if left in show-labels {
    label => { place(dx: -label-dx, label-rotate(place(label-alignment, label))) }
  } else {
    label => { none }
  }
  let label-right = if right in show-labels {
    label => { place(dx: label-dx, label-rotate(place(label-alignment.inv(), label))) }
  } else {
    label => { none }
  }

  for tick in locs.zip(labels) {
    let (loc, label) = tick
    if (loc < 0%) or (loc > 100%) { continue }
    place(left, dy: loc, tick-left + label-left(label))
    place(right, dy: loc, tick-right + label-right(label))
  }
}

#let draw-xaxis-grid(..args) = {
  let (grid-style, locs) = args.named()
  let grid-line = rotate(-90deg, reflow: true, line(length: 100%, ..grid-style))
  for loc in locs { if (loc > 0%) and (loc < 100%) { place(dx: loc, grid-line) } }
}

#let draw-yaxis-grid(..args) = {
  let (grid-style, locs) = args.named()
  let grid-line = line(length: 100%, ..grid-style)
  for loc in locs { if (loc > 0%) and (loc < 100%) { place(dy: loc, grid-line) } }
}
