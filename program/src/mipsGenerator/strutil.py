class StrUtil:
    def is_literal(self, x):
        """
        Devuelve True si x es un literal de cadena entre comillas:
        Ejemplo: "Hola mundo"
        """
        return (
            isinstance(x, str) and len(x) >= 2 and x.startswith('"') and x.endswith('"')
        )
