from setuptools import setup

import numpy
from Cython.Build import cythonize

include_path = [numpy.get_include()]
ext_modules = cythonize("src/pansim/*.pyx")

setup(ext_modules=ext_modules, include_dirs=include_path)
