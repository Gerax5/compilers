class Animal {
	let name;
	let age;

	function speak(): string {
		let animalVar = new Animal();
		return this.name + " makes a sound.";
	}

	function setAge(newAge: integer) {
		this.age = 5;
	}

	function printAge(): string {
		return this.name + " is " + this.age +" years old!";
	}

}

let animalVar = new Animal();