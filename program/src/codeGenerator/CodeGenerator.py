from CompiscriptVisitor import CompiscriptVisitor
from src.utils.Errors import Error
from src.utils.Scope import VarSymbol, Type, ClassSymbol, FuncSymbol, Scope
from src.utils.Types import Type, ArrayType
from CompiscriptListener import CompiscriptListener
from CompiscriptParser import CompiscriptParser
from antlr4.tree.Tree import TerminalNode # type: ignore

from CompiscriptVisitor import CompiscriptVisitor

class CodeGenerator(CompiscriptVisitor):
    def __init__(self, temp_manager):
        self.temp_manager = temp_manager
        self.quadruples = []
        self.counter = 0

        self.label_counter = 0
        self.loop_stack = []
        self.switch_stack = []

    def emit(self, op, arg1, arg2, result):
        quad = {
            "id": self.counter,
            "op": op,
            "arg1": arg1,
            "arg2": arg2,
            "result": result
        }
        self.quadruples.append(quad)
        self.counter += 1
        return quad["id"]
    
    def new_label(self, hint="L"):
        self.label_counter += 1
        return f"{hint}{self.label_counter}"

    
    # EXPR
    def visitAdditiveExpr(self, ctx):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.getChild(0))

        result = self.visit(ctx.getChild(0))
        i = 1
        while i < ctx.getChildCount():
            op = ctx.getChild(i).getText()
            right = self.visit(ctx.getChild(i + 1))
            temp = self.temp_manager.new_temp()
            self.emit(op, result, right, temp)

            # liberar temporales ya usados
            if isinstance(result, str) and result.startswith("t"):
                self.temp_manager.release_temp(result)
            if isinstance(right, str) and right.startswith("t"):
                self.temp_manager.release_temp(right)

            result = temp
            i += 2

        return result

    def visitEqualityExpr(self, ctx):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.getChild(0))

        left = self.visit(ctx.getChild(0))
        right = self.visit(ctx.getChild(2))
        op = ctx.getChild(1).getText()  

        temp = self.temp_manager.new_temp()
        self.emit(op, left, right, temp)

        if isinstance(left, str) and left.startswith("t"):
            self.temp_manager.release_temp(left)
        if isinstance(right, str) and right.startswith("t"):
            self.temp_manager.release_temp(right)

        return temp

    def visitLogicalAndExpr(self, ctx):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.getChild(0))

        left = self.visit(ctx.getChild(0))
        right = self.visit(ctx.getChild(2))

        result = self.temp_manager.new_temp()
        Lfalse = f"L{len(self.quadruples)+1}_false"
        Lend = f"L{len(self.quadruples)+3}_end"

        self.emit("ifFalse", left, None, Lfalse)
        self.emit("ifFalse", right, None, Lfalse)
        self.emit("=", "1", None, result)
        self.emit("goto", None, None, Lend)

        self.emit("label", None, None, Lfalse)
        self.emit("=", "0", None, result)

        self.emit("label", None, None, Lend)

        return result

    def visitLogicalOrExpr(self, ctx):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.getChild(0))

        left = self.visit(ctx.getChild(0))
        right = self.visit(ctx.getChild(2))

        result = self.temp_manager.new_temp()
        Ltrue = f"L{len(self.quadruples)+1}_true"
        Lend = f"L{len(self.quadruples)+3}_end"

        self.emit("ifTrue", left, None, Ltrue)
        self.emit("ifTrue", right, None, Ltrue)
        self.emit("=", "0", None, result)
        self.emit("goto", None, None, Lend)

        self.emit("label", None, None, Ltrue)
        self.emit("=", "1", None, result)

        self.emit("label", None, None, Lend)

        return result

    def visitUnaryExpr(self, ctx):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.getChild(0))

        op = ctx.getChild(0).getText()   
        expr_val = self.visit(ctx.getChild(1))

        temp = self.temp_manager.new_temp()

        if op == "-":
            self.emit("-", 0, expr_val, temp)

        elif op == "!":
            self.emit("not", expr_val, None, temp)

        if isinstance(expr_val, str) and expr_val.startswith("t"):
            self.temp_manager.release_temp(expr_val)

        return temp

    # IF
    def visitIfStatement(self, ctx):
        cond_place = self.visit(ctx.expression())

        else_label = f"L{len(self.quadruples)}_else"
        end_label  = f"L{len(self.quadruples)}_end"

        self.emit("ifFalse", cond_place, None, else_label)

        if ctx.block(0):
            self.visit(ctx.block(0))

        if ctx.block(1):
            self.emit("goto", None, None, end_label)

        self.emit("label", None, None, else_label)
        if ctx.block(1):   
            self.visit(ctx.block(1))

        if ctx.block(1):
            self.emit("label", None, None, end_label)

        return None


    # FUNCTION
    def visitFunctionDeclaration(self, ctx):
        fname = ctx.Identifier().getText()

        func_label = f"func_{fname}"
        self.emit("label", None, None, func_label)

        params_ctx = ctx.parameters()
        if params_ctx:
            for p in params_ctx.parameter():
                pname = p.Identifier().getText()
                self.emit("param", None, None, pname)

        body = ctx.block()
        if body:
            self.visit(body)

        self.emit("endfunc", None, None, fname)
        return None

    def visitReturnStatement(self, ctx):
        expr = getattr(ctx, "expression", None) and ctx.expression()

        if expr:
            ret_val = self.visit(expr)
            self.emit("return", ret_val, None, None)

            if isinstance(ret_val, str) and ret_val.startswith("t"):
                self.temp_manager.release_temp(ret_val)
        else:
            self.emit("return", None, None, None)

        return None

    def visitLeftHandSide(self, ctx):
        cur = self.visit(ctx.primaryAtom())

        for suf in (ctx.suffixOp() or []):
            kind = suf.getChild(0).getText()

            if kind == '(':
                args_ctx = getattr(suf, "arguments", None) and suf.arguments()
                args = (args_ctx.expression() if args_ctx else [])
                arg_vals = [self.visit(e) for e in args]

                for val in arg_vals:
                    self.emit("param", val, None, None)

                temp = self.temp_manager.new_temp()
                self.emit("call", cur, len(arg_vals), temp)

                # si cur era un temporal, liberarlo
                if isinstance(cur, str) and cur.startswith("t"):
                    self.temp_manager.release_temp(cur)

                cur = temp
                continue

            # --- indexación ---
            if kind == '[':
                idx_val = self.visit(suf.expression())
                temp = self.temp_manager.new_temp()
                self.emit("[]", cur, idx_val, temp)

                if isinstance(cur, str) and cur.startswith("t"):
                    self.temp_manager.release_temp(cur)
                if isinstance(idx_val, str) and idx_val.startswith("t"):
                    self.temp_manager.release_temp(idx_val)

                cur = temp
                continue

            # --- acceso a propiedad ---
            if kind == '.':
                prop = suf.Identifier().getText()
                temp = self.temp_manager.new_temp()
                self.emit("getprop", cur, prop, temp)

                if isinstance(cur, str) and cur.startswith("t"):
                    self.temp_manager.release_temp(cur)

                cur = temp
                continue

        return cur


    # CLASS
    def visitClassDeclaration(self, ctx):
        idents = ctx.Identifier()
        if isinstance(idents, list):
            name = idents[0].getText()
            super_name = idents[1].getText() if len(idents) > 1 else None
        else:
            name = idents.getText()
            super_name = None

        self.emit("class", super_name, None, name)

        for member in ctx.classMember() or []:
            self.visit(member)

        self.emit("endclass", None, None, name)
        return name

    def visitNewExpr(self, ctx):
        cname = ctx.Identifier().getText()
        args_ctx = ctx.arguments()
        args = args_ctx.expression() if args_ctx else []

        for arg in args:
            arg_val = self.visit(arg)
            self.emit("param", arg_val, None, None)

        temp = self.temp_manager.new_temp()
        self.emit("new", cname, len(args), temp)
        return temp
    
    def visitThisExpr(self, ctx):
        return "this"
    
    def visitClassMember(self, ctx):
        if hasattr(ctx, "functionDeclaration") and ctx.functionDeclaration():
            return self.visit(ctx.functionDeclaration())
        if hasattr(ctx, "variableDeclaration") and ctx.variableDeclaration():
            return self.visit(ctx.variableDeclaration())
        if hasattr(ctx, "constantDeclaration") and ctx.constantDeclaration():
            return self.visit(ctx.constantDeclaration())
        return self.visitChildren(ctx)

    def visitPropertyAccessExpr(self, ctx):
        recv_place = self.visit(ctx.getChild(0))

        prop = ctx.Identifier().getText() if ctx.Identifier() else ctx.getChild(1).getText()

        temp = self.temp_manager.new_temp()
        self.emit("getprop", recv_place, prop, temp)

        if recv_place and str(recv_place).startswith("t"):
            self.temp_manager.release_temp(recv_place)

        return temp

    def visitMultiplicativeExpr(self, ctx):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.getChild(0))

        left = self.visit(ctx.getChild(0))
        op = ctx.getChild(1).getText()
        right = self.visit(ctx.getChild(2))

        temp = self.temp_manager.new_temp()
        self.emit(op, left, right, temp)

        # Liberar temporales ya usados
        if isinstance(left, str) and left.startswith("t"):
            self.temp_manager.release_temp(left)
        if isinstance(right, str) and right.startswith("t"):
            self.temp_manager.release_temp(right)

        return temp
    
    def visitRelationalExpr(self, ctx):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.getChild(0))

        # a < b
        left = self.visit(ctx.getChild(0))
        op = ctx.getChild(1).getText()
        right = self.visit(ctx.getChild(2))

        # Crear temporal para guardar el resultado (boolean)
        temp = self.temp_manager.new_temp()
        self.emit(op, left, right, temp)

        # Liberar temporales usados
        if isinstance(left, str) and left.startswith("t"):
            self.temp_manager.release_temp(left)
        if isinstance(right, str) and right.startswith("t"):
            self.temp_manager.release_temp(right)

        return temp
    
    # Herencia
    def visitThisExpr(self, ctx):
        return "this"

    def visitSuperExpr(self, ctx):
        # place simbólico el runtime/VM debe despachar al método de la superclase
        return "super"


    # EXTRA FUNCTION
    def visitPrintStatement(self, ctx):
        expr = ctx.expression()
        if expr:
            val = self.visit(expr)
            self.emit("print", val, None, None)
            if isinstance(val, str) and val.startswith("t"):
                self.temp_manager.release_temp(val)

    # Variables
    def visitAssignment(self, ctx):
        left = ctx.Identifier().getText()
        exps = ctx.expression() or []

        if len(exps) == 1:
            rhs_place = self.visit(exps[0])
            self.emit("=", rhs_place, None, left)

            if rhs_place and str(rhs_place).startswith("t"):
                self.temp_manager.release_temp(rhs_place)

            return left

        elif len(exps) == 2:
            print(exps[0].getText())
            recv_place = self.visit(exps[0])
            rhs_place  = self.visit(exps[1])
            self.emit("setprop", recv_place, rhs_place, left)

            if rhs_place and str(rhs_place).startswith("t"):
                self.temp_manager.release_temp(rhs_place)

            return left

        return self.visitChildren(ctx)
    
    def visitIndexExpr(self, ctx):
        arr_place = self.visit(ctx.parentCtx.getChild(0))
        idx_place = self.visit(ctx.expression())

        temp = self.temp_manager.new_temp()
        self.emit("[]", arr_place, idx_place, temp)

        if arr_place and str(arr_place).startswith("t"):
            self.temp_manager.release_temp(arr_place)
        if idx_place and str(idx_place).startswith("t"):
            self.temp_manager.release_temp(idx_place)

        return temp
    
    def visitVariableDeclaration(self, ctx):
        print("a")
        name = ctx.Identifier().getText()
        init = getattr(ctx, "initializer", None) and ctx.initializer()
        if init:
            val = self.visit(init.expression())
            self.emit("=", val, None, name)
            if isinstance(val, str) and val.startswith("t"):
                self.temp_manager.release_temp(val)
        return name
    
    def visitLiteralExpr(self, ctx):
        text = ctx.getText()
        if text.isdigit():
            return int(text)
        try:
            return float(text)
        except ValueError:
            pass
        if text == "true": return True
        if text == "false": return False
        if text.startswith('"') and text.endswith('"'):
            return text.strip('"')
        return text
    
    def visitPrimaryExpr(self, ctx):
        if ctx.getChildCount() == 3 and ctx.getChild(0).getText() == '(' and ctx.getChild(2).getText() == ')':
            return self.visit(ctx.getChild(1))
        return self.visitChildren(ctx)
    
    def visitArrayLiteralExpr(self, ctx):
        print("HOAL")
        elems = ctx.expression() or []

        size = len(elems)

        arr_temp = self.temp_manager.new_temp()
        self.emit("newarr", "int", size, arr_temp)

        for i, e in enumerate(elems):
            val = self.visit(e)
            self.emit("[]=", arr_temp, i, val)

            if isinstance(val, str) and val.startswith("t"):
                self.temp_manager.release_temp(val)

        return arr_temp

    def visitArrayLiteral(self, ctx):
        elems = ctx.expression() or []
        size = len(elems)

        arr_temp = self.temp_manager.new_temp()
        self.emit("newarr", "ref", size, arr_temp) 

        for i, e in enumerate(elems):
            val = self.visit(e)
            self.emit("[]=", arr_temp, i, val)

            if isinstance(val, str) and val.startswith("t"):
                self.temp_manager.release_temp(val)

        return arr_temp



    def visitConstantDeclaration(self, ctx):
        name = ctx.Identifier().getText()
        init = ctx.expression()

        if init:
            val = self.visit(init)   
            self.emit("=", val, None, name)

            if isinstance(val, str) and val.startswith("t"):
                self.temp_manager.release_temp(val)

        return name

    def visitPrimaryExpr(self, ctx):
        if ctx.getChildCount() == 3 and ctx.getChild(0).getText() == '(' and ctx.getChild(2).getText() == ')':
            return self.visit(ctx.getChild(1))

        return self.visitChildren(ctx)

    def visitLiteralExpr(self, ctx):
        print("b")
        tok = ctx.getChild(0)
        if not isinstance(tok, TerminalNode):
            return self.visit(tok)

        tok = tok.getText()

        if tok == "true":
            return 1   
        if tok == "false":
            return 0

        if tok.startswith('"') or tok.startswith("'"):
            return tok   

        if tok.replace("_", "").isdigit():
            return int(tok)  

        try:
            return float(tok)
        except ValueError:
            pass

        return tok


    def visitArrayLiteralExpr(self, ctx):
        elems = ctx.expression() or []
        size = len(elems)

        arr_temp = self.temp_manager.new_temp()
        self.emit("newarr", "any", size, arr_temp)

        for i, e in enumerate(elems):
            val = self.visit(e)
            self.emit("[]=", arr_temp, i, val)

            if isinstance(val, str) and val.startswith("t"):
                self.temp_manager.release_temp(val)

        return arr_temp

    # While
    def visitWhileStatement(self, ctx):
        Ltest = self.new_label("Lwhile_test_")
        Lbody = self.new_label("Lwhile_body_")
        Lend  = self.new_label("Lwhile_end_")

        self.loop_stack.append((Ltest, Lend))

        self.emit("label", None, None, Ltest)
        cond = self.visit(ctx.expression())
        self.emit("ifFalse", cond, None, Lend)

        if isinstance(cond, str) and cond.startswith("t"):
            self.temp_manager.release_temp(cond)

        self.emit("label", None, None, Lbody)
        if getattr(ctx, "block", None) and ctx.block():
            self.visit(ctx.block())

        self.emit("goto", None, None, Ltest)
        self.emit("label", None, None, Lend)

        self.loop_stack.pop()
        return None
    
    # Try / Catch
    def visitTryCatchStatement(self, ctx):
        # try block 'catch' '(' Identifier ')' block
        blocks = ctx.block() or []
        try_block = blocks[0] if len(blocks) >= 1 else None
        catch_block = blocks[1] if len(blocks) >= 2 else None

        Lcatch = self.new_label("Lcatch_")
        Lend   = self.new_label("Ltry_end_")

        # Instala handler
        self.emit("trybegin", None, None, Lcatch)

        if try_block:
            self.visit(try_block)

        # Cierra try y salta al final
        self.emit("tryend", None, None, None)
        self.emit("goto", None, None, Lend)

        # Catch
        self.emit("label", None, None, Lcatch)

        # Si hay nombre de excepción, asígnalo
        if getattr(ctx, "Identifier", None) and ctx.Identifier():
            ex_name = ctx.Identifier().getText()
            self.emit("=", "exception", None, ex_name)

        if catch_block:
            self.visit(catch_block)

        self.emit("label", None, None, Lend)
        return None



    # Continue
    def visitContinueStatement(self, ctx):
        if not self.loop_stack:
            # TypeChecker ya reporta el error aquí evita crashear
            return None
        Lcontinue, _ = self.loop_stack[-1]
        self.emit("goto", None, None, Lcontinue)
        return None

    # Break
    def visitBreakStatement(self, ctx):
        # break en bucle rompe el bucle si en switch, rompe el switch
        if self.switch_stack:
            Lbreak = self.switch_stack[-1]
            self.emit("goto", None, None, Lbreak)
            return None
        if self.loop_stack:
            _, Lbreak = self.loop_stack[-1]
            self.emit("goto", None, None, Lbreak)
            return None
        # fuera de contexto TypeChecker ya lo marco
        return None
    
    # Switch
    def visitSwitchStatement(self, ctx):
        # switch (expr) { case v1: ...; case v2: ...; default: ... }
        scrut = self.visit(ctx.expression())

        cases = list(ctx.switchCase() or [])
        default_ctx = ctx.defaultCase()

        case_labels = [self.new_label("Lcase_") for _ in cases]
        Ldefault = self.new_label("Ldefault_") if default_ctx else None
        Lend = self.new_label("Lswitch_end_")

        self.switch_stack.append(Lend)

        for i, sc in enumerate(cases):
            ce = sc.expression()
            cv = self.visit(ce) if ce else None
            t = self.temp_manager.new_temp()
            self.emit("==", scrut, cv, t)
            self.emit("ifTrue", t, None, case_labels[i])

            if isinstance(t, str) and t.startswith("t"):
                self.temp_manager.release_temp(t)
            if isinstance(cv, str) and isinstance(cv, str) and str(cv).startswith("t"):
                self.temp_manager.release_temp(cv)

        # Si no coincidió ningún case, ve a default o fin
        self.emit("goto", None, None, Ldefault if Ldefault else Lend)

        for i, sc in enumerate(cases):
            self.emit("label", None, None, case_labels[i])
            for st in (sc.statement() or []):
                self.visit(st)

        # Default
        if default_ctx:
            self.emit("label", None, None, Ldefault)
            for st in (default_ctx.statement() or []):
                self.visit(st)

        # End del switch
        self.emit("label", None, None, Lend)

        if isinstance(scrut, str) and scrut.startswith("t"):
            self.temp_manager.release_temp(scrut)

        self.switch_stack.pop()
        return None

    def visitIdentifierExpr(self, ctx):
        return ctx.Identifier().getText()
