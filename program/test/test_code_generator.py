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
    assert any(q["op"] == "newarr" and q["arg1"] == "ref" and q["arg2"] == 5 and q["result"] == "arr_0" for q in cg.quadruples)
    expected_values = [1, 2, 3, 4, 5]
    for idx, val in enumerate(expected_values):
        assert any(
            q["op"] == "[]=" and q["arg1"] == "arr_0" and q["arg2"] == idx and q["result"] == val
            for q in cg.quadruples
        )
    assert any(q["op"] == "=" and q["arg1"] == "arr_0" and q["result"] == "numbers" for q in cg.quadruples)

def test_matrix_declaration_codegen():
    src = "let matrix: integer[][] = [[1, 2], [3, 4]];"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors
    assert any(q["op"] == "newarr" and q["arg1"] == "ref" and q["arg2"] == 2 and q["result"] == "arr_0" for q in cg.quadruples)
    
    expected_inner_arrays = [
        [1, 2],
        [3, 4]
    ]
    
    for i, inner in enumerate(expected_inner_arrays):
        inner_size = len(inner)
        inner_temp = f"arr_{i+1}"
        
        assert any(q["op"] == "newarr" and q["arg1"] == "ref" and q["arg2"] == inner_size and q["result"] == inner_temp for q in cg.quadruples)
        
        for j, val in enumerate(inner):
            assert any(
                q["op"] == "[]=" and q["arg1"] == inner_temp and q["arg2"] == j and q["result"] == val
                for q in cg.quadruples
            )
        
        assert any(q["op"] == "[]=" and q["arg1"] == "arr_0" and q["arg2"] == i and q["result"] == inner_temp for q in cg.quadruples)
    
    assert any(q["op"] == "=" and q["arg1"] == "arr_0" and q["result"] == "matrix" for q in cg.quadruples)

