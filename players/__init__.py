"""Copied from hanabi.  This imports all players in this directory that are
subclassed from Player, this way you can say `from players import *` or `from
players import RandomPlayer`."""

__all__ = []

import pkgutil
import inspect
from bl_classes import Player

for loader, name, is_pkg in pkgutil.walk_packages(__path__):
    try: # only fail later if desired players can't be loaded *cough* numpy
      module = loader.find_module(name).load_module(name)
    except ImportError as err:
      print("Failed to import " + name + " due to error: " + str(err))
      continue

    for name, value in inspect.getmembers(module):
        if name.startswith('__'):
            continue

        if not inspect.isclass(value):
            continue

        # Only add it to exports if Player subclass
        if Player in value.__subclasses__():
            globals()[name] = value
            __all__.append(name)
