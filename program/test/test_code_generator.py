import os, sys
from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker # type: ignore

# Asegura que Python vea los módulos en /program
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from src.utils.Errors import Error
from src.symbolTable.SymbolTableBuilder import SymbolTableBuilder
from src.typeChecker.TypeChecker import TypeChecker
from src.utils.Temp import TempManager
from src.codeGenerator.CodeGenerator import CodeGenerator

# ---------- helpers ----------
def parse_src(src: str):
    inp = InputStream(src)
    lex = CompiscriptLexer(inp)
    ts  = CommonTokenStream(lex)
    parser = CompiscriptParser(ts)
    tree = parser.program()
    return parser, tree

def build_symbols(tree):
    errors = Error()
    stb = SymbolTableBuilder(errors)
    ParseTreeWalker().walk(stb, tree)
    return stb, errors

def type_check(stb, errors, parser, tree):
    tc = TypeChecker(stb.scopes, stb.globalScope, errors, parser)
    tc.visit(tree)
    return tc, errors

def gen_code(tree):
    temp_manager = TempManager()
    cg = CodeGenerator(temp_manager)
    cg.visit(tree)
    return cg

# ---------- tests ----------
def test_simple_var_decl_codegen():
    src = "let x: integer = 42;"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors
    assert any(q["op"] == "=" and q["arg1"] == 42 and q["result"] == "x" for q in cg.quadruples)

def test_arithmetic_codegen():
    src = "let x: integer = 4 + 2 * 2 + 4 * 2;"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors

    last = cg.quadruples[-1]
    assert last["op"] == "="
    assert last["result"] == "x"

    muls = [q for q in cg.quadruples if q["op"] == "*"]
    assert len(muls) == 2
    assert {"arg1": 2, "arg2": 2} in [{ "arg1": q["arg1"], "arg2": q["arg2"] } for q in muls]
    assert {"arg1": 4, "arg2": 2} in [{ "arg1": q["arg1"], "arg2": q["arg2"] } for q in muls]

    pluses = [q for q in cg.quadruples if q["op"] == "+"]
    assert len(pluses) == 2

def test_create_function_codegen():
    src = """
    function add(a: integer, b: integer): integer {
        return a + b;
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors
    assert any(q["op"] == "label" and q["result"] == "func_add" for q in cg.quadruples)
    assert any(q["op"] == "return" for q in cg.quadruples)

def test_function_call_codegen():
    src = """
    function add(a: integer, b: integer): integer {
        return a + b;
    }
    let result: integer = add(2, 3);
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors
    assert any(q["op"] == "call" and q["arg1"] == "add" for q in cg.quadruples)
    assert any(q["op"] == "=" and q["result"] == "result" for q in cg.quadruples)

def test_class_codegen():
    src = """
    class Point {
        var x: integer;
        var y: integer;

        function constructor(x: integer, y: integer) {
            this.x = x;
            this.y = y;
        }
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors
    assert any(q["op"] == "class" and q["result"] == "Point" for q in cg.quadruples)
    assert any(q["op"] == "setprop" and q["arg1"] == "this" and q["arg2"] == "x" for q in cg.quadruples)
    assert any(q["op"] == "setprop" and q["arg1"] == "this" and q["arg2"] == "y" for q in cg.quadruples)

def test_constant_declaration_codegen():
    src = "const PI: float = 3.14;"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors
    assert any(q["op"] == "=" and q["arg1"] == 3.14 and q["result"] == "PI" for q in cg.quadruples)

def test_class_call_codegen():
    src = """
    class Point {
        var x: integer;
        var y: integer;

        function constructor(x: integer, y: integer) {
            this.x = x;
            this.y = y;
        }
    }

    const p: Point = new Point(10, 20);
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors
    assert any(q["op"] == "new" and q["arg1"] == "Point" for q in cg.quadruples)
    assert any(q["op"] == "=" and q["result"] == "p" for q in cg.quadruples)

def test_string_literal_codegen():
    src = 'let greeting: string = "Hello, World!";'
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors
    assert any(q["op"] == "=" and q["arg1"] == '"Hello, World!"' and q["result"] == "greeting" for q in cg.quadruples)

def test_boolean_literal_codegen():
    src = "let isActive: boolean = true;"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors
    assert any(q["op"] == "=" and q["arg1"] == 1 and q["result"] == "isActive" for q in cg.quadruples)

def test_null_literal_codegen():
    src = "let nothing = null;"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors
    assert any(q["op"] == "=" and q["arg1"] == "null" and q["result"] == "nothing" for q in cg.quadruples)

def test_array_declaration_codegen():
    src = "let numbers: integer[] = [1, 2, 3, 4, 5];"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors
    assert any(q["op"] == "newarr" and q["arg1"] == "ref" and q["arg2"] == 5 and q["result"] == "t1" for q in cg.quadruples)
    expected_values = [1, 2, 3, 4, 5]
    for idx, val in enumerate(expected_values):
        assert any(
            q["op"] == "[]=" and q["arg1"] == "t1" and q["arg2"] == idx and q["result"] == val
            for q in cg.quadruples
        )
    assert any(q["op"] == "=" and q["arg1"] == "t1" and q["result"] == "numbers" for q in cg.quadruples)

def test_matrix_declaration_codegen():
    src = "let matrix: integer[][] = [[1, 2], [3, 4]];"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors
    assert any(q["op"] == "newarr" and q["arg1"] == "ref" and q["arg2"] == 2 and q["result"] == "t1" for q in cg.quadruples)
    
    expected_inner_arrays = [
        [1, 2],
        [3, 4]
    ]
    
    for i, inner in enumerate(expected_inner_arrays):
        inner_size = len(inner)
        inner_temp = f"t2"
        
        assert any(q["op"] == "newarr" and q["arg1"] == "ref" and q["arg2"] == inner_size and q["result"] == inner_temp for q in cg.quadruples)
        
        for j, val in enumerate(inner):
            assert any(
                q["op"] == "[]=" and q["arg1"] == inner_temp and q["arg2"] == j and q["result"] == val
                for q in cg.quadruples
            )
        
        assert any(q["op"] == "[]=" and q["arg1"] == "t1" and q["arg2"] == i and q["result"] == inner_temp for q in cg.quadruples)
    
    assert any(q["op"] == "=" and q["arg1"] == "t1" and q["result"] == "matrix" for q in cg.quadruples)