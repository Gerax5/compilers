from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from antlr4 import InputStream, CommonTokenStream # type: ignore
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from antlr4 import ParseTreeWalker # type: ignore

from src.utils.Errors import Error
from src.symbolTable.SymbolTableBuilder import SymbolTableBuilder
from src.typeChecker.TypeChecker import TypeChecker
from fastapi.staticfiles import StaticFiles



import re

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

class AnalyzeReq(BaseModel):
    code: str

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

    # símbolos globales rápidos para la vista
    globalsyms = sorted(list(st.globalScope.symbols.keys()))
    return {"errors": _errors_to_json(errors.errors), "globals": globalsyms}
