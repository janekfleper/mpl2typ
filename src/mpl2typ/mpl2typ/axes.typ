#let xaxis-ticks(show-ticks: (), show-labels: (), ..args, transform) = {
  let (tick-style, label-style, locs, labels) = args.named()
  locs = locs.map(x => (x, 0)).map(transform).map(point => point.at(0))
  if labels == () { labels = locs.len() * ("",) }
  set text(..label-style.text)

  let tick-alignment = (
    "in": (bottom: bottom, top: top),
    "out": (bottom: top, top: bottom),
    "inout": (bottom: horizon, top: horizon),
    "bottom": (bottom: top, top: top),
    "top": (bottom: bottom, top: bottom),
  ).at(tick-style.direction)
  let tick-line = line(..tick-style.line)
  let tick-bottom = if bottom in show-ticks { place(tick-alignment.bottom, tick-line) } else { none }
  let tick-top = if top in show-ticks { place(tick-alignment.top, tick-line) } else { none }

  let label-dy(tick-alignment) = {
    if tick-alignment == bottom {
      label-style.pad + 0pt
    } else if tick-alignment == top {
      label-style.pad + tick-style.line.length
    } else { label-style.pad + tick-style.line.length / 2 }
  }
  let label-alignment = (bottom: center + top, top: center + bottom)
  let label-rotate = rotate.with(label-style.rotation, reflow: true)
  let label-bottom = if bottom in show-labels {
    label => { place(label-alignment.bottom, dy: label-dy(tick-alignment.bottom), label-rotate(label)) }
  } else {
    label => { none }
  }
  let label-top = if top in show-labels {
    label => { place(label-alignment.top, dy: -label-dy(tick-alignment.top.inv()), label-rotate(label)) }
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

#let yaxis-ticks(show-ticks: (), show-labels: (), ..args, transform) = {
  let (tick-style, label-style, locs, labels) = args.named()
  locs = locs.map(y => (0, y)).map(transform).map(point => point.at(1))
  if labels == () { labels = locs.len() * ("",) }
  set text(..label-style.text)

  let tick-alignment = (
    "in": (left: left, right: right),
    "out": (left: right, right: left),
    "inout": (left: center, right: center),
    "left": (left: right, right: right),
    "right": (left: left, right: left),
  ).at(tick-style.direction)
  let tick-line = line(..tick-style.line)
  let tick-left = if left in show-ticks { place(tick-alignment.left, tick-line) } else { none }
  let tick-right = if right in show-ticks { place(tick-alignment.right, tick-line) } else { none }

  let label-dx(tick-alignment) = {
    if tick-alignment == left {
      label-style.pad + 0pt
    } else if tick-alignment == right {
      label-style.pad + tick-style.line.length
    } else { label-style.pad + tick-style.line.length / 2 }
  }
  let label-alignment = (left: horizon + right, right: horizon + left)
  let label-rotate = rotate.with(label-style.rotation)
  let label-left = if left in show-labels {
    label => { place(dx: -label-dx(tick-alignment.left), label-rotate(place(label-alignment.left, label))) }
  } else {
    label => { none }
  }
  let label-right = if right in show-labels {
    label => { place(dx: label-dx(tick-alignment.right.inv()), label-rotate(place(label-alignment.right, label))) }
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

#let xaxis-grid(..args, transform) = {
  let (grid-style, locs) = args.named()
  locs = locs.map(x => (x, 0)).map(transform).map(point => point.at(0))
  let grid-line = rotate(-90deg, reflow: true, line(length: 100%, ..grid-style))
  for loc in locs { if (loc > 0%) and (loc < 100%) { place(dx: loc, grid-line) } }
}

#let yaxis-grid(..args, transform) = {
  let (grid-style, locs) = args.named()
  locs = locs.map(y => (0, y)).map(transform).map(point => point.at(1))
  let grid-line = line(length: 100%, ..grid-style)
  for loc in locs { if (loc > 0%) and (loc < 100%) { place(dy: loc, grid-line) } }
}

