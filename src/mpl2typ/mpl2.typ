#let marker-dot(d, fill: none, stroke: none) = circle(radius: d / 2, fill: fill, stroke: stroke)

#let marker-circle(d, fill: none, stroke: none) = circle(radius: d, fill: fill, stroke: stroke)

#let marker-triangle-down(d, fill: none, stroke: none) = polygon(
  (-d, -d),
  (0pt, d),
  (d, -d),
  fill: fill,
  stroke: stroke,
)

#let marker-triangle-up(d, fill: none, stroke: none) = polygon(
  (0pt, -d),
  (-d, d),
  (d, d),
  fill: fill,
  stroke: stroke,
)

#let marker-triangle-left(d, fill: none, stroke: none) = polygon(
  (d, -d),
  (-d, 0pt),
  (d, d),
  fill: fill,
  stroke: stroke,
)

#let marker-triangle-right(d, fill: none, stroke: none) = polygon(
  (-d, -d),
  (-d, d),
  (d, 0pt),
  fill: fill,
  stroke: stroke,
)

#let marker-octagon(d, fill: none, stroke: none) = polygon(
  (-d / 2, -d),
  (-d, -d / 2),
  (-d, d / 2),
  (-d / 2, d),
  (d / 2, d),
  (d, d / 2),
  (d, -d / 2),
  (d / 2, -d),
  fill: fill,
  stroke: stroke,
)


#let draw-marker(points, marker: none) = {
  if marker == none { return }

  let dx = if marker.has("height") { marker.height / 2 } else { 0pt }
  let dy = if marker.has("width") { marker.width / 2 } else { 0pt }
  points.map(point => place(dx: point.at(0) - dx, dy: point.at(1) - dy, marker)).join([])
}

#let draw-line(points, stroke: none) = {
  if stroke == none { return }

  let (first, ..points) = points
  place(
    curve(
      stroke: stroke,
      curve.move(first),
      ..points.map(point => curve.line(point)),
    ),
  )
}


#let draw-xaxis-ticks(alignment, show-ticks: true, show-labels: true, ..args) = {
  let (tick-style, label-style, locs, labels) = args.named()
  if labels == () { labels = locs.len() * ("",) }
  set line(..tick-style.line)
  set text(..label-style.text)

  let (tick-alignment, tick-dy) = if tick-style.direction == "in" {
    (if alignment == bottom { bottom } else { top }, 0pt)
  } else if tick-style.direction == "out" {
    (if alignment == bottom { top } else { bottom }, tick-style.line.length)
  } else if tick-style.direction == "inout" {
    (horizon, tick-style.line.length / 2)
  } else {
    panic("Unknown tick direction '" + tick-style.direction + "'")
  }

  let label-alignment = center + if alignment == bottom { top } else { bottom }
  let label-dy = label-style.pad + tick-dy
  if alignment == top { label-dy = -label-dy }

  place(
    alignment,
    block(
      width: 100%,
      locs
        .zip(labels)
        .map(tick => {
          let (loc, label) = tick
          if (loc < 0%) or (loc > 100%) { return }
          place(
            dx: loc,
            {
              if show-ticks { place(tick-alignment, line()) }
              if show-labels {
                let body = rotate(label-style.rotation, reflow: true, label)
                place(label-alignment, dy: label-dy, body)
              }
            },
          )
        })
        .join([]),
    ),
  )
}

#let draw-yaxis-ticks(alignment, show-ticks: true, show-labels: true, ..args) = {
  let (tick-style, label-style, locs, labels) = args.named()
  if labels == () { labels = locs.len() * ("",) }
  set line(..tick-style.line)
  set text(..label-style.text)

  let (tick-alignment, tick-dx) = if tick-style.direction == "in" {
    (if alignment == left { left } else { right }, 0pt)
  } else if tick-style.direction == "out" {
    (if alignment == left { right } else { left }, tick-style.line.length)
  } else if tick-style.direction == "inout" {
    (horizon, tick-style.line.length / 2)
  } else {
    panic("Unknown tick direction '" + tick-style.direction + "'")
  }

  let label-alignment = horizon + if alignment == left { right } else { left }
  let label-dx = label-style.pad + tick-dx
  if alignment == left { label-dx = -label-dx }

  place(
    alignment,
    block(
      height: 100%,
      locs
        .zip(labels)
        .map(tick => {
          let (loc, label) = tick
          if (loc < 0%) or (loc > 100%) { return }
          place(
            dy: loc,
            {
              if show-ticks { place(tick-alignment, line()) }
              if show-labels {
                let body = place(label-alignment, label)
                place(dx: label-dx, rotate(label-style.rotation, body))
              }
            },
          )
        })
        .join([]),
    ),
  )
}
