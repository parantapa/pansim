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

  $ cd ~/pansim
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

  $ cd ~/pansim/tests
  $ ./simplesim_test_cva_1.sh

