function makeAdder(x: integer): integer {
  return x + 1;
}

let addFive: integer = (makeAdder(5));
print("5 + 1 = " + addFive);

function sayHelloToFriend(x: string) {
  print("\nHOLA AMIGO "+ x)
}

sayHelloToFriend();