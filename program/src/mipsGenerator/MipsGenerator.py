from .print import MipsPrinter
from .strutil import StrUtil
from .vars import VarUtil
from src.utils.Types import Type, ArrayType
from .arrayutil import ArrayUtil


class MIPSGenerator:
    def __init__(self, quadruples, symbol_table):
        self.quadruples = quadruples
        self.output = []
        self.variables = set()
        self.strings = {}
        self.concat_temps = {}
        self.temp_count = 0
        self.symbol_table = symbol_table
        self.types = {}
        self.arrays = {}
        self.varutil = VarUtil()
        self.strutil = StrUtil()
        self.printer = MipsPrinter(self)
        self.arrayutil = ArrayUtil(self)

    def _is_string_literal(self, x):
        return isinstance(x, str) and len(x) >= 2 and x[0] == '"' and x[-1] == '"'

    def _safe_var(self, name):
        """
        Devuelve un nombre seguro para MIPS:
        - Si ya está convertido (var_x o tmp_x), no lo toca
        - Si es temporal tipo t1, lo convierte a tmp_t1
        - Si es variable normal, lo convierte a var_name
        """
        if not isinstance(name, str):
            return name

        if name.startswith("var_") or name.startswith("tmp_"):
            return name  # ya está seguro

        if name.startswith("t") and name[1:].isdigit():
            # temporal real (t1, t2...)
            return f"tmp_{name}"

        return f"var_{name}"

    def _safe_temp(self, name):
        """Por si alguna vez llamas esto directo."""
        if not isinstance(name, str):
            return name
        if name.startswith("tmp_"):
            return name
        return f"tmp_{name}"

    def _concat(self, a, b):
        parts = []

        # a puede ser temp, string o var
        if isinstance(a, str) and a in self.concat_temps:
            parts += self.concat_temps[a]  # expandir
        else:
            parts.append(a)

        if isinstance(b, str) and b in self.concat_temps:
            parts += self.concat_temps[b]
        else:
            parts.append(b)

        return parts

    def is_string(self, x):

        if isinstance(x, int):
            return False

        if self._is_string_literal(x):
            return True

        clean_x = x.replace("var_", "").replace("tmp_", "")

        if clean_x in self.symbol_table and self.symbol_table[clean_x].ty == Type.STRING:
            return True

        if x in self.types and self.types[x] == "string":
            return True

        return False

    def _load(self, reg, val):
        if isinstance(val, int):
            return [f"\tli {reg}, {val}"]
        else:
            return [f"\tlw {reg}, {val}"]

    def getVariable(self, value):
        return self.strings[value]
    
    def _is_array(self, t):
        return isinstance(t, ArrayType)

    def generate(self):
        # 1) Analizar qué elementos se deben declarar
        for q in self.quadruples:
            if q["op"] == "newarr":
                size = q["arg2"]
                arrname = q["result"]
                print(arrname, "NAME")
                self.arrayutil.declare_array(arrname, size)
                continue

            for key in ("result", "arg1", "arg2"):
                val = q[key]
                if val is None:
                    continue


                if self._is_string_literal(val):
                    if val not in self.strings:
                        label = f"str{len(self.strings)}"
                        self.strings[val] = label
                    continue

                elif isinstance(val, str):
                    if not ((val in self.symbol_table) and (self.symbol_table[val].ty == Type.STRING)):
                        self.variables.add(val)
                elif val in self.symbol_table and self._is_array(self.symbol_table.get(val).ty):
                    print("array detected:", val)
                    self.variables.add(val)
        
        # 2) Sección de datos
        self.output.append(".data")

        for var in sorted(self.variables):
            safe = self._safe_var(var)
            self.output.append(f"{safe}: .word 0")

        for name, (label, size) in self.arrayutil.arrays.items():
            self.output.append(f"{label}: .space {size*4}")

        for lit, label in self.strings.items():
            text = lit[1:-1]
            self.output.append(f'{label}: .asciiz "{text}"')

        # 3) Sección de código
        self.output.append("\n.text")
        self.output.append("main:")

        for q in self.quadruples:
            self.translate(q)

        self.output.append("\n\tli $v0, 10")
        self.output.append("\tsyscall")

        return "\n".join(self.output)

    def translate(self, q):
        op = q["op"]
        arg1 = q["arg1"]
        arg2 = q["arg2"]
        res  = q["result"]

        # Sanear nombres (solo para strings/vars, NO para enteros)
        if isinstance(res, str):
            res = self._safe_var(res)
        if isinstance(arg1, str) and not self._is_string_literal(arg1):
            arg1 = self._safe_var(arg1)
        if isinstance(arg2, str) and not self._is_string_literal(arg2):
            arg2 = self._safe_var(arg2)

        # ---------- ASIGNACIÓN ----------
        if op == "=":


            
            
            if self._is_string_literal(arg1):
                self.concat_temps[res] = [arg1]
                return

            if self.is_string(arg1):
                self.types[res] = "string"
                self.concat_temps[res] = list(self.concat_temps[arg1])
                return

            clean_res = res.replace("var_", "").replace("tmp_", "")
            if clean_res in self.symbol_table and "[]" in str(self.symbol_table[clean_res].ty):
                self.output += [
                    f"\tlw $t0, {arg1}",
                    f"\tsw $t0, {res}",
                ]
                return
            
            if isinstance(arg1, int):
                self.output += [
                    f"\tli $t0, {arg1}",
                    f"\tsw $t0, {res}",
                ]
            else:
                self.output += [
                    f"\tlw $t0, {arg1}",
                    f"\tsw $t0, {res}",
                ]

        # ---------- SUMA ----------
        elif op == "+":
            if self.is_string(arg1) or self.is_string(arg2):
                self.types[res] = "string"
                self.concat_temps[res] = self._concat(arg1, arg2)
            else:
                self.output += self._load("$t0", arg1)
                self.output += self._load("$t1", arg2)
                self.output += [
                    f"\tadd $t2, $t0, $t1",
                    f"\tsw $t2, {res}",
                ]

        # ---------- RESTA ----------
        elif op == "-":
            self.output += self._load("$t0", arg1)
            self.output += self._load("$t1", arg2)
            self.output += [
                f"\tsub $t2, $t0, $t1",
                f"\tsw $t2, {res}",
            ]

        # ---------- MULT ----------
        elif op == "*":
            self.output += self._load("$t0", arg1)
            self.output += self._load("$t1", arg2)
            self.output += [
                f"\tmul $t2, $t0, $t1",
                f"\tsw $t2, {res}",
            ]

        # ---------- DIV ----------
        elif op == "/":
            self.output += self._load("$t0", arg1)
            self.output += self._load("$t1", arg2)
            self.output += [
                f"\tdiv $t0, $t1",
                f"\tmflo $t2",
                f"\tsw $t2, {res}",
            ]

        elif op == "newarr":
            self.output += self.arrayutil.emit_newarr(res)
            return

        elif op == "[]=":
            self.output += self.arrayutil.emit_store(arg1, arg2, res)
            return

        elif op == "[]":
            self.output += self.arrayutil.emit_load(arg1, arg2, res)
            return

        # ---------- PRINT ----------
        elif op == "print":
            self.printer.emit(arg1)
            return