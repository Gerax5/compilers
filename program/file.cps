

let numbers: integer[] = [1, 2, 3, 4, 5, 6];

function makeAdder(x: integer): integer {
  return x + 1;
}

let addFive: integer = (makeAdder(5));
print("\n5 + 1 = " + addFive);
if (addFive > 5) {
  print("\nGreater than 5");
} else {
  print("\n5 or less");
}

while (addFive < 10) {
  addFive = addFive + 1;
}

do {
  print("\nResult is now " + addFive);
  addFive = addFive - 1;
} while (addFive > 7);

for (let i: integer = 0; i < 3; i = i + 1) {
  print("\nLoop index: " + i);
}

foreach (n in numbers) {
  if (n == 3) {
    continue;
  }
  print("\nNumber: " + n);
  if (n > 4) {
    break;
  }
}

switch (addFive) {
  case 7:
    print("\nIt's seven");
  case 6:
    print("\nIt's six");
  default:
    print("\nSomething else");
}

try {
  let risky: integer = numbers[10];
  print("\nRisky access: " + risky);
} catch (err) {
  print("\nCaught an error: " + err);
}