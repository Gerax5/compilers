class Color {
  let r: integer;
  let g: integer;
  let b: integer;

  function WithR(r: integer): Color {
      this.r = r;
      return this;
  }

  function WithG(g: integer): Color {
    this.g = g;
    return this;
  }

  function WithB(b: integer): Color {
    this.b = b;
    return this;
  }

// FIXME: This should be valid!
// Fix array assignment.
//  function ToArray(buffer: integer[]) {
//    buffer[0] = r;
//    buffer[1] = g;
//    buffer[2] = b;
//  }
}

let color = new Color();
let buffer = [0,0,0];
color
  .WithR(100)
  .WithG(100)
  .WithB(100);
//  .ToArray(buffer);