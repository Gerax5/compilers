from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from antlr4 import InputStream, CommonTokenStream # type: ignore
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from antlr4 import ParseTreeWalker # type: ignore
from src.utils.Temp import TempManager
from src.codeGenerator.CodeGenerator import CodeGenerator

from src.utils.Errors import Error
from src.symbolTable.SymbolTableBuilder import SymbolTableBuilder
from src.typeChecker.TypeChecker import TypeChecker
from fastapi.staticfiles import StaticFiles
from src.utils.Types import Type, ArrayType

import re

_TYPE_NAMES = {
    Type.INT: "int",
    Type.FLOAT: "float",
    Type.BOOL: "bool",
    Type.STRING: "string",
    Type.VOID: "void",
    Type.NULL: "null",
}

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

class AnalyzeReq(BaseModel):
    code: str

def _ty_to_str(t):
    if isinstance(t, ArrayType):
        base = _ty_to_str(t.base)
        return base + "[]" * t.dimensions
    
    if hasattr(t, "kind") and getattr(t, "kind") == "class":
        return getattr(t, "name", "class")

    if t in _TYPE_NAMES:
        return _TYPE_NAMES[t]
    return str(t)

def _param_to_json(p):
    return {
        "name": getattr(p, "name", "?"),
        "type": _ty_to_str(getattr(p, "ty", Type.NULL)),
    }

def _sym_to_json(sym):
    kind = getattr(sym, "kind", None)
    name = getattr(sym, "name", "?")

    def mem_meta(s):
        return {
            "size": getattr(s, "size", None),
        }

    if kind in ("var", "const") or hasattr(sym, "is_const"):
        is_const = getattr(sym, "is_const", False)
        base = {
            "kind": "const" if is_const else "var",
            "name": name,
            "type": _ty_to_str(getattr(sym, "ty", Type.NULL)),
        }

        return {**base, **mem_meta(sym)}
    
    if kind == "func":
        ret = _ty_to_str(getattr(sym, "ty", Type.VOID))
        params = [ _param_to_json(p) for p in getattr(sym, "params", []) ]
        base = {
            "kind": "func",
            "name": name,
            "returnType": ret,
            "params": params,
        }
        return {**base, **mem_meta(sym)}
    
    if kind == "class":
        sup = getattr(sym, "superclass", None)
        super_name = getattr(sup, "name", None) if sup else None
        base = {
            "kind": "class",
            "name": name,
            "super": super_name,
        }
        return {**base, **mem_meta(sym)}
    
    return {"kind": kind or "symbol", "name": name, **mem_meta(sym)}

def _build_symtab_json(global_scope, scopes_dict_values):
    all_scopes = set([global_scope])
    for sc in list(scopes_dict_values):
        all_scopes.add(sc)

    id_by_scope = {}
    ordered = list(all_scopes)
    for i, sc in enumerate(ordered):
        id_by_scope[sc] = f"sc_{i}"

    children = { id_by_scope[sc]: [] for sc in all_scopes }
    for sc in all_scopes:
        parent = getattr(sc, "parent", None)
        if parent and parent in id_by_scope:
            children[id_by_scope[parent]].append(id_by_scope[sc])

    node_data = {}
    for sc in all_scopes:
        sid = id_by_scope[sc]
        syms = getattr(sc, "symbols", {}) or {}
        sym_list = []
        for _name, _sym in syms.items():
            sym_list.append(_sym_to_json(_sym))
        sym_list.sort(key=lambda x: (x.get("kind",""), x.get("name","")))
        node_data[sid] = {
            "id": sid,
            "name": getattr(sc, "name", "scope"),
            "symbols": sym_list,
            "children": [],
        }

    for parent_id, childs in children.items():
        for cid in childs:
            node_data[parent_id]["children"].append(node_data[cid])

    return node_data[id_by_scope[global_scope]]

def _errors_to_json(errors_list):
    out = []
    rx = re.compile(r"\[line (\d+):(\d+)\]\s*(.*)")
    for e in errors_list:
        m = rx.match(e)
        if m:
            out.append({"line": int(m.group(1)), "col": int(m.group(2)), "msg": m.group(3), "severity": "error"})
        else:
            out.append({"line": None, "col": None, "msg": e, "severity": "error"})
    return out

@app.post("/analyze")
def analyze(req: AnalyzeReq):
    input_stream = InputStream(req.code)
    lexer = CompiscriptLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = CompiscriptParser(tokens)
    tree = parser.program()

    errors = Error()
    walker = ParseTreeWalker()
    st = SymbolTableBuilder(errors)
    walker.walk(st, tree)

    tc = TypeChecker(st.scopes, st.globalScope, errors, parser)
    tc.visit(tree)

    temp_manager = TempManager()
    generator = CodeGenerator(temp_manager)
    generator.visit(tree)

    tac = generator.quadruples  # lista de {id, op, arg1, arg2, result}

    # símbolos globales rápidos para la vista
    globalsyms = sorted(list(st.globalScope.symbols.keys()))
    symtab_root = _build_symtab_json(st.globalScope, list(st.scopes.values()))

    return {
        "errors": _errors_to_json(errors.errors), 
        "globals": globalsyms, 
        "symtab": symtab_root,
        "tac": tac
    }
