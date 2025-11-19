class FunctionManager:
    def __init__(self):
        self.current_function = None
        self.params = {}        # func_name -> [param1, param2, ...]
        self.localVarName = {}
        self.locals = {}        # func_name -> set(varnames)

    # ------------------------------------
    #  BEGIN FUNCTION
    # ------------------------------------
    def begin_function(self, name, classname = ""):
        self.current_function = name
        self.params[name] = []
        self.localVarName[name] = {}
        self.locals[name] = set()
        return [
            f"{classname}{name}:",
            "\taddiu $sp, $sp, -8",
            "\tsw $ra, 4($sp)",
            "\tsw $fp, 0($sp)",
            "\tmove $fp, $sp"
        ]

    # ------------------------------------
    #  REGISTER PARAM
    # ------------------------------------
    def add_param(self, func, name):
        self.params[func].append(name)
        
        raw = name.replace("var_", "")
        pretty = f"var_{func}_{raw}"

        self.localVarName[func][name] = pretty

    def get_param_storage(self, func, name):
        """
        Devuelve el nombre real en .data donde se guardará el parámetro.
        """
        clean = name.replace("var_", "")
        return f"var_{func}_{clean}"

    def save_params_to_memory(self):
        """
        Genera las instrucciones para sw $a0, var_func_x, etc
        """
        func = self.current_function
        code = []
        for i, pname in enumerate(self.params[func]):
            local_name = self.get_param_storage(func, pname)
            code.append(f"\tsw $a{i}, {local_name}")
        return code

    # ------------------------------------
    #  MAP VARIABLE TO REGISTER
    # ------------------------------------
    def resolve_var(self, name):
        """
        Devuelve el registro o la variable.
        Si es parámetro → reg $a0, $a1, ...
        Si es temporal → memory
        """
        func = self.current_function
        
        # if func and name in self.params[func]:
        #     idx = self.params[func].index(name)
        #     return f"$a{idx}"

        if func and name in self.localVarName[func]:
            return self.localVarName[func][name]

        return name  # normal variable (en .data)

    def is_param(self, name):
        for plist in self.params.values():
            if name in plist:
                return True
        return False

    # ------------------------------------
    #  END FUNCTION
    # ------------------------------------
    def end_function(self):
        return [
            "\tlw $ra, 4($sp)",
            "\tlw $fp, 0($sp)",
            "\taddiu $sp, $sp, 8",
            "\tjr $ra"
        ]
