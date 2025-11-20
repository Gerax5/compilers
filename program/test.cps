function makeAdder(x: integer): integer {
  return x + 1;
}

let addFive: integer = (makeAdder(1));

if (addFive > 5) {
  print("Greater than 5");
} else {
  print("5 or less");
}

while (addFive < 10) {
  addFive = addFive + 1;
}

do {
  print("Result is now "+addFive);
  addFive = addFive - 1;
} while (addFive > 7);
