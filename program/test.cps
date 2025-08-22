const PI: integer = 314;
let greeting: string = "Hello, Compiscript!";

let numbers: integer[] = [1, 2, 3, 4, 5];

function makeAdder(x: integer, y: interger): integer {
  return x + 1;
}

class Animal {
  let name: string;

  function constructor(name: string) {
    this.name = name;
  }

  function speak(): string {
    return this.name + " makes a sound.";
  }
}

foreach (n in numbers) {
  if (n == 3) {
    continue;
  }
  print("Number: " + n);
  if (n > 4) {
    break;
  }
}