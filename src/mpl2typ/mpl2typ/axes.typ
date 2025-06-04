#let xaxis-ticks(show-ticks: (), show-labels: (), ..args) = {
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

#let yaxis-ticks(show-ticks: (), show-labels: (), ..args) = {
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

#let xaxis-grid(..args) = {
  let (grid-style, locs) = args.named()
  let grid-line = rotate(-90deg, reflow: true, line(length: 100%, ..grid-style))
  for loc in locs { if (loc > 0%) and (loc < 100%) { place(dx: loc, grid-line) } }
}

#let yaxis-grid(..args) = {
  let (grid-style, locs) = args.named()
  let grid-line = line(length: 100%, ..grid-style)
  for loc in locs { if (loc > 0%) and (loc < 100%) { place(dy: loc, grid-line) } }
}
