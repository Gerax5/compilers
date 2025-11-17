class VarUtil:
    def safe(self, name):
        if name.startswith("var_") or name.startswith("tmp_"):
            return name
        if name.startswith("t") and name[1:].isdigit():
            return f"tmp_{name}"
        return f"var_{name}"
