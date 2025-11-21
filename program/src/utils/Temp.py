import re

class TempManager:
    def __init__(self):
        self.available = []  # temporales libres
        self.counter = 0     # cuántos he creado

    def new_temp(self):
        if self.available:  # si hay alguno libre, reutilízalo
            return self.available.pop()
        self.counter += 1
        return f"t{self.counter}"

    def release_temp(self, name):
        if isinstance(name, str) and re.fullmatch(r"t\d+", name) and name not in self.available:
            self.available.append(name)
