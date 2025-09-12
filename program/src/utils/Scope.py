from typing import List, Optional
from src.utils.Types import Type

class Symbol:
    def __init__(self, name: str, ty: Type): 
        self.name, self.ty = name, ty
        self.kind = None

class VarSymbol(Symbol): 
    def __init__(self, name, ty, is_const=False, value=None, owner=None):
        super().__init__(name, ty)
        self.kind = 'const' if is_const else 'var'
        self.value = value
        self.owner = owner

class FuncSymbol(Symbol):
    def __init__(self, name: str, ret: Type, params: list[Symbol]):
        super().__init__(name, ret)
        self.kind = 'func'
        self.params = params

class ClassSymbol(Symbol):
    def __init__(self, name: str, superclass: Optional["ClassSymbol"] = None):
        super().__init__(name, None)
        self.kind = 'class'
        self.superclass = superclass
        self.fields: dict[str, Symbol] = {}
        self.methods: dict[str, FuncSymbol] = {}
        self.scope: Scope|None = None

    def resolve_member(self, member: str):
        c: ClassSymbol | None = self
        while c:
            sc = getattr(c, "scope", None)
            if sc:
                s = sc.resolve(member)
                if s:
                    return s
            c = getattr(c, "superclass", None)
        return None

class Scope:
    def __init__(self, parent=None, name="<scope>", owner=None):
        self.parent, self.name, self.symbols, self.owner = parent, name, {}, owner
    def define(self, sym: Symbol):
        if sym.name in self.symbols: return False
        self.symbols[sym.name] = sym; return True
    def resolve(self, name: str):
        s = self.symbols.get(name)
        return s if s else (self.parent.resolve(name) if self.parent else None)