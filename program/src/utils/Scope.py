from typing import List, Optional
from src.utils.Types import Type

class Symbol:
    def __init__(self, name: str, ty: Type): 
        self.name, self.ty = name, ty
        self.kind = None

class VarSymbol(Symbol): 
    def __init__(self, name, ty, is_const=False, value=None):
        super().__init__(name, ty)
        self.kind = 'const' if is_const else 'var'
        self.value = value

class FuncSymbol(Symbol):
    def __init__(self, name: str, ret: Type, params: list[Symbol]):
        super().__init__(name, ret)
        self.kind = 'func'
        self.params = params

class ClassSymbol(Symbol):
    def __init__(self, name: str):
        super().__init__(name, None)
        self.kind = 'class'
        self.fields: dict[str, Symbol] = {}
        self.methods: dict[str, FuncSymbol] = {}
        self.scope: Scope|None = None

class Scope:
    def __init__(self, parent=None, name="<scope>"):
        self.parent, self.name, self.symbols = parent, name, {}
    def define(self, sym: Symbol):
        if sym.name in self.symbols: return False
        self.symbols[sym.name] = sym; return True
    def resolve(self, name: str):
        s = self.symbols.get(name)
        print("ESEEEE",name, s, self.parent)
        return s if s else (self.parent.resolve(name) if self.parent else None)