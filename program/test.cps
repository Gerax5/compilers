class Animal {
  let name: string;

  function constructor(name: string) {
    this.name = name;
  }

  function speak(): string {
    print(this.name + " makes a sound.");
    return this.name + " makes a sound.";
  }
}

let dog: Animal = new Animal("Rex");
print(dog.speak());

