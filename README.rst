PanSim: A Distributed Pandemic Simulator
========================================

PanSim is a distributed pandemic simulator.

Test Instructions
-----------------

Clone Pansim
............

.. code:: bash

  $ cd ~
  $ git clone https://github.com/parantapa/pansim.git
  $ cd pansim

Create a Anaconda environment
.............................

To create a new virtual environment with conda,
have Anaconda/Miniconda setup on your system.
Installation instructions for Miniconda can be found
at https://docs.conda.io/en/latest/miniconda.html#linux-installers
After installation of Anaconda/Miniconda
execute the following commands:

.. code:: bash

  $ conda env create -f environment.yml

The above command creates a new conda environment called ``pansim``.

Install PanSim in the environment
.................................

.. code:: bash

  $ conda activate pansim
  $ pip install -U -e .

Test Pansim
...........

.. code:: bash

  $ pansim --help




  $ cd tests
  $ ./simplesim_test_cva_1.sh
  $ ./


Known Issues
------------

Executing Pansim shows error "undefined symbol: _ZSt28__throw_bad_array_new_lengthv"
....................................................................................

This is caused by differing versions of gcc/stdlib in conda compared to on the host system.
Try the following set of commands:

.. code:: bash

  $ conda activate pansim
  $ cd $CONDA_PREFIX/lib
  $ mv libstdc++.so.6.0.28 libstdc++.so.6.0.28.old                                                                                      (pansi
  $ ln -s /usr/lib64/libstdc++.so.6.0.29 libstdc++.so.6.0.28
  $ cd ~/pansim
  $ pip install -U -e .
  $ pansim --help

More details can be found at:

* https://github.com/conda/conda/issues/10757
  