def test_array_element_assignment_codegen():
    src = """
    let arr: integer[] = [1, 2, 3];
    arr[0] = 10;
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors
    assert any(q["op"] == "[]=" and q["arg1"] == "arr" and q["arg2"] == 0 and q["result"] == 10 for q in cg.quadruples)


def test_for_statement_codegen():
    src = """
    for (let i = 0; i < 3; i = i + 1) {
        print(i);
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors, f"Errores de compilación: {errors.errors}"

    quads = cg.quadruples

    assert any(
        q["op"] == "=" and q["arg1"] == 0 and q["result"] == "i"
        for q in quads
    ), "No se generó la asignación inicial i = 0"

    assert any("Lfor_test_" in (q["result"] or "") for q in quads if q["op"] == "label"), "Falta label Lfor_test"
    assert any("Lfor_body_" in (q["result"] or "") for q in quads if q["op"] == "label"), "Falta label Lfor_body"
    assert any("Lfor_incr_" in (q["result"] or "") for q in quads if q["op"] == "label"), "Falta label Lfor_incr"
    assert any("Lfor_end_" in (q["result"] or "") for q in quads if q["op"] == "label"), "Falta label Lfor_end"

    assert any(
        q["op"] == "<" and q["arg1"] == "i" and q["arg2"] == 3
        for q in quads
    ), "No se generó la comparación i < 3"

    assert any(
        q["op"] == "ifFalse" and "Lfor_end_" in str(q["result"])
        for q in quads
    ), "Falta el salto condicional ifFalse hacia Lfor_end"

    assert any(
        q["op"] == "print" and q["arg1"] == "i"
        for q in quads
    ), "No se generó print(i)"

    assert any(
        q["op"] == "+" and q["arg1"] == "i" and q["arg2"] == 1
        for q in quads
    ), "No se generó i + 1"

    assert any(
        q["op"] == "=" and isinstance(q["arg1"], str) and q["arg1"].startswith("t") and q["result"] == "i"
        for q in quads
    ), "No se reasignó el incremento a i"

    assert any(
        q["op"] == "goto" and "Lfor_test_" in str(q["result"])
        for q in quads
    ), "Falta salto goto hacia Lfor_test"

    assert any(
        q["op"] == "label" and "Lfor_end_" in q["result"]
        for q in quads
    ), "Falta etiqueta final Lfor_end"


def test_foreach_codegen():
    src = """
    const arr = [5,1];
    foreach (x in arr) {
        print(x);
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors, f"Errores en type checker: {errors.errors}"

    quads = cg.quadruples

    # --- Creación del arreglo ---
    assert any(q["op"] == "newarr" and q["arg1"] == "ref" and q["arg2"] == 2 for q in quads)
    assert any(q["op"] == "[]=" and q["arg2"] == 0 and q["result"] == 5 for q in quads)
    assert any(q["op"] == "[]=" and q["arg2"] == 1 and q["result"] == 1 for q in quads)
    assert any(q["op"] == "=" and q["arg1"] == "arr_0" and q["result"] == "arr" for q in quads)

    # --- Inicio del foreach ---
    assert any(q["op"] == "len" and q["arg1"] == "arr" for q in quads), "Debe calcularse la longitud del arreglo"
    assert any(q["op"] == "<" and q["arg1"] == "t1" for q in quads), "Debe comparar índice con longitud"
    assert any(q["op"] == "label" and "foreach_test" in q["result"] for q in quads), "Debe existir label de test"
    assert any(q["op"] == "label" and "foreach_body" in q["result"] for q in quads), "Debe existir label de cuerpo"

    # --- Cuerpo del foreach ---
    assert any(q["op"] == "[]" and q["arg1"] == "arr" for q in quads), "Debe acceder al elemento actual"
    assert any(q["op"] == "=" and q["result"] == "x" for q in quads), "Debe asignar el valor a la variable de iteración"
    assert any(q["op"] == "print" and q["arg1"] == "x" for q in quads), "Debe imprimir el valor actual"

    # --- Incremento y bucle ---
    assert any(q["op"] == "+" and q["arg1"] == "t1" and q["arg2"] == 1 for q in quads), "Debe incrementar el índice"
    assert any(q["op"] == "goto" and "foreach_test" in q["result"] for q in quads), "Debe saltar al inicio del foreach"
    assert any(q["op"] == "label" and "foreach_end" in q["result"] for q in quads), "Debe existir label de fin del foreach"

    op_order = [q["op"] for q in quads]
    expected_ops = ["newarr", "[]=", "[]=", "=", "=", "label", "len", "<", "ifFalse", "label", "[]", "=", "print", "+", "=", "goto", "label"]
    for op in expected_ops:
        assert op in op_order, f"Falta operación esperada: {op}"

# While
# ----- Exito
def test_while_codegen_success():
    src = """
    let i: integer = 0;
    while (i < 3) {
        print(i);
        i = i + 1;
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors

    quads = cg.quadruples
    assert any(q["op"] == "label" and "Lwhile_test_" in q["result"] for q in quads)
    assert any(q["op"] == "label" and "Lwhile_body_" in q["result"] for q in quads)
    assert any(q["op"] == "label" and "Lwhile_end_"  in q["result"] for q in quads)
    assert any(q["op"] == "<" and q["arg1"] == "i" and q["arg2"] == 3 for q in quads)
    assert any(q["op"] == "ifFalse" and "Lwhile_end_" in str(q["result"]) for q in quads)
    assert any(q["op"] == "print" and q["arg1"] == "i" for q in quads)
    assert any(q["op"] == "+" and q["arg1"] == "i" and q["arg2"] == 1 for q in quads)
    assert any(q["op"] == "goto" and "Lwhile_test_" in str(q["result"]) for q in quads)

# ----- Fallo
def test_while_condition_not_bool_failure():
    src = """
    while (42) { print(1); }   // int no es bool
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors.errors, "Se esperaba error de tipo en condición de while"

# do while
# ----- Exito
def test_dowhile_codegen_success():
    src = """
    let i: integer = 0;
    do {
        print(i);
        i = i + 1;
    } while (i < 2);
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors

    quads = cg.quadruples
    assert any(q["op"] == "label" and "Ldowhile_body_" in q["result"] for q in quads)
    assert any(q["op"] == "label" and "Ldowhile_cond_" in q["result"] for q in quads)
    assert any(q["op"] == "label" and "Ldowhile_end_"  in q["result"] for q in quads)
    assert any(q["op"] == "ifTrue" and "Ldowhile_body_" in str(q["result"]) for q in quads)

# ----- Fallo
def test_dowhile_condition_not_bool_failure():
    src = """
    do { print(1); } while (2);   // int no es bool
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors.errors, "Se esperaba error de tipo en condición de do-while"

# Try / Catch
# ----- Exito
def test_try_catch_codegen_success():
    src = """
    try {
        print(1);
    } catch (e) {
        print(e);
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors

    quads = cg.quadruples
    assert any(q["op"] == "trybegin" for q in quads)
    assert any(q["op"] == "tryend"   for q in quads)
    assert any(q["op"] == "label" and "Lcatch_"    in q["result"] for q in quads)
    assert any(q["op"] == "label" and "Ltry_end_"  in q["result"] for q in quads)
    assert any(q["op"] == "=" and q["arg1"] == "exception" and q["result"] == "e" for q in quads)

# Continue
# ----- Exito
def test_continue_in_loop_codegen_success():
    src = """
    let i: integer = 0;
    while (i < 2) {
        continue;
        i = i + 1;   // no debería ejecutarse si continue salta
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors

    quads = cg.quadruples
    # continue en while salta a Lwhile_test_ (tu pila mapea continue → Ltest)
    assert any(q["op"] == "goto" and "Lwhile_test_" in str(q["result"]) for q in quads)


# ----- Fallo
def test_continue_outside_loop_failure():
    src = """
    continue;
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors.errors, "Se esperaba error por 'continue' fuera de bucle"

# Break
# ----- Exito
def test_break_in_loop_codegen_success():
    src = """
    let i: integer = 0;
    while (i < 10) {
        break;
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors

    quads = cg.quadruples
    # break en while debe saltar a Lwhile_end_
    assert any(q["op"] == "goto" and "Lwhile_end_" in str(q["result"]) for q in quads)

# ----- Fallo
def test_break_outside_loop_or_switch_failure():
    src = """
    break;
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors.errors, "Se esperaba error por 'break' fuera de bucle o switch"

# Switch
# ----- Exito
def test_switch_basic_codegen_success():
    src = """
    switch (true) {
        case true:
            print(1);
            break;
        default:
            print(2);
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors

    quads = cg.quadruples
    assert any(q["op"] == "label" and "Lswitch_end_" in q["result"] for q in quads)
    # Debe existir la comparación == entre scrutinee y case
    assert any(q["op"] == "==" for q in quads)
    # Y un ifTrue saltando a un Lcase_
    assert any(q["op"] == "ifTrue" and str(q["result"]).startswith("Lcase_") for q in quads)
    # El break debe saltar a Lswitch_end_
    assert any(q["op"] == "goto" and "Lswitch_end_" in str(q["result"]) for q in quads)

def test_switch_no_default_fallthrough_success():
    src = """
    let x: boolean = true;
    switch (x) {
        case false:
            print(0);
        case true:
            print(1);
            break;
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree)

    assert not errors.errors

    quads = cg.quadruples
    # Debe existir al menos un label de case y el end
    assert any(q["op"] == "label" and "Lcase_" in q["result"] for q in quads)
    assert any(q["op"] == "label" and "Lswitch_end_" in q["result"] for q in quads)


# ----- Fallo
def test_switch_incompatible_case_type_failure():
    src = """
    switch (true) {
        case 1:        // incompatible con bool
            print(1);
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors.errors, "Se esperaba error por case incompatible con switch(bool)"

