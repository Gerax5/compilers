class ClassManager:
    """
    Administra la información de clases:
    - atributos
    - métodos
    - resolución de this
    - generación de nombres MIPS únicos
    """
    def __init__(self):
        self.current_class = None
        self.classes = {}  # { className : { "fields": set(), "methods": set() } }
        self.object_storages = {} # Mapeo de instancias → almacenamiento MIPS
        self.class_sizes = {}   # className -> size in bytes


    # -------------------------
    #  BEGIN CLASS
    # -------------------------
    def begin_class(self, name):
        self.current_class = name
        if name not in self.classes:
            self.classes[name] = {
                "fields": set(),
                "methods": set()
            }

    # -------------------------
    #  REGISTER FIELD
    # -------------------------
    def add_field(self, name):
        """
        name es un string como 'name', 'age', etc.
        """
        cls = self.current_class
        self.classes[cls]["fields"].add(name)

    # -------------------------
    #  REGISTER METHOD
    # -------------------------
    def add_method(self, method_name):
        cls = self.current_class
        self.classes[cls]["methods"].add(method_name)

    # -------------------------
    #  END CLASS
    # -------------------------
    def end_class(self):
        cls = self.current_class
        if cls:
            field_count = len(self.classes[cls]["fields"])
            print(f"Class '{cls}' has {field_count} fields.")
            self.class_sizes[cls] = field_count * 4
        self.current_class = None

    # -------------------------
    #  RESOLVE FIELD STORAGE
    # -------------------------
    def resolve_field(self, class_name, field):
        """
        Devuelve el nombre MIPS donde se guarda:
        Animal.name    → var_Animal_name
        Persona.age    → var_Persona_age
        """
        return f"var_{class_name}_{field}"

    # -------------------------
    #  RESOLVE METHOD LABEL
    # -------------------------
    def resolve_method_label(self, class_name, method_name):
        """
        Devuelve la etiqueta de función:
        Animal.speak → func_Animal_speak
        """
        return f"func_{class_name}_{method_name}"

    # -------------------------
    #  INSTANCE STORAGE
    # -------------------------
    def map_instance(self, inst_name, class_name):
        """
        Guarda el tipo de la instancia.
        Ejemplo: self.object_storages["a1"] = "Animal"
        """
        self.object_storages[inst_name] = class_name

    def get_instance_class(self, inst_name):
        return self.object_storages.get(inst_name, None)
