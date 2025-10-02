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

# def test_simple_addition_codegen():
#     src = "function f(): integer { return 1 + 2; }"
#     parser, tree = parse_src(src)
#     stb, errors = build_symbols(tree)
#     tc, errors  = type_check(stb, errors, parser, tree)
#     cg = gen_code(tree)

#     assert not errors.errors
#     assert any(q["op"] == "+" for q in cg.quadruples)

# def test_class_and_method_codegen():
#     src = """
#     class Persona {
#         var nombre;
#         function saludar() {
#             print("Hola " + this.nombre);
#         }
#     }
#     """
#     parser, tree = parse_src(src)
#     stb, errors = build_symbols(tree)
#     tc, errors  = type_check(stb, errors, parser, tree)
#     cg = gen_code(tree)

#     # Revisar que haya "class" y "getprop"
#     ops = [q["op"] for q in cg.quadruples]
#     assert "class" in ops
#     assert "getprop" in ops
