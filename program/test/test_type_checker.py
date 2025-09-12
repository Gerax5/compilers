import os, sys
from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker # type: ignore

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


def test_equiality_expr():
    src = """
        let a: bool = x == y;
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)

    assert not errors.errors

def test_logical_and_expr():
    src = """
    function f(x: boolean, y: boolean): boolean {
        return x && y;
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert not errors.errors

def test_logical_or_expr():
    src = """
    function f(x: boolean, y: boolean): boolean {
        return x || y;
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert not errors.errors

def test_logical_not_expr():
    src = """
    function f(x: boolean): boolean {
        return !x;
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert not errors.errors

#  visitMultiplicativeExpr
def test_mul_int_int():
    src = "function f(): integer { return 2 * 3; }"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert not errors.errors  # 2*3 es int -> OK

def test_mul_int_float_promotes_to_float():
    src = "function f(): float { return 2 * 3.5; }"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert not errors.errors  # promoción a float -> OK

def test_div_int_int_is_float():
    src = "function f(): float { return 5 / 2; }"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert not errors.errors  # tu regla hace / -> float

def test_mod_int_int_ok():
    src = "function f(): integer { return 5 % 2; }"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert not errors.errors  # % entre enteros -> OK

def test_mod_with_float_is_error():
    src = "function f(): integer { return 5.0 % 2; }"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert any("% requiere enteros" in str(e) for e in errors.errors)

# visitTernaryExpr
def test_ternary_basic_int_ok():
    src = """
    function f(): integer { 
        return true ? 1 : 2; 
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert not errors.errors

def test_ternary_numeric_promotion_to_float():
    src = """
    function f(): float { 
        return false ? 1.0 : 2; 
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert not errors.errors

def test_ternary_condition_not_bool_is_error():
    src = """
    function f(): integer { 
        return 1 ? 10 : 20; 
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert errors_contain(errors, "Se esperaba bool")

def test_ternary_incompatible_branches_is_error():
    src = """
    function f(): integer { 
        return true ? 1 : "x"; 
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert errors_contain(errors, "Tipos incompatibles en ternario")

# visitExprNoAssign

def test_expr_no_assign_passthrough_additive():
    src = """
    function f(): integer { 
        return 1 + 2; 
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert not errors.errors

# visitExpression

def test_expression_rule_passthrough_literal():
    src = """
    function f(): integer { 
        return 7; 
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert not errors.errors

# visitPropertyAssignExpr

def test_property_assign_ok():
    src = """
    class C { var x: integer; }
    function f(): void {
        let c: C;
        c.x = 42;
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert not errors.errors

def test_property_assign_wrong_type_error():
    src = """
    class C { var x: integer; }
    function f(): void {
        let c: C;
        c.x = 3.5;   // error: int = float
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert errors_contain(errors, "Asignación incompatible") or errors_contain(errors, "incompatible")

def test_property_assign_missing_property_error():
    src = """
    class C { var x: integer; }
    function f(): void {
        let c: C;
        c.y = 1;     // error: no existe
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert errors_contain(errors, "Propiedad") and errors_contain(errors, "no existe")

# visitWhileStatement

def test_while_condition_bool_ok():
    src = """
    function f(): void {
        let x: integer;
        x = 0;
        while (true) {
            x = x + 1;
        }
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert not errors.errors


def test_while_condition_not_bool_error():
    src = """
    function f(): void {
        while (1) { }
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert errors_contain(errors, "Se esperaba bool, se obtuvo")

# visitDoWhileStatement

def test_do_while_condition_bool_ok():
    src = """
    function f(): void {
        do { } while (true);
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert not errors.errors


def test_do_while_condition_not_bool_error():
    src = """
    function f(): void {
        do { } while (2);
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert errors_contain(errors, "Se esperaba bool")

# visitSwitchStatement

def test_switch_condition_bool_ok_and_break_allowed():
    src = """
    function f(): void {
        switch (true) {
            case true:
                break;   // permitido dentro de switch
            default:
                // nada
        }
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert not errors.errors


def test_switch_condition_not_bool_error():
    src = """
    function f(): void {
        switch (1) {
            default: ;
        }
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert errors_contain(errors, "Se esperaba bool")


def test_switch_continue_is_error():
    src = """
    function f(): void {
        switch (true) {
            case true:
                continue;  // continue no es válido en switch
            default:
                ;
        }
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert errors_contain(errors, "'continue' fuera de un bucle")

# visitSwitchCase

def test_switch_case_expr_bool_ok():
    src = """
    function f(): void {
        switch (true) {
            case false:
                ;
            default: ;
        }
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert not errors.errors


def test_switch_case_expr_not_bool_error():
    src = """
    function f(): void {
        switch (true) {
            case 1:
                ;
            default:
                ;
        }
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert errors_contain(errors, "Se esperaba bool")

# visitDefaultCase

def test_default_case_executes_statements_typechecked():
    src = """
    function f(): void {
        let x: integer;
        switch (true) {
            default:
                x = "hola";  // error: int = string
        }
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert errors_contain(errors, "Asignación incompatible")


# visitTryCatchStatement

def test_try_catch_ok():
    src = """
    function f(): void {
        try { 
            let x: integer; 
            x = 1; 
        } catch (e) { 
            // nada
        }
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert not errors.errors


def test_try_catch_type_error_inside_try_is_reported():
    src = """
    function f(): void {
        try { 
            let x: integer; 
            x = "a";   // debe reportar asignación incompatible
        } catch (e) { 
            // nada
        }
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert errors_contain(errors, "Asignación incompatible")

# visitExpressionStatement

def test_expression_statement_undeclared_identifier_reports_error():
    src = "y;"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert errors_contain(errors, "'y' no declarado")

# visitPrintStatement

def test_print_statement_propagates_inner_expr_errors():
    src = "print(1 + true);"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    # Debe reportar el error del + inválido dentro de print(...)
    assert any("Operación +" in e and "inválida" in e for e in errors.errors)

# visitClassMember

def test_class_member_var_and_method_checked():
    src = """
    class D {
        let x: integer;
        function m(): void { this.x = 1; }
        const k: integer = 5;
    }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    assert not errors.errors


# visitTypeAnnotation

def test_type_annotation_allows_later_assignment():
    src = """
    let a: integer;
    a = 1;
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    # Asignación válida a variable anotada como integer
    assert not errors.errors

# visitInitializer

def test_initializer_infers_type_ok():
    src = "let a = 1;"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert not errors.errors
    assert "a" in stb.globalScope.symbols
    assert stb.globalScope.symbols["a"].ty == Type.INT

def test_initializer_type_mismatch_fails():
    src = 'let a: integer = "hola";'
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    # Debe coincidir con el wording que ya usas en visitVariableDeclaration
    assert errors_contain(errors, "No se puede asignar Type.STRING a Type.INT en 'a'")


def test_class_inheritance_and_method_override():
    src = """
        class A {
            function m(x: int): void {}
        }

        class B: A {
            function m(x: string): void {}
        }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors_contain(errors, "Override inválido de 'm': tipo de parámetro Type.STRING no coincide con Type.INT")

def test_class_inheritance_and_method_override_error():
    src = """
        class A {
            function m(x: int): void {}
        }

        class B: A {
            function m(x: int): string {}
        }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert errors_contain(errors, "Override inválido de 'm': tipo de retorno Type.STRING no coincide con Type.VOID")

def test_class_inheritance_and_method_override_ok():
    src = """
        class A {
            function m(x: int): void {}
        }

        class B: A {
            function m(x: int): void {
                const a: int = x;
            }
        }
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)

    assert not errors.errors
