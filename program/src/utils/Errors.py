class Error:
    def __init__(self): 
        self.errors=[]

    def err_ctx(self, ctx, msg):
        tok = getattr(ctx, "start", None)
        if tok: 
            self.errors.append(f"[line {tok.line}:{tok.column}] {msg}")
        else:   
            self.errors.append(msg)