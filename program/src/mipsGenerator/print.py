from src.utils.Types import Type
class MipsPrinter:
    def __init__(self, gen):
        self.gen = gen      # referencia a MIPSGenerator

    def emit(self, arg):
        print(arg, "EMIT ARG")

        if isinstance(arg, tuple) and arg[0] == "runtime":
            return self._emit_runtime_string(arg[1])

        # A) concatenación
        if isinstance(arg, str) and arg in self.gen.concat_temps:
            return self._emit_concat(arg)
            

        # B) string literal
        if self.gen.strutil.is_literal(arg):
            return self._emit_literal(arg)

        
        print("HOLA ENTRO ACA CREO")        

        # C) variable
        if isinstance(arg, str):
            print("EMIT VAR:", arg)
            return self._emit_variable(arg)

        # D) número literal
        if isinstance(arg, int):
            return self._emit_int(arg)

    def _emit_concat(self, temp):
        for part in self.gen.concat_temps[temp]:
            self.emit(part)

    def _emit_literal(self, lit):
        label = self.gen.strings[lit]
        self.gen.output += [
            f"\tla $a0, {label}",
            "\tli $v0, 4",
            "\tsyscall",
        ]

    def _emit_runtime_string(self, name):
        safe = self.gen.varutil.safe(name)
        self.gen.output += [
            f"\tlw $a0, {safe}",
            "\tli $v0, 4",
            "\tsyscall",
        ]

    def _emit_runtime_concat(self, marker):
        _, left, right = marker

        # imprimir left
        self.emit(left)

        # imprimir right
        self.emit(right)



    def _emit_variable(self, name):
        print("EMIT VAR 2:", name, self.gen.types)
        if name in self.gen.types and (self.gen.types[name] == "string" or self.gen.types[name] == Type.STRING):
            safe = self.gen.varutil.safe(name)
            self.gen.output += [
                f"\tlw $a0, {safe}",  
                "\tli $v0, 4",       
                "\tsyscall",
            ]
            return
        
        safe = self.gen.varutil.safe(name)
        self.gen.output += [
            f"\tlw $a0, {safe}",
            "\tli $v0, 1",
            "\tsyscall",
        ]

    def _emit_int(self, num):
        self.gen.output += [
            f"\tli $a0, {num}",
            "\tli $v0, 1",
            "\tsyscall",
        ]
