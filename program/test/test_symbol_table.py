# tests/test_symbol_table.py
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker

# Ajusta estos imports a tu layout real
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from src.utils.Errors import Error
from src.symbolTable.SymbolTableBuilder import SymbolTableBuilder
from src.utils.Types import Type, ArrayType

def parse_and_build(src: str):
    input_stream = InputStream(src)
    lexer = CompiscriptLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = CompiscriptParser(stream)
    tree = parser.program()

    errors = Error()
    stb = SymbolTableBuilder(errors)
    ParseTreeWalker().walk(stb, tree)
    return stb, errors, parser, tree

def find_scope_of_ctx(stb, ctx_name: str):
    for ctx, sc in stb.scopes.items():
        if ctx.__class__.__name__ == ctx_name:
            return sc, ctx
    return None, None

# TEST

def test_const_and_var_declared():
    src = """
        const PI: integer = 314;
        let greeting: string = "hola";
    """
    stb, errors, parser, tree = parse_and_build(src)

    assert "PI" in stb.globalScope.symbols
    assert "greeting" in stb.globalScope.symbols

    pi = stb.globalScope.symbols["PI"]
    g  = stb.globalScope.symbols["greeting"]

    assert getattr(pi, "is_const", True) is True
    assert pi.ty == Type.INT
    assert g.ty == Type.STRING

    assert len(errors.errors) == 0

def test_redeclaration_reports_errors():
    src = """
        const PI: integer = 314;
        const PI: integer = 100;
        let a: integer = 1;
        let a: integer = 2;
    """
    _, errors, *_ = parse_and_build(src)
    assert any("Constant 'PI' redeclared" in e for e in errors.errors)
    assert any("Variable 'a' redeclared" in e for e in errors.errors)

def test_function_decl_params_and_scope():
    src = """
        function add(x: integer, y: float): float {
            return x + y;
        }
    """
    stb, errors, *_ = parse_and_build(src)

    assert "add" in stb.globalScope.symbols
    fn = stb.globalScope.symbols["add"]
    assert fn.kind == "func"
    assert fn.ty == Type.FLOAT
    assert len(fn.params) == 2
    assert fn.params[0].name == "x" and fn.params[0].ty == Type.INT
    assert fn.params[1].name == "y" and fn.params[1].ty == Type.FLOAT

    fscope, _ = find_scope_of_ctx(stb, "FunctionDeclarationContext")
    assert fscope is not None
    assert "x" in fscope.symbols and "y" in fscope.symbols
    assert len(errors.errors) == 0

def test_class_decl_creates_class_scope_and_this():
    src = """
        class Animal {
            let name: string;
            function constructor(name: string) {
                this.name = name;
            }
        }
    """
    stb, errors, *_ = parse_and_build(src)

    assert "Animal" in stb.globalScope.symbols
    cls = stb.globalScope.symbols["Animal"]
    assert cls.kind == "class"

    class_scope, _ = find_scope_of_ctx(stb, "ClassDeclarationContext")
    assert class_scope is not None
    assert "this" in class_scope.symbols
    assert "name" in class_scope.symbols

def test_block_creates_scope_and_local_var_not_global():
    src = """
        {
            let a: integer = 1;
        }
    """
    stb, errors, *_ = parse_and_build(src)

    assert "a" not in stb.globalScope.symbols

    found = False
    for ctx, sc in stb.scopes.items():
        if ctx.__class__.__name__ == "BlockContext" and "a" in sc.symbols:
            found = True
            break
    assert found
    assert len(errors.errors) == 0

def test_foreach_creates_scope_and_iterator_symbol():
    src = """
        let numbers: integer[] = [1,2,3];
        foreach (n in numbers) {
            print(n);
        }
    """
    stb, errors, *_ = parse_and_build(src)
    fe_scope, _ = find_scope_of_ctx(stb, "ForeachStatementContext")
    assert fe_scope is not None
    assert "n" in fe_scope.symbols 
    assert len(errors.errors) == 0

def test_for_creates_scope():
    src = """
        for (let i: integer = 0; i < 3; i = i + 1) {
            print(i);
        }
    """
    stb, errors, *_ = parse_and_build(src)
    for_scope, _ = find_scope_of_ctx(stb, "ForStatementContext")
    assert for_scope is not None
    assert len(errors.errors) == 0

def test_while_and_do_while_balance_depth():
    src = """
        let x: integer = 0;
        while (x < 3) { x = x + 1; }
        do { x = x + 1; } while (x < 6);
    """
    stb, errors, *_ = parse_and_build(src)
    # Al finalizar el walk, loop_depth vuelve a 0
    assert stb.loop_depth == 0
    assert len(errors.errors) == 0

def test_array_type_annotation_1d_and_2d():
    src = """
        let a: integer[] = [1,2,3];
        let m: float[][] = [[1.0,2.0],[3.0,4.0]];
    """
    stb, errors, *_ = parse_and_build(src)

    a = stb.globalScope.symbols["a"].ty
    m = stb.globalScope.symbols["m"].ty

    assert isinstance(a, ArrayType)
    assert a.base == Type.INT and a.dimensions == 1

    assert isinstance(m, ArrayType)
    assert m.base == Type.FLOAT and m.dimensions == 2

    assert len(errors.errors) == 0