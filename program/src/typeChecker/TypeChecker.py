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
    
    def _apply_assignment(self, name, rhs_ty, ctx):
        sym: VarSymbol = self.current.resolve(name)
        if not sym:
            self.errors.err_ctx(ctx, f"'{name}' no declarado")
            return self._set(ctx, rhs_ty)
        if sym.kind == 'const':
            self.errors.err_ctx(ctx, f"No se puede asignar a const '{name}'")
            return self._set(ctx, sym.ty)
        if not self._can_assign(sym.ty, rhs_ty):
            self.errors.err_ctx(ctx, f"Asignación incompatible: {sym.ty} = {rhs_ty}")
        return self._set(ctx, sym.ty)

    def _apply_property_assignment(self, recv_ty, prop, rhs_ty, ctx):
        if not (hasattr(recv_ty, "kind") and recv_ty.kind == "class"):
            self.errors.err_ctx(ctx, f"No se puede asignar propiedad '{prop}' sobre tipo {recv_ty}")
            return self._set(ctx, rhs_ty)
        cls_scope = getattr(recv_ty, "scope", None)
        psym = cls_scope and cls_scope.resolve(prop)
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

            dims = elem_types[0].dimensions
            if any(t.dimensions != dims for t in elem_types):
                self.errors.err_ctx(ctx, "Arreglo irregular: dimensiones distintas entre elementos.")
                return self._set(ctx, ArrayType(Type.NULL, dims))

            base = elem_types[0].base
            for t in elem_types[1:]:
                ub = self._unify_base(base, t.base)
                if ub is None:
                    self.errors.err_ctx(ctx, f"Tipos incompatibles en arreglo: {base} y {t.base}")
                    return self._set(ctx, ArrayType(Type.NULL, dims))
                base = ub

            return self._set(ctx, ArrayType(base, dims))

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
            # x = 10
            rhs_ty = self.visit(exps[0])
            return self._apply_assignment(left, rhs_ty, ctx)

        elif len(exps) == 2:
            # this.x = 10
            recv_ty = self.visit(exps[0])
            rhs_ty  = self.visit(exps[1])
            return self._apply_property_assignment(recv_ty, left, rhs_ty, ctx)

        return self.visitChildren(ctx)

        # return self._check_assignment(left, right, ctx)

        # print(right_ty)

    def visitAssignExpr(self, ctx):
        # print("AASIGN EXPR")
        # print(ctx.getChildCount())
        # print(ctx.getChild(0).getText())
        pass


    
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
        print(ty)
        if not self._can_assign(expected, ty):
            self.errors.err_ctx(ctx, f"return: esperado {expected}, recibido {ty}")
        return self._set(ctx, expected)

    # ADD
    def visitAdditiveExpr(self, ctx):
        n = ctx.getChildCount()

        if n == 1: # Por alguna razon entra aqui lol no entiendo
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

    def _type_of(self, tctx):
        if tctx is None:
            return Type.NULL
        
        text = tctx.getText() 
        
        dims = text.count("[]")
        
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
    