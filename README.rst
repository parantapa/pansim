PanSim: A Distributed Pandemic Simulator
========================================

PanSim is a distributed pandemic simulator.

Test Instructions
-----------------

Setup a Anaconda environment
............................

To create a new virtual environment with conda,
have Anaconda/Miniconda setup on your system.
Installation instructions for Miniconda can be found
at https://docs.conda.io/en/latest/miniconda.html#linux-installers
After installation of Anaconda/Miniconda
execute the following commands:

.. code:: bash

  $ conda create -n pansim python=3.8 numpy cython openmpi mpi4py


The above command creates a new conda environment called ``pansim``
with python=3.8, numpy and cython installed.

Install Pansim
..............

.. code:: bash

  $ cd ~
  $ git clone https://github.com/parantapa/pansim.git
  $ cd pansim
  $ conda activate pansim
  $ pip install -e .


Test Pansim
...........

.. code:: bash

  $ cd ~/pansim/tests
  $ ./simplesim_test_cva_1.sh

