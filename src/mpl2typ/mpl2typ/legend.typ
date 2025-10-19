#import "draw.typ"

#let line2d(stroke: none, marker: none, ..style) = {
  let (handle-length, ..) = style.named()
  let w = handle-length / 2
  if stroke != none { draw.place((50%, 50%), line(start: (-w, 0pt), end: (w, 0pt), stroke: stroke)) }
  if marker != none { draw.place((50%, 50%), marker) }
}

#let errorbar(data: none, caps: none, bars: none, ..style) = {
  let (handle-length, xerr-size, yerr-size, ..) = style.named()
  if caps != none {
    let cap-left = caps.at("x", default: caps.at("left", default: none))
    let cap-right = caps.at("x", default: caps.at("right", default: none))
    let cap-bottom = caps.at("y", default: caps.at("bottom", default: none))
    let cap-top = caps.at("y", default: caps.at("top", default: none))
    draw.place((50% - xerr-size, 50%), cap-left)
    draw.place((50% + xerr-size, 50%), cap-right)
    draw.place((50%, 50% - yerr-size), cap-bottom)
    draw.place((50%, 50% + yerr-size), cap-top)
  }

  if bars != none {
    let stroke-x = bars.at("x", default: none)
    let stroke-y = bars.at("y", default: none)
    if stroke-x != none {
      let line-x = std.line(start: (-xerr-size, 0pt), end: (xerr-size, 0pt), stroke: stroke-x)
      draw.place((50%, 50%), line-x)
    }
    if stroke-y != none {
      let line-y = std.line(start: (0pt, -yerr-size), end: (0pt, yerr-size), angle: 90deg, stroke: stroke-y)
      draw.place((50%, 50%), line-y)
    }
  }

  if data != none { line2d(..data, handle-length: handle-length) }
}

#let legend(
  location: top + left,
  title: none,
  columns: 1,
  marker-first: true,
  row-gutter: 0.5em,
  item-gutter: 0.8em,
  column-gutter: 2.0em,
  handle-length: 2.0em,
  handle-height: 0.7em,
  xerr-size: 0.5em,
  yerr-size: 0.5em,
  inset: 0.4em,
  outset: 0.5em,
  fill: none,
  stroke: none,
  frame: block,
  ..items,
) = {
  let handle-style = (
    handle-length: handle-length,
    handle-height: handle-height,
    xerr-size: xerr-size,
    yerr-size: yerr-size,
  )
  let legend-handle = block.with(width: handle-length, height: handle-height, inset: 0em, outset: 0em)
  items = items
    .pos()
    .map(item => {
      let item = (
        legend-handle(item.at("handle")(..handle-style)),
        item.at("label"),
      )
      if marker-first { item } else { item.rev() }
    })
    .flatten()

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

  columns = calc.min(columns, calc.quo(items.len(), 2))
  column-gutter = ((item-gutter,) * columns).intersperse(column-gutter)
  let grid = grid.with(
    align: horizon + left,
    columns: 2 * columns,
    column-gutter: column-gutter,
    row-gutter: row-gutter,
    inset: 0em,
  )

  let frame = frame.with(
    stroke: stroke,
    fill: fill,
    inset: inset,
  )

  if title != none { items.insert(0, grid.cell(y: 0, colspan: 2 * columns, align(center, title))) }
  std.place(alignment, dx: dx, dy: dy, frame(grid(..items)))
}
