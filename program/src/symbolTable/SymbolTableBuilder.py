from src.utils.Errors import Error
from src.utils.Scope import *
from src.utils.Types import Type
from CompiscriptListener import CompiscriptListener


class SymbolTableBuilder(CompiscriptListener):
    def __init__(self, errors: Error):
        self.errors = errors
        self.globalScope = Scope(None, "global")
        self.current = self.globalScope
        self.scopes = {}  # ctx -> scope (para la 2ª pasada)

    def enterProgram(self, ctx): 
        self.scopes[ctx] = self.current

    def enterBlock(self, ctx):
        self.current = Scope(self.current, "block")
        self.scopes[ctx] = self.current

    def exitBlock(self, ctx):
        self.current = self.current.parent

    # def enterFunctionDeclaration(self, ctx):
    #     name = ctx.ID().getText()
    #     ret  = self._type_of(ctx.type_()) if ctx.type_() else Type.VOID
    #     func = FuncSymbol(name, ret, [])
    #     if not self.current.define(func):
    #         self.errors.err_ctx(ctx, f"Function '{name}' redeclared")

    #     self.current = Scope(self.current, f"func {name}")
    #     self.scopes[ctx] = self.current

    #     if ctx.params():
    #         for p in ctx.params().param(): 
    #             pid = p.ID().getText()
    #             pty = self._type_of(p.type_())
    #             if not self.current.define(VarSymbol(pid, pty)):
    #                 self.errors.err_ctx(p, f"Parameter '{pid}' duplicated")
    #             func.params.append(VarSymbol(pid, pty))

    def enterConstantDeclaration(self, ctx):
        name = ctx.Identifier().getText() 
        ty = ctx.typeAnnotation().type_()
        ty_decl = self._type_of(ty) if ty else Type.NIL
        sym = VarSymbol(name, ty_decl, is_const=True)
        if not self.current.define(sym):
            self.errors.err_ctx(ctx, f"Constant '{name}' redeclared in this scope")

    # def exitFunctionDeclaration(self, ctx):
    #     self.current = self.current.parent

    def enterVariableDeclaration(self, ctx):
        name = ctx.Identifier().getText()
        ty = ctx.typeAnnotation().type_()
        ty = self._type_of(ty) if ty else Type.NIL
        if not self.current.define(VarSymbol(name, ty)):
            self.errors.err_ctx(ctx, f"Variable '{name}' redeclared in this scope")

    def _type_of(self, tctx) -> Type:
        if tctx is None: return Type.NIL
        text = tctx.getText()
        return {
            "int":Type.INT, "float":Type.FLOAT, "bool":Type.BOOL,
            "string":Type.STRING, "void":Type.VOID
        }.get(text, Type.NIL)