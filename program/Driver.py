import sys
from antlr4 import * # type: ignore
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser

from CompiscriptListener import CompiscriptListener

from src.utils.Errors import Error
from src.utils.Temp import TempManager
from src.symbolTable.SymbolTableBuilder import SymbolTableBuilder
from src.typeChecker.TypeChecker import TypeChecker
from src.codeGenerator.CodeGenerator import CodeGenerator
from src.mipsGenerator.MipsGenerator import MIPSGenerator


def main(argv):
    input_stream = FileStream(argv[1], encoding="utf-8")
    lexer = CompiscriptLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = CompiscriptParser(stream)
    tree = parser.program()  # We are using 'prog' since this is the starting rule based on our Compiscript grammar, yay!

    errors = Error()

    walker = ParseTreeWalker()
    listener = SymbolTableBuilder(errors)
    walker.walk(listener, tree)

    checker = TypeChecker(listener.scopes, listener.globalScope, errors, parser)
    checker.visit(tree)

    temp_manager = TempManager()
    generator = CodeGenerator(temp_manager, listener.globalScope.symbols)
    generator.visit(tree)

    print("TAC generado:")
    for quad in generator.quadruples:
        print(quad)

    # mips_generator = MIPSGenerator(generator.quadruples, listener.globalScope.symbols)
    # mips_code = mips_generator.generate()
    # print("\nCódigo MIPS generado:")
    # print(mips_code)

    # output_filename = "codegen.s"
    # with open(output_filename, "w", encoding="utf-8") as f:
    #     f.write(mips_code)

    # print("GLOBAL:", list(listener.globalScope.symbols.keys()))
    # for ctx, sc in listener.scopes.items():
    #     print(type(ctx).__name__, sc.name, list(sc.symbols.keys()))

    for error in errors.errors:
        print(error)





if __name__ == '__main__':
    main(sys.argv)