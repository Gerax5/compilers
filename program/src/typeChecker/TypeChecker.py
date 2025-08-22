from CompiscriptVisitor import CompiscriptVisitor
from src.utils.Errors import Error
from src.utils.Scope import VarSymbol, Type, ClassSymbol, FuncSymbol, Scope
from src.utils.Types import Type
from CompiscriptListener import CompiscriptListener
from CompiscriptParser import CompiscriptParser

class TypeChecker(CompiscriptVisitor):
    def __init__(self, scopes_by_ctx, global_scope, errors, parser):
        self.scopes = scopes_by_ctx
        self.current = global_scope
        self.errors = errors
        self.parser = parser
        self.types = {}
        self.fn_ret_stack = []
        self.loop_depth = 0
        self.switch_depth = 0

    def _set(self, ctx, ty):
        self.types[ctx] = ty
        return ty

    def _same(self, a, b):
        return a == b

    def _can_assign(self, dst, src):
        if dst == src: return True
        if dst == Type.FLOAT and src == Type.INT: return True
        if dst == Type.NULL: return True
        return False

    def _expect_bool(self, ctx, ty):
        if ty != Type.BOOL:
            self.errors.err_ctx(ctx, f"Se esperaba bool, se obtuvo {ty}")
        return Type.BOOL

    # INITIAL
    def visitProgram(self, ctx):
        print("Programming")
        return self.visitChildren(ctx)
    
    def visitBlock(self, ctx):
        prev = self.current
        self.current = self.scopes.get(ctx, self.current)
        r = self.visitChildren(ctx)
        self.current = prev
        return r

    def visitStatement(self, ctx):
        return self.visitChildren(ctx)

    # AAA

    def visitFunctionDeclaration(self, ctx):
        prev_scope = self.current
        fscope = self.scopes.get(ctx, self.current)
        self.current = fscope

        ret_ann = getattr(ctx, "type_", None) and ctx.type_()
        ret_ty = self._type_of(ret_ann) if ret_ann else Type.VOID
        self.fn_ret_stack.append(ret_ty)

        r = self.visitChildren(ctx)

        self.fn_ret_stack.pop()
        self.current = prev_scope
        return r

    def visitVariableDeclaration(self, ctx):
        name = ctx.Identifier().getText()
        ann  = getattr(ctx, "typeAnnotation", None) and ctx.typeAnnotation()
        declared_ty = self._type_of(ann.type_()) if ann else Type.NULL

        sym = self.current.resolve(name)
        if not sym:
            self.errors.err_ctx(ctx, f"Interno: variable '{name}' no encontrada")
            return None

        init = getattr(ctx, "initializer", None) and ctx.initializer()
        init_ty = None
        if init:
            expr = getattr(init, "expression", None) and init.expression()
            init_ty = self.visit(expr) if expr else self.visit(init)

        if declared_ty == Type.NULL and init_ty is not None:
            sym.ty = init_ty
        elif init_ty is not None and not self._can_assign(declared_ty, init_ty):
            self.errors.err_ctx(ctx, f"No se puede asignar {init_ty} a {declared_ty} en '{name}'")
        else:
            pass

        return None
    
    # IDENTIFICADOR DE TIPOS
    def visitIdentifierExpr(self, ctx):
        name = ctx.Identifier().getText()
        sym = self.current.resolve(name)
        if not sym:
            self.errors.err_ctx(ctx, f"'{name}' no declarado")
            return self._set(ctx, Type.NULL)
        return self._set(ctx, sym.ty)

    def visitLiteralExpr(self, ctx):
        tok = ctx.getChild(0).getText()
        if tok in ('true','false'): return self._set(ctx, Type.BOOL)
        if tok.startswith('"') or tok.startswith("'"): return self._set(ctx, Type.STRING)
        if tok.replace('_','').isdigit(): return self._set(ctx, Type.INT)
        try:
            float(tok); return self._set(ctx, Type.FLOAT)
        except ValueError:
            return self._set(ctx, Type.NULL)
    
    # VISIT de variables
    def visitConstantDeclaration(self, ctx):
        name = ctx.Identifier().getText()
        ann  = ctx.typeAnnotation()
        declared_ty = self._type_of(ann.type_()) if ann else Type.NULL


        sym = self.current.resolve(name)
        if not sym:
            self.errors.err_ctx(ctx, f"Interno: const '{name}' no encontrada")
            return None

        init = ctx.expression()
        if not init:
            self.errors.err_ctx(ctx, f"Const '{name}' requiere inicializador")
            return None

        init_ty = self.visit(init)


        if declared_ty == Type.NULL:
            sym.ty = init_ty
        elif not self._can_assign(declared_ty, init_ty):
            self.errors.err_ctx(ctx, f"Const '{name}': esperado {declared_ty}, recibido {init_ty}")
        return None

    def visitAssignExpr(self, ctx):
        lhs = getattr(ctx, "leftHandSide", None) and ctx.leftHandSide()
        rhs = getattr(ctx, "expression", None) and ctx.expression()

        rhs_ty = self.visit(rhs) if rhs else Type.NULL

        ident_expr = lhs and getattr(lhs, "IdentifierExpr", None) and lhs.IdentifierExpr()
        if ident_expr:
            name = ident_expr.Identifier().getText()
            sym = self.current.resolve(name)
            if not sym:
                self.errors.err_ctx(ctx, f"'{name}' no declarado")
                return self._set(ctx, rhs_ty)
            if getattr(sym, "is_const", False):
                self.errors.err_ctx(ctx, f"No se puede asignar a const '{name}'")
            elif not self._can_assign(sym.ty, rhs_ty):
                self.errors.err_ctx(ctx, f"Asignación incompatible: {sym.ty} = {rhs_ty}")
            return self._set(ctx, sym.ty)

        return self._set(ctx, rhs_ty)


    def _type_of(self, tctx):
        if not tctx: return Type.NULL
        text = tctx.getText()
        m = {
            "int": Type.INT, "integer": Type.INT,
            "float": Type.FLOAT,
            "bool": Type.BOOL, "boolean": Type.BOOL,
            "string": Type.STRING,
            "void": Type.VOID,
        }.get(text)
        if m is not None: return m
        sym = self.current.resolve(text)
        if sym and getattr(sym, "kind", None) == "class":
            return sym
        self.errors.err_ctx(tctx, f"Tipo desconocido '{text}'")
        return Type.NULL
    