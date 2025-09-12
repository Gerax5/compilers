class Animal {
  let name: string;
  let child : Animal;

  function constructor(name: string) : string {
    this.name = name;
    return "";
  }

  function speak(): string {
    return this.name + " makes a sound.";
  }
}

class Dog {
	function constructor(name: string) {
		return "";
	}
}