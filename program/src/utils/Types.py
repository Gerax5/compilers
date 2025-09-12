from enum import Enum

class Type(Enum):
    INT="int"; 
    FLOAT="float"; 
    BOOL="bool"; 
    STRING="string"; 
    VOID="void"; 
    NULL = "null"

class ArrayType:
    def __init__(self, base, dimensions=1, empty=False):
        self.base = base
        self.dimensions = dimensions
        self.empty = empty
    
    def __repr__(self):
        return f"{self.base}{'[]' * self.dimensions}"