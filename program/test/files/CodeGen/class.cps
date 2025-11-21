class Point {
    var x: integer;
    var y: integer;

    function constructor(x: integer, y: integer) {
        this.x = x;
        this.y = y;
    }
}

const p: Point = new Point(10, 20);
print(p.x);