#let abc(
  location: top + left,
  inset: 0.4em,
  outset: 0.5em,
  fill: none,
  stroke: none,
  frame: block,
  numbering: "a",
  text-style: (:),
  number,
) = {
  outset = if type(outset) in (length, ratio) { (outset, outset) } else { outset }
  let alignment = if type(location) == std.alignment { location } else { top + left }
  let (dx, dy) = if type(location) == std.alignment {
    (
      if location.x == right { -outset.at(0) } else if location.x == center { 0% } else { outset.at(0) },
      if location.y == bottom { -outset.at(1) } else if location.y == horizon { 0% } else { outset.at(1) },
    )
  } else {
    location
  }

  let frame = frame.with(
    stroke: stroke,
    fill: fill,
    inset: inset,
  )

  let body = if numbering == none { number } else { std.numbering(numbering, number) }
  {
    set text(..text-style)
    std.place(alignment, dx: dx, dy: dy, frame(align(center + horizon, body)))
  }
}

#let spines(spines) = {
  set line(stroke: (cap: "square"))
  if "top" in spines {
    let (start, end) = spines.top.bounds
    let stroke = spines.top.at("stroke", default: black)
    std.place(top, line(start: (start, 0%), end: (end, 0%), stroke: stroke))
  }
  if "bottom" in spines {
    let (start, end) = spines.bottom.bounds
    let stroke = spines.bottom.at("stroke", default: black)
    std.place(bottom, line(start: (start, 0%), end: (end, 0%), stroke: stroke))
  }
  if "left" in spines {
    let (start, end) = spines.left.bounds
    let stroke = spines.left.at("stroke", default: black)
    std.place(left, line(start: (0%, start), end: (0%, end), stroke: stroke))
  }
  if "right" in spines {
    let (start, end) = spines.right.bounds
    let stroke = spines.right.at("stroke", default: black)
    std.place(right, line(start: (100%, start), end: (100%, end), stroke: stroke))
  }
}

#let cell(position: (0, 0), shape: (1, 1), body) = {
  grid.cell(
    x: position.at(0),
    y: position.at(1),
    colspan: shape.at(0),
    rowspan: shape.at(1),
    block(
      width: 100%,
      height: 100%,
      stroke: none,
      fill: none,
      body,
    ),
  )
}

#let inset(position: none, shape: none, body) = {
  assert.ne(position, none, message: "Parameter position must not be none")
  assert.ne(shape, none, message: "Parameter shape must not be none")

  let (dx, dy) = position
  let (width, height) = shape
  std.place(
    top + left,
    dx: dx,
    dy: dy,
    block(
      width: width,
      height: height,
      fill: none,
      stroke: none,
      inset: 0em,
      outset: 0em,
      body,
    ),
  )
}

#let inset-indicator(target: none, source: none, connectors: ()) = {
  assert.ne(target, none, message: "Parameter target must not be none")
  assert.ne(source, none, message: "Parameter source must not be none")

  let (x0, y0) = target.position
  let (x1, y1) = (x0 + target.shape.at(0), y0 + target.shape.at(1))
  let (xt0, yt0) = (target.transform)((x0, y0))
  let (xt1, yt1) = (target.transform)((x1, y1))
  let (hw, ht) = (xt1 - xt0, yt0 - yt1)

  let (xs0, ys0) = source.position
  let (hs, ws) = source.shape

  for conn in connectors.anchors {
    let (xc0, xc1) = if conn.x == left {
      (xt0, xs0)
    } else if conn.x == right {
      (xt0 + hw, xs0 + ws)
    } else {
      panic("Invalid horizontal connector direction: " + repr(conn))
    }
    let (yc0, yc1) = if conn.y == top {
      (yt0, ys0)
    } else if conn.y == bottom {
      (yt0 + ht, ys0 + hs)
    } else {
      panic("Invalid vertical connector direction: " + repr(conn))
    }

    if connectors.stroke != none {
      std.place(top + left, std.line(
        start: (xc0, yc0),
        end: (xc1, yc1),
        stroke: connectors.stroke,
      ))
    }
  }

  // Draw the target rectangle at the end to ensure it is on top of the connectors
  std.place(top + left, dx: xt0, dy: yt0, rect(
    width: hw,
    height: ht,
    fill: target.at("fill", default: none),
    stroke: target.at("stroke", default: none),
    inset: 0em,
    outset: 0em,
  ))
}
