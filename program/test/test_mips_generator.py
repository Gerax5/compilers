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
from src.mipsGenerator.MipsGenerator import MIPSGenerator

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

def gen_code(tree, symbol_table):
    temp_manager = TempManager()
    cg = CodeGenerator(temp_manager, symbol_table)
    cg.visit(tree)
    return cg

def gen_mips(cg, symbol_table):
    mg = MIPSGenerator(cg.quadruples, symbol_table)
    code = mg.generate()
    return code

# ---------- tests ----------
def test_mips_assign_integer():
    src = "const a = 5;"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg = gen_code(tree, stb.globalScope.symbols)
    code = gen_mips(cg, stb.globalScope.symbols)

    assert ".data" in code
    assert "var_a: .word 0" in code
    assert "li $t0, 5" in code
    assert "sw $t0, var_a" in code

def test_let_assign_integer():
    src = "let a = 10;"
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg =gen_code(tree, stb.globalScope.symbols)
    code = gen_mips(cg, stb.globalScope.symbols)

    assert ".data" in code
    assert "var_a: .word 0" in code
    assert "li $t0, 10" in code
    assert "sw $t0, var_a" in code

def test_mips_assign_variable():
    src = """
    let a = 5; 
    let b = a;
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg =gen_code(tree, stb.globalScope.symbols)
    code = gen_mips(cg, stb.globalScope.symbols)

    assert ".data" in code
    assert "var_a: .word 0" in code
    assert "var_b: .word 0" in code
    assert "li $t0, 5" in code
    assert "sw $t0, var_a" in code
    assert "lw $t0, var_a" in code
    assert "sw $t0, var_b" in code

def test_string_literal_handling():
    src = 'print("Hello, World!");'
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg =gen_code(tree, stb.globalScope.symbols)
    code = gen_mips(cg, stb.globalScope.symbols)

    assert ".data" in code
    assert 'str0: .asciiz "Hello, World!"' in code
    assert 'la $a0, str0' in code
    assert 'li $v0, 4' in code
    assert 'syscall' in code

def test_variable_printing():
    src = """
    let a = 42;
    print(a);
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg =gen_code(tree, stb.globalScope.symbols)
    code = gen_mips(cg, stb.globalScope.symbols)

    assert ".data" in code
    assert "var_a: .word 0" in code
    assert "li $t0, 42" in code
    assert "sw $t0, var_a" in code
    assert "lw $a0, var_a" in code
    assert "li $v0, 1" in code
    assert "syscall" in code

def test_addition_operation():
    src = """
    let a = 10;
    let b = 20;
    let c = a + b;
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg =gen_code(tree, stb.globalScope.symbols)
    code = gen_mips(cg, stb.globalScope.symbols)

    assert ".data" in code
    assert "var_a: .word 0" in code
    assert "var_b: .word 0" in code
    assert "var_c: .word 0" in code
    assert "li $t0, 10" in code
    assert "sw $t0, var_a" in code
    assert "li $t0, 20" in code
    assert "sw $t0, var_b" in code
    assert "lw $t0, var_a" in code
    assert "lw $t1, var_b" in code
    assert "add $t2, $t0, $t1" in code
    assert "sw $t0, var_c" in code

def test_subtraction_operation():
    src = """
    let a = 30;
    let b = 15;
    let c = a - b;
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg =gen_code(tree, stb.globalScope.symbols)
    code = gen_mips(cg, stb.globalScope.symbols)

    assert ".data" in code
    assert "var_a: .word 0" in code
    assert "var_b: .word 0" in code
    assert "var_c: .word 0" in code
    assert "li $t0, 30" in code
    assert "sw $t0, var_a" in code
    assert "li $t0, 15" in code
    assert "sw $t0, var_b" in code
    assert "lw $t0, var_a" in code
    assert "lw $t1, var_b" in code
    assert "sub $t2, $t0, $t1" in code
    assert "sw $t0, var_c" in code

def test_string_concatenation():
    src = """
    let str1 = "Hello, ";
    let str2 = "World!";
    let result = str1 + str2;
    print(result);
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg =gen_code(tree, stb.globalScope.symbols)
    code = gen_mips(cg, stb.globalScope.symbols)

    assert ".data" in code
    assert 'str0: .asciiz "Hello, "' in code
    assert 'str1: .asciiz "World!"' in code
    assert 'la $a0, str0' in code
    assert 'li $v0, 4' in code
    assert 'syscall' in code

def test_string_int_concatenation():
    src = """
    let num = 42;
    let str = "The answer is: ";
    let result = str + num;
    print(result);
    """
    parser, tree = parse_src(src)
    stb, errors = build_symbols(tree)
    tc, errors  = type_check(stb, errors, parser, tree)
    cg =gen_code(tree, stb.globalScope.symbols)
    code = gen_mips(cg, stb.globalScope.symbols)

    assert ".data" in code
    assert 'str0: .asciiz "The answer is: "' in code
    assert 'la $a0, str0' in code
    assert 'li $v0, 4' in code
    assert 'syscall' in code
