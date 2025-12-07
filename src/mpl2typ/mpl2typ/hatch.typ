#let _hatch-horizontal(n, stroke, density) = {
  density = density * 2
  for i in range(n * density + 1) {
    let y = i * 100% / (n * density)
    (line(start: (0%, y), end: (100%, y), stroke: stroke),)
  }
}

#let _hatch-vertical(n, stroke, density) = {
  density = density * 2
  for i in range(n * density + 1) {
    let x = i * 100% / (n * density)
    (line(start: (x, 0%), end: (x, 100%), stroke: stroke),)
  }
}

#let _hatch-north-east(n, stroke, density) = {
  (line(start: (0%, 100%), end: (100%, 0%), stroke: stroke),)
  for i in range(n * density) {
    let d = (i + 1) * 100% / (n * density)
    (
      line(start: (0% - d, 100%), end: (100%, 0% - d), stroke: stroke),
      line(start: (0%, 100% + d), end: (100% + d, 0%), stroke: stroke),
    )
  }
}

#let _hatch-south-east(n, stroke, density) = {
  (line(start: (0%, 0%), end: (100%, 100%), stroke: stroke),)
  for i in range(n * density) {
    let d = (i + 1) * 100% / (n * density)
    (
      line(start: (0%, 0% - d), end: (100% + d, 100%), stroke: stroke),
      line(start: (0% - d, 0%), end: (100%, 100% + d), stroke: stroke),
    )
  }
}

#let _hatch-shape(shape, n, size, density) = {
  density = density * 2
  let ax = size.at(0) / density
  let ay = size.at(1) / density

  for row in range(n * density) {
    let dy = (row + 0.5) * ay / n
    // Every second row is shifted by half a column
    for col in range(n * density + calc.rem(row, 2)) {
      let dx = (col + 0.5 * calc.rem(row + 1, 2)) * ax / n
      (place(dx: dx, dy: dy, shape),)
    }
  }
}

// The default size (24pt, 24pt) and the default density 2 match the default of
// matplotlib where the density is 6 in a unit square of size (72pt, 72pt).
#let hatch(pattern: "", stroke: none, fill: none, size: (24pt, 24pt), density: 2, scale: 1) = {
  // the density is rescaled for everything but the diagonal hatches
  size = size.map(s => s * 2)

  let n-horizontal = pattern.matches("-").len() + pattern.matches("+").len()
  let n-vertical = pattern.matches("|").len() + pattern.matches("+").len()
  let n-north-east = pattern.matches("/").len() + pattern.matches("X").len()
  let n-south-east = pattern.matches("\\").len() + pattern.matches("X").len()
  let n-small-circles = pattern.matches("o").len()
  let n-large-circles = pattern.matches("O").len()
  let n-small-filled-circles = pattern.matches(".").len()

  let children = ()
  if fill != none { children.push(rect(width: size.at(0), height: size.at(1), fill: fill)) }

  if n-horizontal > 0 { children += _hatch-horizontal(n-horizontal, stroke, density) }
  if n-vertical > 0 { children += _hatch-vertical(n-vertical, stroke, density) }
  if n-north-east > 0 { children += _hatch-north-east(n-north-east, stroke, density) }
  if n-south-east > 0 { children += _hatch-south-east(n-south-east, stroke, density) }

  // The circle radii are computed from 12pt * size in matplotlib/hatch.py
  if n-small-circles > 0 {
    let circle = place(center + horizon, dx: 0pt, dy: 0pt, circle(radius: 2.4pt * scale, stroke: stroke))
    children += _hatch-shape(circle, n-small-circles, size, density)
  }
  if n-large-circles > 0 {
    let circle = place(center + horizon, dx: 0pt, dy: 0pt, circle(radius: 4.8pt * scale, stroke: stroke))
    children += _hatch-shape(circle, n-large-circles, size, density)
  }
  if n-small-filled-circles > 0 {
    let circle = place(center + horizon, dx: 0pt, dy: 0pt, circle(radius: 1.2pt * scale, stroke: stroke, fill: black))
    children += _hatch-shape(circle, n-small-filled-circles, size, density)
  }

  tiling(
    size: size,
    children.map(child => place(child)).join([]),
  )
}
