class MipsPrinter:
    def __init__(self, gen):
        self.gen = gen      # referencia a MIPSGenerator

    def emit(self, arg):
        # A) concatenación
        if isinstance(arg, str) and arg in self.gen.concat_temps:
            return self._emit_concat(arg)

        # B) string literal
        if self.gen.strutil.is_literal(arg):
            return self._emit_literal(arg)

        # C) variable
        if isinstance(arg, str):
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

    def _emit_variable(self, name):
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
