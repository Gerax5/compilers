class Animal {
  let name: string;

  function constructor(name: string) {
    this.name = name;
  }

  function speak(): string {
    print(this.name);
  }
}

let dog: Animal = new Animal("Rex");
dog.speak();