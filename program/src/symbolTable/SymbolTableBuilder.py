from src.utils.Errors import Error
from src.utils.Scope import VarSymbol, Type, ClassSymbol, FuncSymbol, Scope
from src.utils.Types import Type, ArrayType
from CompiscriptListener import CompiscriptListener
from CompiscriptParser import CompiscriptParser


class SymbolTableBuilder(CompiscriptListener):

    def __init__(self, errors: Error):
        self.errors = errors
        self.globalScope = Scope(None, "global")
        self.current = self.globalScope
        self.scopes = {}
        self.loop_depth = 0
        self.switch_depth = 0

    # Program
    def enterProgram(self, ctx): 
        self.scopes[ctx] = self.current

    # Block
    def enterBlock(self, ctx):
        self.current = Scope(self.current, "block")
        self.scopes[ctx] = self.current

    def exitBlock(self, ctx):
        self.current = self.current.parent

    # Variables
    def enterConstantDeclaration(self, ctx):
        name = ctx.Identifier().getText() 
        ty = ctx.typeAnnotation().type_()
        ty_decl = self._type_of(ty) if ty else Type.NULL
        sym = VarSymbol(name, ty_decl, is_const=True)
        if not self.current.define(sym):
            self.errors.err_ctx(ctx, f"Constant '{name}' redeclared in this scope")

    def enterVariableDeclaration(self, ctx):
        name = ctx.Identifier().getText()
        ty = ctx.typeAnnotation().type_()
        ty = self._type_of(ty) if ty else Type.NULL
        if not self.current.define(VarSymbol(name, ty)):
            self.errors.err_ctx(ctx, f"Variable '{name}' redeclared in this scope")

    # Functions
    def enterFunctionDeclaration(self, ctx):
        name = ctx.Identifier().getText() 
        ty = ctx.type_()
        ret  = self._type_of(ty) if ty else Type.VOID
        func = FuncSymbol(name, ret, [])
        if not self.current.define(func):
            self.errors.err_ctx(ctx, f"Function '{name}' redeclared")

        self.current = Scope(self.current, f"func {name}")
        self.scopes[ctx] = self.current

        if ctx.parameters():
            for p in ctx.parameters().parameter(): 
                p: CompiscriptParser.ParametersContext
                pid = p.Identifier().getText()
                pty_ = p.type_()
                pty = self._type_of(pty_)
                if not self.current.define(VarSymbol(pid, pty)):
                    self.errors.err_ctx(p, f"Parameter '{pid}' duplicated")
                func.params.append(VarSymbol(pid, pty))

    def exitFunctionDeclaration(self, ctx):
        self.current = self.current.parent
    
    # Clases
    def enterClassDeclaration(self, ctx):
        name = ctx.Identifier(0).getText()

        cls = ClassSymbol(name)
        if not self.current.define(cls):
            self.errors.err_ctx(ctx, f"Class '{name}' redeclared")

        classScope = Scope(self.current, f"class {name}")
        self.scopes[ctx] = classScope
        self.current = classScope
        cls.scope = classScope

        self.current.define(VarSymbol("this", cls, is_const=True))

    def exitClassDeclaration(self, ctx):
        self.current = self.current.parent

    def enterForStatement(self, ctx):
        forScope = Scope(self.current, "for")
        self.current = forScope
        self.scopes[ctx] = forScope
        self.loop_depth += 1

    def exitForStatement(self, ctx):
        self.loop_depth -= 1
        self.current = self.current.parent

    def enterForeachStatement(self, ctx):
        feScope = Scope(self.current, "foreach")
        self.current = feScope
        self.scopes[ctx] = feScope
        self.loop_depth += 1

        nameVariable = ctx.Identifier().getText()
        self.current.define(VarSymbol(nameVariable, Type.NULL))


    def exitForeachStatement(self, ctx):
        self.loop_depth -= 1
        self.current = self.current.parent

    def enterWhileStatement(self, ctx):
        self.loop_depth += 1

    def exitWhileStatement(self, ctx):
        self.loop_depth -= 1

    def enterDoWhileStatement(self, ctx):
        self.loop_depth += 1

    def exitDoWhileStatement(self, ctx):
        self.loop_depth -= 1

    def _type_of(self, tctx):
        if tctx is None:
            return Type.NULL
        
        text = tctx.getText() 
        
        # contar cuántos [] hay
        dims = text.count("[]")
        
        # quitar los [] para ver el tipo base
        base_name = text.replace("[]", "")
        
        base = {
            "int": Type.INT, "integer": Type.INT,
            "float": Type.FLOAT,
            "bool": Type.BOOL, "boolean": Type.BOOL,
            "string": Type.STRING,
            "void": Type.VOID,
            "null": Type.NULL
        }.get(base_name, None)
        
        if base is None:
            raise Exception(f"Tipo desconocido '{base_name}'")
        
        if dims > 0:
            return ArrayType(base, dims)
        else:
            return base