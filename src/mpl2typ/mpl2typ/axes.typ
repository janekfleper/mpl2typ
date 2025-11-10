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
