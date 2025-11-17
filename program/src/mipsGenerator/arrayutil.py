# arrayutil.py

class ArrayUtil:
    def __init__(self, generator):
        self.gen = generator       # referencia al MIPSGenerator
        self.arrays = {}           # name -> (label, size)

    def declare_array(self, name, size):
        label = f"arr_{name}"
        self.arrays[name] = (label, size)

    def get_label(self, varname):
        """Recibe var_t1 o tmp_t1 y devuelve arr_t1."""
        clean = varname.replace("var_", "").replace("tmp_", "")
        label, _ = self.arrays[clean]
        return label

    def emit_newarr(self, res_name):
        """newarr → carga la dirección base del arreglo"""
        clean = res_name.replace("var_", "").replace("tmp_", "")
        label, _ = self.arrays[clean]

        return [
            f"\tla $t0, {label}",
            f"\tsw $t0, {res_name}",
        ]

    def emit_store(self, base, index, value):
        """Genera código para t1[index] = value"""
        label = self.get_label(base)

        code = [f"\tla $t0, {label}"]

        # --- index ---
        if isinstance(index, int):
            code.append(f"\tli $t1, {index}")
        else:
            code.append(f"\tlw $t1, {index}")

        # --- value ---
        if isinstance(value, int):
            code.append(f"\tli $t2, {value}")
        else:
            code.append(f"\tlw $t2, {value}")

        code += [
            "\tsll $t1, $t1, 2",
            "\tadd $t0, $t0, $t1",
            "\tsw $t2, 0($t0)",
        ]

        return code

    def emit_load(self, base_ptr, index, dest):
        """
        Genera:
        dest = base_ptr[index]
        """
        code = [
            f"\tlw $t3, {base_ptr}"   # pointer in t3
        ]

        if isinstance(index, int):
            code.append(f"\tli $t1, {index}")
        else:
            code.append(f"\tlw $t1, {index}")

        code += [
            "\tsll $t1, $t1, 2",
            "\tadd $t3, $t3, $t1",
            "\tlw $t4, 0($t3)",
            f"\tsw $t4, {dest}",
        ]

        return code
