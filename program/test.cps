class A {
    function m(x: int): void {}
}

class B: A {
    function m(x: int): void {
        const a: int = x;
    }
}