# type_checker.py
from CompiscriptParserVisitor import CompiscriptParserVisitor
from CompiscriptParser import CompiscriptParser
from src.utils.Types import Type

class TypeChecker(CompiscriptParserVisitor):
    def __init__(self, scopes_by_ctx, global_scope, errors, parser):
        self.scopes = scopes_by_ctx
        self.current = global_scope
        self.errors = errors
        self.parser = parser
        self.types = {}              # ctx -> Type resultante de expresiones
        self.fn_ret_stack = []       # pila de tipos de retorno esperados
        self.loop_depth = 0
        self.switch_depth = 0

    # -------- helpers --------
    def _set(self, ctx, ty):
        self.types[ctx] = ty
        return ty

    def _same(self, a, b):
        return a == b

    def _can_assign(self, dst, src):
        if dst == src: return True
        # Widening simple: int -> float
        if dst == Type.FLOAT and src == Type.INT: return True
        # NULL (no anotado) permite inferir, lo maneja var/const
        if dst == Type.NULL: return True
        return False

    def _expect_bool(self, ctx, ty):
        if ty != Type.BOOL:
            self.errors.err_ctx(ctx, f"Se esperaba bool, se obtuvo {ty}")
        return Type.BOOL

    # -------- scopes --------
    def visitBlock(self, ctx):
        prev = self.current
        self.current = self.scopes.get(ctx, self.current)
        r = self.visitChildren(ctx)
        self.current = prev
        return r

    def visitFunctionDeclaration(self, ctx):
        # entrar a scope de la función
        prev_scope = self.current
        fscope = self.scopes.get(ctx, self.current)
        self.current = fscope

        # tipo de retorno declarado (si tu regla usa type_())
        ret_ann = getattr(ctx, "type_", None) and ctx.type_()
        ret_ty = self._type_of(ret_ann) if ret_ann else Type.VOID
        self.fn_ret_stack.append(ret_ty)

        r = self.visitChildren(ctx)

        self.fn_ret_stack.pop()
        self.current = prev_scope
        return r

    def visitClassDeclaration(self, ctx):
        prev = self.current
        self.current = self.scopes.get(ctx, self.current)
        r = self.visitChildren(ctx)
        self.current = prev
        return r

    # -------- declaraciones --------
    def visitVariableDeclaration(self, ctx):
        name = ctx.Identifier().getText()
        ann  = getattr(ctx, "typeAnnotation", None) and ctx.typeAnnotation()
        declared_ty = self._type_of(ann.type_()) if ann else Type.NULL

        sym = self.current.resolve(name)
        if not sym:
            # no debería pasar: ya se definió en DefPhase
            self.errors.err_ctx(ctx, f"Interno: variable '{name}' no encontrada")
            return None

        # inicializador (ajusta a tu gramatica: initializer -> expression)
        init = getattr(ctx, "initializer", None) and ctx.initializer()
        init_ty = None
        if init:
            # si tu 'initializer' tiene 'expression', úsalo; si no, visita el initializer
            expr = getattr(init, "expression", None) and init.expression()
            init_ty = self.visit(expr) if expr else self.visit(init)

        # inferencia si no hay tipo declarado
        if declared_ty == Type.NULL and init_ty is not None:
            sym.ty = init_ty
        elif init_ty is not None and not self._can_assign(declared_ty, init_ty):
            self.errors.err_ctx(ctx, f"No se puede asignar {init_ty} a {declared_ty} en '{name}'")
        else:
            # sin inicializador y sin anotación -> manten Type.NULL o marca error si tu lenguaje lo exige
            pass

        return None

    def visitConstantDeclaration(self, ctx):
        name = ctx.Identifier().getText()
        ann  = getattr(ctx, "typeAnnotation", None) and ctx.typeAnnotation()
        declared_ty = self._type_of(ann.type_()) if ann else Type.NULL

        sym = self.current.resolve(name)
        if not sym:
            self.errors.err_ctx(ctx, f"Interno: const '{name}' no encontrada")
            return None

        init = getattr(ctx, "initializer", None) and ctx.initializer()
        if not init:
            self.errors.err_ctx(ctx, f"Const '{name}' requiere inicializador")
            return None
        expr = getattr(init, "expression", None) and init.expression()
        init_ty = self.visit(expr) if expr else self.visit(init)

        if declared_ty == Type.NULL:
            sym.ty = init_ty
        elif not self._can_assign(declared_ty, init_ty):
            self.errors.err_ctx(ctx, f"Const '{name}': esperado {declared_ty}, recibido {init_ty}")
        return None

    # -------- asignaciones --------
    def visitAssignExpr(self, ctx):
        # regla: leftHandSide '=' expression
        # obtén el nombre si es IdentifierExpr; para propiedades/índices necesitas más lógica
        lhs = getattr(ctx, "leftHandSide", None) and ctx.leftHandSide()
        rhs = getattr(ctx, "expression", None) and ctx.expression()

        rhs_ty = self.visit(rhs) if rhs else Type.NULL

        # Caso simple: x = expr;
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

        # TODO: property/index assignment (si tu lenguaje lo soporta)
        return self._set(ctx, rhs_ty)

    # -------- expresiones (ajusta a tus labels) --------
    def visitAdditiveExpr(self, ctx):
        # expr (+|-) expr
        t0 = self.visit(ctx.getChild(0))
        op = ctx.getChild(1).getText()
        t1 = self.visit(ctx.getChild(2))
        # numérico con widening
        if {t0, t1} <= {Type.INT, Type.FLOAT}:
            return self._set(ctx, Type.FLOAT if Type.FLOAT in (t0, t1) else Type.INT)
        # suma de strings (si tu lenguaje admite)
        if op == '+' and (t0 == Type.STRING or t1 == Type.STRING):
            return self._set(ctx, Type.STRING)
        self.errors.err_ctx(ctx, f"Operación {op} inválida para {t0} y {t1}")
        return self._set(ctx, Type.NULL)

    def visitMultiplicativeExpr(self, ctx):
        t0 = self.visit(ctx.getChild(0))
        t1 = self.visit(ctx.getChild(2))
        if {t0, t1} <= {Type.INT, Type.FLOAT}:
            return self._set(ctx, Type.FLOAT if Type.FLOAT in (t0, t1) else Type.INT)
        self.errors.err_ctx(ctx, f"Multiplicación inválida para {t0} y {t1}")
        return self._set(ctx, Type.NULL)

    def visitRelationalExpr(self, ctx):
        # <, <=, >, >= → bool si comparables
        t0 = self.visit(ctx.getChild(0))
        t1 = self.visit(ctx.getChild(2))
        if {t0, t1} <= {Type.INT, Type.FLOAT, Type.STRING, Type.BOOL}:
            return self._set(ctx, Type.BOOL)
        self.errors.err_ctx(ctx, f"Comparación inválida entre {t0} y {t1}")
        return self._set(ctx, Type.NULL)

    def visitEqualityExpr(self, ctx):
        # ==, != → bool
        self.visit(ctx.getChild(0))
        self.visit(ctx.getChild(2))
        return self._set(ctx, Type.BOOL)

    def visitLogicalAndExpr(self, ctx):
        t0 = self.visit(ctx.getChild(0))
        t1 = self.visit(ctx.getChild(2))
        self._expect_bool(ctx, t0)
        self._expect_bool(ctx, t1)
        return self._set(ctx, Type.BOOL)

    def visitLogicalOrExpr(self, ctx):
        t0 = self.visit(ctx.getChild(0))
        t1 = self.visit(ctx.getChild(2))
        self._expect_bool(ctx, t0)
        self._expect_bool(ctx, t1)
        return self._set(ctx, Type.BOOL)

    def visitUnaryExpr(self, ctx):
        op = ctx.getChild(0).getText()
        t  = self.visit(ctx.getChild(1))
        if op in ('-', '+'):
            if t in (Type.INT, Type.FLOAT): return self._set(ctx, t)
            self.errors.err_ctx(ctx, f"Operador {op} inválido para {t}")
            return self._set(ctx, Type.NULL)
        if op == '!':
            self._expect_bool(ctx, t)
            return self._set(ctx, Type.BOOL)
        return self._set(ctx, Type.NULL)

    # -------- primarios / identificadores / literales --------
    def visitIdentifierExpr(self, ctx):
        name = ctx.Identifier().getText()
        sym = self.current.resolve(name)
        if not sym:
            self.errors.err_ctx(ctx, f"'{name}' no declarado")
            return self._set(ctx, Type.NULL)
        return self._set(ctx, sym.ty)

    def visitLiteralExpr(self, ctx):
        # ajusta a tus tokens: INTEGER, FLOAT, STRING, TRUE/FALSE
        tok = ctx.getChild(0).getText()
        if tok in ('true', 'false'):   return self._set(ctx, Type.BOOL)
        if tok.isdigit():              return self._set(ctx, Type.INT)
        if tok.replace('.','',1).isdigit(): return self._set(ctx, Type.FLOAT)
        if tok.startswith('"') or tok.startswith("'"): return self._set(ctx, Type.STRING)
        return self._set(ctx, Type.NULL)

    # -------- llamadas --------
    def visitCallExpr(self, ctx):
        # fname(args)
        fname = ctx.Identifier().getText()
        fn = self.current.resolve(fname)
        if not fn or getattr(fn, "kind", None) != "func":
            self.errors.err_ctx(ctx, f"'{fname}' no es función")
            return self._set(ctx, Type.NULL)

        # argumentos
        arg_types = []
        args = getattr(ctx, "arguments", None) and ctx.arguments()
        if args and hasattr(args, "expression"):
            # si arguments → expression (lista), ajústalo si tu gramatica usa otra lista
            for e in args.expression():
                arg_types.append(self.visit(e))

        if len(arg_types) != len(fn.params):
            self.errors.err_ctx(ctx, f"{fname} espera {len(fn.params)} args, se pasaron {len(arg_types)}")
        else:
            for i, (a, p) in enumerate(zip(arg_types, fn.params)):
                if not self._can_assign(p.ty, a):
                    self.errors.err_ctx(ctx, f"Arg {i+1} de {fname}: esperado {p.ty}, obtenido {a}")

        return self._set(ctx, fn.ty)

    # -------- control de flujo --------
    def visitIfStatement(self, ctx):
        cond = getattr(ctx, "expression", None) and ctx.expression()
        if cond: self._expect_bool(cond, self.visit(cond))
        return self.visitChildren(ctx)

    def visitWhileStatement(self, ctx):
        cond = getattr(ctx, "expression", None) and ctx.expression()
        if cond: self._expect_bool(cond, self.visit(cond))
        self.loop_depth += 1
        r = self.visitChildren(ctx)
        self.loop_depth -= 1
        return r

    def visitDoWhileStatement(self, ctx):
        self.loop_depth += 1
        r = self.visitChildren(ctx)
        self.loop_depth -= 1
        # condición suele venir al final
        cond = getattr(ctx, "expression", None) and ctx.expression()
        if cond: self._expect_bool(cond, self.visit(cond))
        return r

    # -------- returns / break/continue --------
    def visitReturnStatement(self, ctx):
        expected = self.fn_ret_stack[-1] if self.fn_ret_stack else Type.VOID
        expr = getattr(ctx, "expression", None) and ctx.expression()
        got = self.visit(expr) if expr else Type.VOID
        if not self._can_assign(expected, got):
            self.errors.err_ctx(ctx, f"return: esperado {expected}, obtenido {got}")
        return None

    # (si tienes nodos específicos para break/continue)
    def visitBreakStatement(self, ctx):
        if self.loop_depth == 0 and self.switch_depth == 0:
            self.errors.err_ctx(ctx, "break fuera de loop/switch")
        return None

    def visitContinueStatement(self, ctx):
        if self.loop_depth == 0:
            self.errors.err_ctx(ctx, "continue fuera de loop")
        return None

    # -------- util: mapear tipos desde nodos 'type_' --------
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
        # tipos nominales (clases)
        sym = self.current.resolve(text)
        if sym and getattr(sym, "kind", None) == "class":
            return sym
        self.errors.err_ctx(tctx, f"Tipo desconocido '{text}'")
        return Type.NULL
