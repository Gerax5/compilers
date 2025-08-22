from enum import Enum

class Type(Enum):
    INT="int"; 
    FLOAT="float"; 
    BOOL="bool"; 
    STRING="string"; 
    VOID="void"; 
    NULL = "null"

class ArrayType:
    def __init__(self, base, dimensions=1):
        self.base = base
        self.dimensions = dimensions
    
    def __repr__(self):
        return f"{self.base}{'[]' * self.dimensions}"