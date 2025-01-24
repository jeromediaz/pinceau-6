import importlib
import weakref


class Loader:
    def __init__(self):
        self._module_cache = weakref.WeakValueDictionary()
        self._class_cache = weakref.WeakValueDictionary()

    def get_module(self, module_name: str, package=None):
        module = self._module_cache.get(f"{package}{module_name}")

        if not module:
            module = importlib.import_module(module_name, package)
            self._module_cache[module_name] = module

        return module

    def get_class(self, class_name: str, module_name: str, package=None):
        module = self.get_module(module_name, package)

        qualified_name = f"{module.__name__}.{class_name}"

        class_object = self._class_cache.get(qualified_name)

        if not class_object:
            class_object = getattr(module, class_name)
            self._class_cache[qualified_name] = class_object

        return class_object
