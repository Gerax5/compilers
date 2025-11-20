from .print import MipsPrinter
from .strutil import StrUtil
from .vars import VarUtil
from src.utils.Types import Type, ArrayType
from .arrayutil import ArrayUtil
from .functionmanager import FunctionManager
from .classmanager import ClassManager


class MIPSGenerator:
    def __init__(self, quadruples, symbol_table):
        self.quadruples = quadruples
        self.output = []
        self.variables = set()
        self.strings = {}
        self.concat_temps = {}
        self.pending_params = []
        self.function_quads = []
        self.class_quads = []
        self.main_quads = []
        self.temp_count = 0
        self.symbol_table = symbol_table
        self.types = {}
        self.arrays = {}
        self.varutil = VarUtil()
        self.strutil = StrUtil()
        self.funcman = FunctionManager()
        self.classman = ClassManager()
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
            if self.funcman.is_param(a):
                param_reg = self.funcman.resolve_var(a) 
                parts.append(param_reg)
            else:
                parts.append(a)

        if isinstance(b, str) and b in self.concat_temps:
            parts += self.concat_temps[b]
        else:
            if self.funcman.is_param(b):
                param_reg = self.funcman.resolve_var(b) 
                parts.append(param_reg)
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
        
        if self.funcman.is_param(val):
            param_reg = self.funcman.resolve_var(val) 
            return [f"\tlw {reg}, {param_reg}"]
        
        return [f"\tlw {reg}, {val}"]

    def getVariable(self, value):
        return self.strings[value]
    
    def _is_array(self, t):
        return isinstance(t, ArrayType)

    def generate(self):
        self.scan_classes()
        # 1) Analizar qué elementos se deben declarar
        isFunction = False
        inFunction = None
        inClass = None
        for q in self.quadruples:
            if q["op"] == "label" and q["result"].startswith("func_"):
                isFunction = True

            if q["op"] == "class":
                inClass = q["result"]   # Animal
                self.class_quads.append(q)
                continue

            if q["op"] == "endclass":
                self.class_quads.append(q)
                inClass = None
                continue

            if inClass:
                self.class_quads.append(q)

                if q["op"] == "endfunc":
                    inFunction = None
                    isFunction = False

            elif isFunction:
                if q["op"] == "endfunc":
                    inFunction = None
                    isFunction = False
                self.function_quads.append(q)
            else:
                self.main_quads.append(q)

            if q["op"] == "newarr":
                size = q["arg2"]
                arrname = q["result"]
                self.arrayutil.declare_array(arrname, size)
                continue

            for key in ("result", "arg1", "arg2"):
                val = q[key]
                if val is None:
                    continue

                if key == "arg1" and q["op"] == "call":
                    continue  # función

                if key == "result" and q["op"] == "endfunc":
                    continue  # endfunc
 
                if key == "result" and q["op"] == "label" and val.startswith("func_"):
                    inFunction = val
                    continue  # función
                    
                if q["op"] == "call":
                    continue  # llamada


                if self._is_string_literal(val):
                    if val not in self.strings:
                        label = f"str{len(self.strings)}"
                        self.strings[val] = label
                    continue

                elif isinstance(val, str):
                    if not ((val in self.symbol_table) and (self.symbol_table[val].ty == Type.STRING)):
                        if inClass:
                            if inFunction:
                                if q["op"] == "setprop" and q["arg1"] == "this":
                                    self.variables.add(f"var_{inClass}_{val}")
                                else:
                                    self.variables.add(f"{inFunction}_{val}")
                            else:
                                self.variables.add(f"{inClass}_{val}")
                        elif inFunction:
                            self.variables.add(f"{inFunction}_{val}")
                        else:
                            self.variables.add(val)
                elif val in self.symbol_table and self._is_array(self.symbol_table.get(val).ty):
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

        for q in self.main_quads:
            self.translate(q)

        self.output.append("\n\tli $v0, 10")
        self.output.append("\tsyscall")

        for q in self.function_quads:
            self.translate(q)

        for q in self.class_quads:
            self.translate(q)

        return "\n".join(self.output)

    def scan_classes(self):
        inClass = None

        for q in self.quadruples:
            if q["op"] == "class":
                inClass = q["result"]
                self.classman.begin_class(inClass)
                continue

            if q["op"] == "endclass":
                self.classman.end_class()
                inClass = None
                continue

            if inClass and q["op"] == "label" and q["result"].startswith("func_"):
                _, class_name, method_name = q["result"].split("_", 2)
                self.classman.add_method(method_name)

            # Registrar atributos AUTOMÁTICAMENTE
            if inClass and q["op"] == "setprop":
                # q = setprop this, field, value
                if q["arg1"] == "this":
                    field = q["arg2"]
                    self.classman.add_field(field)

    def translate(self, q):
        op = q["op"]
        arg1 = q["arg1"]
        arg2 = q["arg2"]
        res  = q["result"]

        # Sanear nombres (solo para strings/vars, NO para enteros)
        if isinstance(res, str):
            if not res.startswith("func_"):
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

        elif op == ">":
            self.output += self._load("$t0", arg1)
            self.output += self._load("$t1", arg2)

            # Implementación: t2 = (t1 < t0)
            self.output += [
                f"\tslt $t2, $t1, $t0",
                f"\tsw $t2, {res}",
            ]

        elif op == "<":        # MENOR QUE
            self.output += self._load("$t0", arg1)
            self.output += self._load("$t1", arg2)
            # t2 = (arg1 < arg2)
            self.output += [
                f"\tslt $t2, $t0, $t1",
                f"\tsw $t2, {res}",
            ]
        elif op == ">=":       # MAYOR O IGUAL
            self.output += self._load("$t0", arg1)
            self.output += self._load("$t1", arg2)
            # t2 = !(arg1 < arg2)
            # slt t3, t0, t1 → t3 = arg1<arg2
            # xori t2, t3, 1 → negación
            self.output += [
                f"\tslt $t3, $t0, $t1",
                f"\txori $t2, $t3, 1",
                f"\tsw $t2, {res}",
            ]

        elif op == "<=":       # MENOR O IGUAL
            self.output += self._load("$t0", arg1)
            self.output += self._load("$t1", arg2)
            # t2 = !(arg1 > arg2)
            # slt t3, t1, t0 → arg1>arg2
            # xori t2, t3, 1
            self.output += [
                f"\tslt $t3, $t1, $t0",
                f"\txori $t2, $t3, 1",
                f"\tsw $t2, {res}",
            ]

        elif op == "==":       # IGUALDAD
            self.output += self._load("$t0", arg1)
            self.output += self._load("$t1", arg2)
            # t2 = (arg1 == arg2)
            # sub t3 = t0 - t1 → 0 si iguales
            # sltiu t2, t3, 1 → 1 si t3 < 1 → t3=0
            self.output += [
                f"\tsub $t3, $t0, $t1",
                f"\tsltiu $t2, $t3, 1",
                f"\tsw $t2, {res}",
            ]

        elif op == "!=":       # DIFERENTE
            self.output += self._load("$t0", arg1)
            self.output += self._load("$t1", arg2)
            # t2 = (arg1 != arg2)
            # sub t3 = t0 - t1
            # sltiu t4, t3, 1 → t4=1 si t3=0 (iguales)
            # xori  t2, t4, 1 → invierte (1 si distintos)
            self.output += [
                f"\tsub $t3, $t0, $t1",
                f"\tsltiu $t4, $t3, 1",
                f"\txori $t2, $t4, 1",
                f"\tsw $t2, {res}",
            ]

        elif op == "ifFalse":
            self.output += self._load("$t0", arg1)
            raw = res.replace("var_", "").replace("tmp_", "")
            self.output.append(f"\tbeq $t0, $zero, {raw}")
            return

        elif op == "goto":
            raw = res.replace("var_", "").replace("tmp_", "")
            self.output.append(f"\tj {raw}")
            return

        elif op == "label" and res.startswith("func_"):
            if self.classman.current_class:
                _, class_name, method_name = res.split("_", 2)
                self.classman.add_method(method_name)
                self.output += self.funcman.begin_function(res)
                return
            
            self.output += self.funcman.begin_function(res)
            return

        elif op == "label":
            raw = res.replace("var_", "").replace("tmp_", "")
            self.output.append(f"{raw}:")
            return
        
        if op == "setprop":
            inst = arg1           # this
            field = arg2
            value = res

            class_name = self.classman.current_class
            storage = self.classman.resolve_field(class_name, field)

            self.output += [
                f"\tlw $t0, {value}",
                f"\tsw $t0, {storage}"
            ]
            return

        if op == "getprop":
            inst = arg1
            field = arg2
            dest = res

            class_name = self.classman.current_class
            storage = self.classman.resolve_field(class_name, field)

            self.output += [
                f"\tlw $t0, {storage}",
                f"\tsw $t0, {dest}"
            ]
            return

        if op == "getmethod":
            inst = arg1.replace("var_", "").replace("tmp_", "")
            method = arg2.replace("var_", "").replace("tmp_", "")       # speak
            dest = res          # t1

            # 1. Obtener clase de la instancia
            class_name = self.classman.get_instance_class(dest)
            if class_name is None:
                raise Exception(f"No se conoce la clase de instancia '{inst}'")

            # 2. Resolver etiqueta de método
            label = self.classman.resolve_method_label(class_name, method)

            self.types[dest] = q["retType"]

            # 3. Guardar la etiqueta como un "puntero" (la etiqueta misma)
            self.output.append(f"\tla $t0, {label}")
            self.output.append(f"\tsw $t0, {dest}")
            return

        if op == "new":
            class_name = arg1.replace("var_", "").replace("tmp_", "")
            obj = res

            self.classman.map_instance(obj, class_name)

            raw = class_name.replace("var_", "").replace("tmp_", "")
            size =  self.classman.class_sizes[raw]   # por ejemplo {"Animal": 4}
            
            self.output += [
                "\tli $v0, 9",             # sbrk
                f"\tli $a0, {size}",       # bytes
                "\tsyscall",               # $v0 = ptr
                f"\tsw $v0, {obj}",        # guardar el puntero en t1
            ]

            if "constructor" in self.classman.classes[class_name]["methods"]:
                # llamar constructor si existe
                ctor = f"func_{class_name}_constructor"

                self.output += [
                    f"\tlw $a0, {obj}",        # this
                    f"\tjal {ctor}"            # constructor()
                ]
            return



        if op == "param":
            self.funcman.add_param(self.funcman.current_function, res)
            self.output += self.funcman.save_params_to_memory()
            return
        
        if op == "call_param":
            self.pending_params.append(arg1)
            return

        if op == "return":

            if self._is_string_literal(arg1):
                label = self.strings[arg1]   # ejemplo: "HOLA" → str0
                self.output.append(f"\tla $v0, {label}")
                self.output += self.funcman.end_function()
                return
            
            # if self.is_string(arg1):
            #     # Debes asegurar que 'arg1' tiene un label generado por concat
            #     label = self.strutil.concat_to_mips(self, arg1)
            #     self.output.append(f"\tla $v0, {label}")
            #     self.output += self.funcman.end_function()
            #     return
            
            reg = self.funcman.resolve_var(arg1)

            if reg.startswith("$"):
                self.output.append(f"\tmove $v0, {reg}")
            else:
                self.output.append(f"\tlw $v0, {reg}")

            self.output += self.funcman.end_function()
            return

        if op == "call":
            func_name = arg1.replace("var_", "func_")
            n = arg2   # number of params

            raw = func_name.replace("func_", "")

            if raw in self.symbol_table:
                if self.symbol_table[raw].ty == Type.STRING:
                    self.types[res] = "string"

            if raw in self.types:
                self.types[res] = self.types[raw]

            if self.classman.current_class:
                pass

            # load arguments into $a0..$a3
            for i, p in enumerate(self.pending_params):
                if isinstance(p, int):
                    self.output.append(f"\tli $a{i}, {p}")
                else:
                    if self.strings.get(p):
                        label = self.strings[p]
                        self.output.append(f"\tla $a{i}, {label}")
                    else:
                        self.output.append(f"\tlw $a{i}, {p}")

            self.pending_params = []

            raw = func_name.replace("func_", "").replace("var_", "").replace("tmp_", "")

            if raw in self.variables:
                self.output.append(f"\tlw $t0, {func_name}")
                func_name = "$t0"

            # if func_name in self.variables

            self.output.append(f"\tjal {func_name}")

            raw = arg1.replace("func_", "").replace("var_", "").replace("tmp_", "")

            self.output.append(f"\tsw $v0, {res}")

            if raw in self.symbol_table and self.symbol_table[raw].ty == Type.STRING:
                self.types[res] = "string"
                self.concat_temps[res] = [("runtime", res)]
            return
        
        if op == "class":
            self.classman.begin_class(res)
            return

        if op == "endclass":
            self.classman.end_class()
            return

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