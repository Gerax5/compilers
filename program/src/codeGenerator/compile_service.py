from antlr4 import InputStream, CommonTokenStream
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from antlr4 import ParseTreeWalker


from symbolTable.SymbolTableBuilder import SymbolTableBuilder
from typeChecker.TypeChecker import TypeChecker
from utils.Error import Error
from codeGenerator.CodeGenerator import CodeGenerator
from mipsGenerator.MipsGenerator import MIPSGenerator
from utils.TempManager import TempManager


def compile_source_to_mips(source_code: str):
    """
    Recibe código Compiscript (string)
    Regresa:
        - tac_list  : lista de quadruples
        - mips_code : string con MIPS
        - errors    : lista de strings
    """

    errors = Error()

    input_stream = InputStream(source_code)
    lexer = CompiscriptLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = CompiscriptParser(stream)

    tree = parser.program()

    # 1. Build symbol table
    listener = SymbolTableBuilder(errors)

    ParseTreeWalker().walk(listener, tree)

    # 2. Type checking
    checker = TypeChecker(listener.scopes, listener.globalScope, errors, parser)
    checker.visit(tree)

    # 3. TAC generation
    temp_manager = TempManager()
    generator = CodeGenerator(temp_manager, listener.globalScope.symbols)
    generator.visit(tree)

    # 4. MIPS generation
    mips_generator = MIPSGenerator(generator.quadruples, listener.globalScope.symbols)
    mips_code = mips_generator.generate()

    # 5. Collect errors
    error_list = [str(e) for e in errors.errors]

    return generator.quadruples, mips_code, error_list
