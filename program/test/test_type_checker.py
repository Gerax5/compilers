import os, sys
from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker

# Asegura que Python vea los módulos en /program
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser

from src.utils.Errors import Error
from src.symbolTable.SymbolTableBuilder import SymbolTableBuilder
from src.typeChecker.TypeChecker import TypeChecker
from src.utils.Types import Type, ArrayType


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

def errors_contain(errors, substr):
    return any(substr in e for e in errors.errors)


# ---------- tests ----------

def test_return_ok_with_identifier():
    src = """
    function makeAdder(x: integer): integer {
      return x;
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert not errors.errors

def test_return_type_mismatch_string_in_int_fn():
    src = """
    function f(x: integer): integer {
      return "x + 1";
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors_contain(errors, "return: esperado Type.INT")
    assert errors_contain(errors, "STRING")

def test_additive_numeric_promotes_to_float():
    src = """
    function f(): float { return 1 + 2.5; }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert not errors.errors 

def test_additive_string_concat_is_string():
    src = """
    function f(): string { return "a" + 1; }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert not errors.errors

def test_var_assignment_type_mismatch():
    src = """
    let a: integer = "hola";
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors_contain(errors, "No se puede asignar Type.STRING a Type.INT en 'a'")

def test_const_cannot_be_assigned():
    src = """
    const x: integer = 1;
    function g(): void {
      x = 2;
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors_contain(errors, "No se puede asignar a const 'x'")

def test_undeclared_identifier_in_return():
    src = """
    function f(): integer { return y; }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors_contain(errors, "'y' no declarado")

def test_array_literal_and_annotation_ok():
    src = """
    let nums: integer[] = [1, 2, 3];
    let numsF: float[] = [1, 2, 3];   // int[] -> asignable a float[]
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert not errors.errors

def test_class_declaration():
    src = """
    class C {
        let x: integer;
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert not errors.errors

def test_class_this_reference():
    src = """
    class C {
        let x: integer;
        function m(): void {
            this.x = 1;
        }
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert not errors.errors

def test_class_this_outside_class():
    src = """
    function f(): void {
        this.x = 1;
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors_contain(errors, "Uso de 'this' fuera de una clase")

def test_call_function_with_string_argument():
    src = """
    function f(x: integer): integer {
        return x;
    }
    
    f("5");
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors_contain(errors, "Arg 1 de 'f': esperado Type.INT, recibió Type.STRING")

def test_call_function_with_no_arguments():
    src = """
    function f(x: integer): integer {
        return 42;
    }

    f();
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors_contain(errors, "'f' espera 1 args, recibió 0")

def test_assignment_variable_function_call_with_diff_return_type():
    src = """
    function f(): integer {
        return 42;
    }

    let x: string = f();
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors_contain(errors, "No se puede asignar Type.INT a Type.STRING en 'x'")

def test_array_indexing():
    src = """
    let a: integer[] = [1, 2, 3];
    let b: integer = a[0];
    let c: float = a[1];
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert not errors.errors

def test_assignment_array_element():
    src = """
    let a: integer[] = [1, 2, 3];
    a[0] = 4;
    a[1] = "hola";
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors_contain(errors, "Asignación incompatible en arreglo: Type.INT = Type.STRING")

def test_class_inheritance():
    src = """
    class A {
        function m(): void {}
    }

    class B: A {
        function n(): void {
            this.m();
        }
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert not errors.errors

def test_initialization_class_instance():
    src = """
    class C {
        let x: integer;
    }

    let c: C = new C();
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert not errors.errors

def test_initialization_class_instance_type_mismatch():
    src = """
    class C {
        let x: integer;
    }

    let c: C = new C();
    c.x = "hello";
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors_contain(errors, "Asignación incompatible a 'x': Type.INT = Type.STRING")

def test_initialization_class_with_no_args():
    src = """
    class C {
        let x: integer;
        function constructor(args: integer) {
            this.x = args;
        }
    }

    let c: C = new C();
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors_contain(errors, "constructor de C espera 1 args, recibió 0")

def test_simple_bool_expr():
    src = """
    function f(x: integer): boolean {
        return x > 0;
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert not errors.errors

def test_assignment_bool_var():
    src = """
    let a: boolean = 1 < 2;
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert not errors.errors
