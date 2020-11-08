"""Setup."""

from setuptools import setup

import numpy
from Cython.Build import cythonize

package_name = "pansim"
description = "PanSim is a distributed pandemic simulator."

with open("README.rst", "r") as fh:
    long_description = fh.read()

classifiers = """
Intended Audience :: Developers
Intended Audience :: Science/Research
License :: OSI Approved :: MIT License
Operating System :: POSIX :: Linux
Programming Language :: Python :: 3.7
Programming Language :: Python :: 3.8
Topic :: Scientific/Engineering
Topic :: System :: Distributed Computing
""".strip().split("\n")

include_path = [numpy.get_include()]
ext_modules = cythonize("src/pansim/*.pyx")

setup(
    name=package_name,
    description=description,

    author="Parantapa Bhattacharya",
    author_email="pb+pypi@parantapa.net",

    long_description=long_description,
    long_description_content_type="text/x-rst",

    packages=[package_name],
    package_dir={'': 'src'},

    ext_modules=ext_modules,
    include_dirs=include_path,

    zip_safe=False,

    entry_points="""
        [console_scripts]
        pansim=pansim.cli:cli
    """,

    use_scm_version=True,
    setup_requires=['setuptools_scm'],

    install_requires=[
        "click",
        "click_completion",
        "numpy",
        "pandas",
        "pyarrow",
        "toml",
        "Vose-Alias-Method",
        "tqdm",
        "py4j",
        "cython",
        "xactor"
    ],

    url="http://github.com/nssac/pansim",
    classifiers=classifiers
)
