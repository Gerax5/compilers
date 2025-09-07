from CompiscriptVisitor import CompiscriptVisitor
from src.utils.Errors import Error
from src.utils.Scope import VarSymbol, Type, ClassSymbol, FuncSymbol, Scope
from src.utils.Types import Type, ArrayType
from CompiscriptListener import CompiscriptListener
from CompiscriptParser import CompiscriptParser
from antlr4.tree.Tree import TerminalNode

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

    # HELPERS
    def _set(self, ctx, ty):
        self.types[ctx] = ty
        return ty

    def _same(self, a, b):
        return a == b

    def _is_subclass(self, sub, sup):
        c = sub
        while c and getattr(c, "superclass", None):
            if c.superclass == sup:
                return True
            c = c.superclass
        return False

    def _can_assign(self, dst, src):
        if dst == src: return True
        if dst == Type.FLOAT and src == Type.INT: return True
        if dst == Type.NULL: return True
        if isinstance(dst, ArrayType) and isinstance(src, ArrayType):
            if dst.dimensions != src.dimensions:
                return False
            if dst.base == src.base:
                return True
            if dst.base == Type.FLOAT and src.base == Type.INT:
                return True
            return False
        if getattr(dst, "kind", "") == "class" and getattr(src, "kind", "") == "class":
            return src == dst or self._is_subclass(src, dst)
        return False

    def _expect_bool(self, ctx, ty):
        if ty != Type.BOOL:
            self.errors.err_ctx(ctx, f"Se esperaba bool, se obtuvo {ty}")
        return Type.BOOL

    def _is_array(self, t):
        return isinstance(t, ArrayType)

    def _unify_base(self, a, b):
        if a == b:
            return a
        if {a, b} <= {Type.INT, Type.FLOAT}:
            return Type.FLOAT
        return None

    def _class_member(self, cls, name):
        c = cls
        while c:
            sc = getattr(c, "scope", None)
            if sc:
                sym = sc.resolve(name)
                if sym: return sym
            c = getattr(c, "superclass", None)
        return None

    
    def _apply_assignment(self, name, rhs_ty, ctx):
        sym: VarSymbol = self.current.resolve(name)
        if not sym:
            self.errors.err_ctx(ctx, f"'{name}' no declarado")
            return self._set(ctx, rhs_ty)
        if sym.kind == 'const':
            self.errors.err_ctx(ctx, f"No se puede asignar a const '{name}'")
            return self._set(ctx, sym.ty)
        if not self._can_assign(sym.ty, rhs_ty):
            self.errors.err_ctx(ctx, f"Asignación incompatible: {sym.ty} y {rhs_ty}")
        return self._set(ctx, sym.ty)

    def _apply_property_assignment(self, recv_ty, prop, rhs_ty, ctx):
        if not (getattr(recv_ty, "kind", "") == "class"):
            self.errors.err_ctx(ctx, f"No se puede asignar propiedad '{prop}' sobre tipo {recv_ty}")
            return self._set(ctx, rhs_ty)
        psym = self._class_member(recv_ty, prop)
        if not psym:
            self.errors.err_ctx(ctx, f"Propiedad '{prop}' no existe")
            return self._set(ctx, rhs_ty)
        if getattr(psym, "is_const", False):
            self.errors.err_ctx(ctx, f"La propiedad '{prop}' es const")
            return self._set(ctx, psym.ty)
        if not self._can_assign(psym.ty, rhs_ty):
            self.errors.err_ctx(ctx, f"Asignación incompatible a '{prop}': {psym.ty} = {rhs_ty}")
        return self._set(ctx, psym.ty)


    def _apply_index_assignment(self, arr_ty, idx_ty, rhs_ty, ctx):
        from src.utils.Types import ArrayType, Type
        if not isinstance(arr_ty, ArrayType):
            self.errors.err_ctx(ctx, "Indexación sobre no-arreglo")
            return self._set(ctx, rhs_ty)
        if idx_ty != Type.INT:
            self.errors.err_ctx(ctx, "Índice de arreglo debe ser integer")
        # tipo del elemento
        elem_ty = (ArrayType(arr_ty.base, arr_ty.dimensions-1)
                if arr_ty.dimensions > 1 else arr_ty.base)
        if not self._can_assign(elem_ty, rhs_ty):
            self.errors.err_ctx(ctx, f"Asignación incompatible en arreglo: {elem_ty} = {rhs_ty}")

        return self._set(ctx, elem_ty)

    def _const_int(self, expr_ctx):
        txt = expr_ctx.getText().replace('_','')
        if txt.startswith('-'):
            return int(txt[1:]) * -1 if txt[1:].isdigit() else None
        return int(txt) if txt.isdigit() else None

    def _resolve_primary_atom_type(self, base):
        if hasattr(base, "Identifier") and base.Identifier():
            name = base.Identifier().getText()
            sym = self.current.resolve(name)
            if not sym:
                self.errors.err_ctx(base, f"'{name}' no declarado")
                return Type.NULL, name, None
            return sym.ty, name, sym
        ty = self.visit(base)
        return ty, None, None


    # INITIAL
    def visitProgram(self, ctx):
        return self.visitChildren(ctx)
    
    def visitBlock(self, ctx):
        prev = self.current
        self.current = self.scopes.get(ctx, self.current)
        r = self.visitChildren(ctx)
        self.current = prev
        return r

    def visitStatement(self, ctx):
        return self.visitChildren(ctx)
    
    # IDENTIFICADOR DE TIPOS
    def visitIdentifierExpr(self, ctx):
        name = ctx.Identifier().getText()
        sym = self.current.resolve(name)
        if not sym:
            self.errors.err_ctx(ctx, f"'{name}' no declarado")
            return self._set(ctx, Type.NULL)
        
        if sym.kind == "func":
            return self._set(ctx, sym) 

        if getattr(sym, "kind", "") == "class":
            return self._set(ctx, sym)

        return self._set(ctx, sym.ty)

    def visitLiteralExpr(self, ctx):
        tok = ctx.getChild(0)
        if not isinstance(tok, TerminalNode):
            return self.visit(tok)

        tok = tok.getText()
        if tok in ('true','false'): return self._set(ctx, Type.BOOL)
        if tok.startswith('"') or tok.startswith("'"): return self._set(ctx, Type.STRING)
        if tok.replace('_','').isdigit(): return self._set(ctx, Type.INT)
        try:
            float(tok); return self._set(ctx, Type.FLOAT)
        except ValueError:
            return self._set(ctx, Type.NULL)
        
    def visitArrayLiteral(self, ctx):
        elem_nodes = ctx.expression() or []
        elem_types = [self.visit(e) for e in elem_nodes]

        if not elem_types:
            self.errors.err_ctx(ctx, "No se puede inferir el tipo de un arreglo vacío; anota el tipo (p. ej. int[])")
            return self._set(ctx, ArrayType(Type.NULL, 1))

        any_arr = any(self._is_array(t) for t in elem_types)

        if any_arr:
            if not all(self._is_array(t) for t in elem_types):
                self.errors.err_ctx(ctx, "Arreglo irregular: mezcla de elemento escalar y subarreglo.")
                return self._set(ctx, ArrayType(Type.NULL, 1))

            inner_dims = elem_types[0].dimensions
            if any(t.dimensions != inner_dims for t in elem_types):
                self.errors.err_ctx(ctx, "Arreglo irregular: dimensiones distintas entre elementos.")
                return self._set(ctx, ArrayType(Type.NULL, inner_dims + 1))

            base = elem_types[0].base
            for t in elem_types[1:]:
                ub = self._unify_base(base, t.base)
                if ub is None:
                    self.errors.err_ctx(ctx, f"Tipos incompatibles en arreglo: {base} y {t.base}")
                    return self._set(ctx, ArrayType(Type.NULL, inner_dims + 1))
                base = ub

            return self._set(ctx, ArrayType(base, inner_dims + 1))

        else:
            base = elem_types[0]
            for t in elem_types[1:]:
                ub = self._unify_base(base, t)
                if ub is None:
                    self.errors.err_ctx(ctx, f"Tipos incompatibles en arreglo: {base} y {t}")
                    return self._set(ctx, ArrayType(Type.NULL, 1))
                base = ub
            return self._set(ctx, ArrayType(base, 1))


    
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

    def visitAssignment(self, ctx):
        left = ctx.Identifier().getText()
        exps = ctx.expression() or []

        if len(exps) == 1:
            rhs_ty = self.visit(exps[0])
            return self._apply_assignment(left, rhs_ty, ctx)

        elif len(exps) == 2:
            recv_ty = self.visit(exps[0])
            rhs_ty  = self.visit(exps[1])
            return self._apply_property_assignment(recv_ty, left, rhs_ty, ctx)

        return self.visitChildren(ctx)

    def visitAssignExpr(self, ctx):
        rhs_ty = self.visit(ctx.assignmentExpr())

        lhs = ctx.leftHandSide()
        base_ty, base_name, _ = self._resolve_primary_atom_type(lhs.primaryAtom())
        suffixes = list(lhs.suffixOp() or [])

        if not suffixes:
            if base_name is None:
                self.errors.err_ctx(lhs, "El lado izquierdo no es asignable")
                return self._set(ctx, base_ty)
            return self._apply_assignment(base_name, rhs_ty, ctx)

        recv_ty = base_ty
        for s in suffixes[:-1]:
            kind = s.getChild(0).getText()  
            if kind == '[':
                idx_ty = self.visit(s.expression())
                if idx_ty != Type.INT:
                    self.errors.err_ctx(s, "Índice de arreglo debe ser integer")
                if not isinstance(recv_ty, ArrayType):
                    self.errors.err_ctx(s, "Indexación sobre no-arreglo")
                    recv_ty = Type.NULL
                else:
                    recv_ty = (ArrayType(recv_ty.base, recv_ty.dimensions - 1)
                            if recv_ty.dimensions > 1 else recv_ty.base)

            elif kind == '.':
                prop = s.Identifier().getText()
                if not (hasattr(recv_ty, "kind") and recv_ty.kind == "class" and getattr(recv_ty, "scope", None)):
                    self.errors.err_ctx(s, f"No se puede acceder propiedad '{prop}' sobre tipo {recv_ty}")
                    recv_ty = Type.NULL
                else:
                    psym = recv_ty.scope.resolve(prop)
                    if not psym:
                        self.errors.err_ctx(s, f"Propiedad '{prop}' no existe")
                        recv_ty = Type.NULL
                    else:
                        recv_ty = psym.ty

            else:  
                self.errors.err_ctx(s, "Una llamada no puede usarse como lado izquierdo de una asignación")
                recv_ty = Type.NULL

        last = suffixes[-1]
        last_kind = last.getChild(0).getText()

        if last_kind == '[':
            idx_ty = self.visit(last.expression())
            return self._apply_index_assignment(recv_ty, idx_ty, rhs_ty, ctx)

        if last_kind == '.':
            prop = last.Identifier().getText()
            return self._apply_property_assignment(recv_ty, prop, rhs_ty, ctx)

        self.errors.err_ctx(last, "Una llamada no puede usarse como lado izquierdo de una asignación")
        return self._set(ctx, recv_ty)


    
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

    def visitLeftHandSide(self, ctx):
        return super().visitLeftHandSide(ctx)

    # Varibales Arrays
    def visitIndexExpr(self, ctx):
        recv_ty = self.visit(ctx.parentCtx.getChild(0))
        idx_ty  = self.visit(ctx.expression())

        if not isinstance(recv_ty, ArrayType):
            self.errors.err_ctx(ctx, "Indexación sobre no-arreglo")
            return self._set(ctx, Type.NULL)

        if idx_ty != Type.INT:
            self.errors.err_ctx(ctx, "Índice de arreglo debe ser integer")

        elem_ty = (ArrayType(recv_ty.base, recv_ty.dimensions - 1)
               if recv_ty.dimensions > 1 else recv_ty.base)

        return self._set(ctx, elem_ty)

    
    # Funciones y clases
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
    
    def visitParameter(self, ctx): # REVISAR
        ty_ctx = ctx.type_() if hasattr(ctx, "type_") else None
        ty = self._type_of(ty_ctx) if ty_ctx else Type.NULL
        if ty == Type.VOID:
            self.errors.err_ctx(ctx, "Un parámetro no puede ser de tipo void")
        return ty

    def visitParameters(self, ctx): # REVISAR
        params = ctx.parameter() or []
        return [self.visit(p) for p in params]

    def visitReturnStatement(self, ctx):
        expected = self.fn_ret_stack[-1] if self.fn_ret_stack else Type.VOID
        expr: CompiscriptParser.ExpressionContext = ctx.expression()
        if expected == Type.VOID:
            if expr is not None:
                self.errors.err_ctx(ctx, "return no debe llevar expresión en función void")
            return self._set(ctx, Type.VOID)

        if expr is None:
            self.errors.err_ctx(ctx, f"se esperaba return de tipo {expected}")
            return self._set(ctx, expected)

        ty = self.visit(expr)
        if not self._can_assign(expected, ty):
            self.errors.err_ctx(ctx, f"return: esperado {expected}, recibido {ty}")
        return self._set(ctx, expected)

    def visitArguments(self, ctx):
        exprs = ctx.expression() or []
        return [self.visit(e) for e in exprs]
    
    def visitCallExpr(self, ctx):
        args_ctx = ctx.arguments()
        args_ty = self.visit(args_ctx) if args_ctx else []

        parent = ctx.parentCtx
        callee_node = parent.getChild(0)        
        callee_val  = self.visit(callee_node)

        if isinstance(callee_val, FuncSymbol):
            params = callee_val.params
            if len(params) != len(args_ty):
                self.errors.err_ctx(ctx, f"'{callee_val.name}' espera {len(params)} args, recibió {len(args_ty)}")
                return self._set(ctx, callee_val.ty)
            for i, (p, a) in enumerate(zip(params, args_ty), 1):
                if not self._can_assign(p.ty, a):
                    self.errors.err_ctx(ctx, f"Arg {i} de '{callee_val.name}': esperado {p.ty}, recibió {a}")
            return self._set(ctx, callee_val.ty)

        if getattr(callee_val, "kind", "") == "class":
            cls = callee_val

            ctor = cls.resolve_member("constructor") if hasattr(cls, "resolve_member") else None
            if ctor:
                params = ctor.params
                if len(params) != len(args_ty):
                    self.errors.err_ctx(ctx, f"constructor de {cls.name} espera {len(params)} args, recibió {len(args_ty)}")
                else:
                    for i, (p, a) in enumerate(zip(params, args_ty), 1):
                        if not self._can_assign(p.ty, a):
                            self.errors.err_ctx(ctx, f"Arg {i} del constructor de {cls.name}: esperado {p.ty}, recibió {a}")
            elif args_ty:
                self.errors.err_ctx(ctx, f"{cls.name} no tiene constructor que acepte {len(args_ty)} args")

            return self._set(ctx, cls)

        self.errors.err_ctx(ctx, "expresión no invocable")
        return self._set(ctx, Type.NULL)

    def visitPrimaryExpr(self, ctx):
        if ctx.getChildCount() == 3 and ctx.getChild(0).getText() == '(' and ctx.getChild(2).getText() == ')':
            return self.visit(ctx.getChild(1))
        return self.visitChildren(ctx)

    # CLASES
    def visitClassDeclaration(self, ctx): # PREGUNTAR OVERRIDE
        prev = self.current
        self.current = self.scopes.get(ctx, self.current)
        r = self.visitChildren(ctx)
        self.current = prev
        return r

    def visitThisExpr(self, ctx):
        sym = self.current.resolve("this")
        if not sym:
            self.errors.err_ctx(ctx, "Uso de 'this' fuera de una clase")
            return self._set(ctx, Type.NULL)
        return self._set(ctx, sym.ty)
    
    def visitPropertyAccessExpr(self, ctx):
        parent = ctx.parentCtx
        recv_node = parent.getChild(0) if parent and parent.getChildCount() > 0 else None
        recv_ty = self.visit(recv_node) if recv_node else Type.NULL

        prop = ctx.Identifier().getText() if hasattr(ctx, "Identifier") and ctx.Identifier() \
           else ctx.getChild(1).getText()

        if not (hasattr(recv_ty, "kind") and recv_ty.kind == "class"):
            self.errors.err_ctx(ctx, f"No se puede acceder propiedad '{prop}' sobre tipo {recv_ty}")
            return self._set(ctx, Type.NULL)

        psym = recv_ty.resolve_member(prop) if hasattr(recv_ty, "resolve_member") \
           else (recv_ty.scope.resolve(prop) if getattr(recv_ty, "scope", None) else None)


        psym = recv_ty.resolve_member(prop)
        if not psym:
            self.errors.err_ctx(ctx, f"Propiedad '{prop}' no existe")
            return self._set(ctx, Type.NULL)
        
        return self._set(ctx, psym if getattr(psym, "kind", "") == "func" else psym.ty)

    def visitNewExpr(self, ctx):
        name = ctx.Identifier().getText()

        if not name:
            return self._set(ctx, Type.NULL)

        sym = self.current.resolve(name)
        if not sym or getattr(sym, "kind", "") != "class":
            self.errors.err_ctx(ctx, f"Tipo de clase '{name}' no encontrado")
            return self._set(ctx, Type.NULL)

        args = ctx.arguments()
        if isinstance(args, list):       
            args = args[0] if args else None

        exprs = args.expression() if (args and hasattr(args, "expression")) else []
        args_ty = [self.visit(e) for e in exprs]

        ctor = self._class_member(sym, "constructor")

        if ctor:
            params = ctor.params
            if len(params) != len(args_ty):
                self.errors.err_ctx(ctx,
                    f"constructor de {name} espera {len(params)} args, recibió {len(args_ty)}")
            else:
                for i, (p, a) in enumerate(zip(params, args_ty), 1):
                    if not self._can_assign(p.ty, a):
                        self.errors.err_ctx(ctx,
                            f"Arg {i} del constructor de {name}: esperado {p.ty}, recibió {a}")
        elif args_ty:
            self.errors.err_ctx(ctx, f"{name} no tiene constructor que acepte {len(args_ty)} args")

        return self._set(ctx, sym)

    # FOR
    def visitForStatement(self, ctx):
        prev_scope = self.current
        fscope = self.scopes.get(ctx, self.current)
        self.current = fscope

        self.loop_depth += 1
        
        try:
            exprs = list(ctx.expression() or [])

            if hasattr(ctx, "variableDeclaration") and ctx.variableDeclaration():
                self.visit(ctx.variableDeclaration())
                cond = exprs[0] if len(exprs) >= 1 else None
                incr = exprs[1] if len(exprs) >= 2 else None
            else:
                init = exprs[0] if len(exprs) >= 1 else None
                cond = exprs[1] if len(exprs) >= 2 else None
                incr = exprs[2] if len(exprs) >= 3 else None
                if init:
                    self.visit(init)

            if cond:
                cond_ty = self.visit(cond)
                self._expect_bool(cond, cond_ty)

            if incr:
                self.visit(incr)

            if hasattr(ctx, "block") and ctx.block():
                self.visit(ctx.block())

        finally:
            self.loop_depth -= 1
            self.current = prev_scope

    def visitForeachStatement(self, ctx):
        prev_scope = self.current
        self.current = self.scopes.get(ctx, self.current)
        self.loop_depth += 1

        try:
            coll_expr = getattr(ctx, "expression", None) and ctx.expression()
            coll_ty = self.visit(coll_expr) if coll_expr else Type.NULL

            if isinstance(coll_ty, ArrayType):
                elem_ty = (ArrayType(coll_ty.base, coll_ty.dimensions - 1)
                        if coll_ty.dimensions > 1 else coll_ty.base)
            else:
                self.errors.err_ctx(ctx, f"foreach espera un arreglo; recibió {coll_ty}")
                elem_ty = Type.NULL

            name = getattr(ctx, "Identifier", None) and ctx.Identifier().getText()
            if name:
                sym = self.current.resolve(name)
                if not sym:
                    self.errors.err_ctx(ctx, f"Interno: variable '{name}' no encontrada en foreach")
                else:
                    sym.ty = elem_ty

            body = getattr(ctx, "block", None) and ctx.block()
            if body:
                self.visit(body)

        finally:
            self.loop_depth -= 1
            self.current = prev_scope

        return None

    def visitContinueStatement(self, ctx):
        if self.loop_depth <= 0:
            self.errors.err_ctx(ctx, "'continue' fuera de un bucle")
        return None
    
    def visitBreakStatement(self, ctx):
        # válido si estamos dentro de un ciclo o de un switch
        if self.loop_depth == 0 and self.switch_depth == 0:
            self.errors.err_ctx(ctx, "break fuera de un ciclo o switch")
        return None


    # IF
    def visitIfStatement(self, ctx):
        cond = ctx.expression()
        cond_ty = self.visit(cond) if cond else Type.NULL
        self._expect_bool(cond or ctx, cond_ty)
        body = ctx.block()
        if len(body) >= 1: self.visit(body[0])
        if len(body) >= 2: self.visit(body[1])

    # Bool EXPR
    def visitRelationalExpr(self, ctx):
        n = ctx.getChildCount()
        if n == 1:
            return self.visit(ctx.getChild(0))

        left  = self.visit(ctx.getChild(0))
        op    = ctx.getChild(1).getText()
        right = self.visit(ctx.getChild(2))

        if left not in (Type.INT, Type.FLOAT) or right not in (Type.INT, Type.FLOAT):
            self.errors.err_ctx(ctx, f"Comparación {op} requiere números, recibió {left} y {right}")

        return self._set(ctx, Type.BOOL)


    def visitEqualityExpr(self, ctx):
        n = ctx.getChildCount()
        if n == 1:
            return self.visit(ctx.getChild(0))
        
        left = self.visit(ctx.getChild(0))
        op = ctx.getChild(1).getText()
        right = self.visit(ctx.getChild(2))

        if not self._can_assign(left, right) and not self._can_assign(right, left):
            self.errors.err_ctx(ctx, f"Comparación {op} entre tipos incompatibles: {left} y {right}")

        return self._set(ctx, Type.BOOL)

    def visitLogicalAndExpr(self, ctx):
        n = ctx.getChildCount()
        if n == 1:
            return self.visit(ctx.getChild(0))

        left = self.visit(ctx.getChild(0))
        op = ctx.getChild(1).getText()
        right = self.visit(ctx.getChild(2))

        if left != Type.BOOL or right != Type.BOOL:
            self.errors.err_ctx(ctx, f"Operación {op} requiere booleanos, recibió {left} y {right}")

        return self._set(ctx, Type.BOOL)

    def visitLogicalOrExpr(self, ctx):
        n = ctx.getChildCount()
        if n == 1:
            return self.visit(ctx.getChild(0))

        left = self.visit(ctx.getChild(0))
        op = ctx.getChild(1).getText()
        right = self.visit(ctx.getChild(2))

        if left != Type.BOOL or right != Type.BOOL:
            self.errors.err_ctx(ctx, f"Operación {op} requiere booleanos, recibió {left} y {right}")

        return self._set(ctx, Type.BOOL)

    # ADD
    def visitAdditiveExpr(self, ctx):
        n = ctx.getChildCount()

        if n == 1: # Por alguna razon las variables entran aqui lol no entiendo
            return self.visit(ctx.getChild(0))

        left  = self.visit(ctx.getChild(0))
        op = ctx.getChild(1).getText()
        right = self.visit(ctx.getChild(2))

        if left in (Type.INT, Type.FLOAT) and right in (Type.INT, Type.FLOAT):
            return self._set(ctx, Type.FLOAT if Type.FLOAT in (left, right) else Type.INT)

        if op == '+' and (left == Type.STRING or right == Type.STRING):
            return self._set(ctx, Type.STRING)

        self.errors.err_ctx(ctx, f"operación {op} inválida para {left} y {right}")
        return self._set(ctx, Type.NULL)

    def visitMultiplicativeExpr(self, ctx):
        # print(list[ctx.getChild(0)])
        n = ctx.getChildCount()

        if n == 1:
            return self.visit(ctx.getChild(0))

        left = self.visit(ctx.getChild(0))
        op = ctx.getChild(1).getText()
        right = self.visit(ctx.getChild(2)) 

        if op == "%":
            if left == Type.INT and right == Type.INT:
                return self._set(ctx, Type.INT)
            self.errors.err_ctx(ctx, f"Operación % requiere enteros, recibió {left} y {right}")
            # Para evitar cascada de errores, asumimos que el resultado pretendido era entero
            return self._set(ctx, Type.INT)

        elif op in ('*', '/'):
            if left in (Type.INT, Type.FLOAT) and right in (Type.INT, Type.FLOAT):
                if op == '/':
                    # División produce float (int/int -> float también)
                    return self._set(ctx, Type.FLOAT)
                # Multiplicación: promoción a float si alguno es float
                return self._set(ctx, Type.FLOAT if Type.FLOAT in (left, right) else Type.INT)

            self.errors.err_ctx(ctx, f"Operación {op} inválida para {left} y {right}")
            return self._set(ctx, Type.NULL)
        
        self.errors.err_ctx(ctx, f"Operador desconocido: {op}")
        return self._set(ctx, Type.NULL)

    def visitUnaryExpr(self, ctx):
        n = ctx.getChildCount()

        if n == 1:
            return self.visit(ctx.getChild(0))
        
        value = self.visit(ctx.getChild(1))
        self._expect_bool(ctx, value)

        return self._set(ctx, Type.BOOL)

    def visitTernaryExpr(self, ctx):
        # Regla: conditionalExpr : logicalOrExpr ('?' expression ':' expression)?
        n = ctx.getChildCount()
        if n == 1:
            return self.visit(ctx.getChild(0))

        # Con operador ternario
        cond_ty = self.visit(ctx.getChild(0))
        self._expect_bool(ctx, cond_ty)

        then_ty = self.visit(ctx.getChild(2))
        else_ty = self.visit(ctx.getChild(4))

        # Igualdad exacta -> ese tipo
        if then_ty == else_ty:
            return self._set(ctx, then_ty)

        # Arreglos: mismas dimensiones y unificación de base numérica
        if self._is_array(then_ty) and self._is_array(else_ty):
            if then_ty.dimensions == else_ty.dimensions:
                ub = self._unify_base(then_ty.base, else_ty.base)
                if ub is not None:
                    return self._set(ctx, ArrayType(ub, then_ty.dimensions))
            self.errors.err_ctx(ctx, f"Tipos incompatibles en ternario: {then_ty} y {else_ty}")
            return self._set(ctx, ArrayType(Type.NULL, then_ty.dimensions))

        # Primitivos numéricos: INT/FLOAT -> promo
        ub = self._unify_base(then_ty, else_ty)
        if ub is not None:
            return self._set(ctx, ub)

        # Incompatibles (ej. int vs string; clase vs int, etc.)
        self.errors.err_ctx(ctx, f"Tipos incompatibles en ternario: {then_ty} y {else_ty}")
        return self._set(ctx, Type.NULL)

    def visitExprNoAssign(self, ctx):
        # Alt de assignmentExpr: conditionalExpr # ExprNoAssign
        ty = self.visit(ctx.getChild(0))
        return self._set(ctx, ty)
    
    def visitExpression(self, ctx):
        # Regla: expression : assignmentExpr
        ty = self.visit(ctx.getChild(0))
        return self._set(ctx, ty)

    def visitPropertyAssignExpr(self, ctx):
        # Alt: lhs=leftHandSide '.' Identifier '=' assignmentExpr
        recv_ty = self.visit(ctx.leftHandSide())
        prop    = ctx.Identifier().getText()
        rhs_ty  = self.visit(ctx.assignmentExpr())
        return self._apply_property_assignment(recv_ty, prop, rhs_ty, ctx)
    
    # Sentencias de Control / flujo
    
    def visitWhileStatement(self, ctx):
        # while '(' expression ')' block
        cond = ctx.expression()
        cond_ty = self.visit(cond) if cond else Type.NULL
        self._expect_bool(cond or ctx, cond_ty)

        self.loop_depth += 1
        try:
            body = getattr(ctx, "block", None) and ctx.block()
            if body:
                self.visit(body)
        finally:
            self.loop_depth -= 1
        return None

    def visitDoWhileStatement(self, ctx):
        # do block 'while' '(' expression ')' ';'
        self.loop_depth += 1
        try:
            body = getattr(ctx, "block", None) and ctx.block()
            if body:
                self.visit(body)
        finally:
            self.loop_depth -= 1

        cond = ctx.expression()
        cond_ty = self.visit(cond) if cond else Type.NULL
        self._expect_bool(cond or ctx, cond_ty)
        return None

    def visitSwitchStatement(self, ctx):
        # switch '(' expression ')' '{' switchCase* defaultCase? '}'
        cond = ctx.expression()
        cond_ty = self.visit(cond) if cond else Type.NULL
        self._expect_bool(cond or ctx, cond_ty)

        self.switch_depth += 1
        try:
            for sc in (ctx.switchCase() or []):
                self.visit(sc)
            d = getattr(ctx, "defaultCase", None) and ctx.defaultCase()
            if d:
                self.visit(d)
        finally:
            self.switch_depth -= 1
        return None

    def visitSwitchCase(self, ctx):
        # 'case' expression ':' statement*
        ex = ctx.expression()
        ex_ty = self.visit(ex) if ex else Type.NULL
        self._expect_bool(ex or ctx, ex_ty)

        for st in (ctx.statement() or []):
            self.visit(st)
        return None


    def visitDefaultCase(self, ctx):
        # 'default' ':' statement*
        for st in (ctx.statement() or []):
            self.visit(st)
        return None
    

    def visitTryCatchStatement(self, ctx):
        # try block 'catch' '(' Identifier ')' block
        blocks = ctx.block() or []
        if len(blocks) >= 1:
            self.visit(blocks[0])  # try { ... }
        if len(blocks) >= 2:
            self.visit(blocks[1])  # catch (...) { ... }
        return None



    # Types
    def visitBaseType(self, ctx):
        ty = self._type_of(ctx)
        return self._set(ctx, ty)

    def visitType(self, ctx):
        ty = self._type_of(ctx)
        return self._set(ctx, ty)

        

    def _type_of(self, tctx):
        if tctx is None:
            return Type.NULL
        
        text = tctx.getText() 
        
        dims = text.count("[]")
        
        base_name = text.replace("[]", "")

        prim = {
            "int": Type.INT, "integer": Type.INT,
            "float": Type.FLOAT,
            "bool": Type.BOOL, "boolean": Type.BOOL,
            "string": Type.STRING,
            "void": Type.VOID,
            "null": Type.NULL
        }.get(base_name, None)

        if prim is not None:
            base = prim
        else:
            sym = self.current.resolve(base_name)
            if isinstance(sym, ClassSymbol):
                base = sym
            else:
                self.errors.err_ctx(tctx, f"Tipo desconocido '{base_name}'")
                base = Type.NULL

        return ArrayType(base, dims) if dims > 0 else base
    