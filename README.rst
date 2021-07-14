PanSim: A Distributed Pandemic Simulator
========================================

PanSim is a distributed pandemic simulator.

Local Test Instructions
-----------------------

Step 1: Clone PanSim repository
-------------------------------

.. code:: bash

  $ cd ~
  $ git clone https://github.com/parantapa/pansim.git
  $ cd pansim

Step 2: Create a Anaconda environment
.....................................

To create a new virtual environment with conda,
have Anaconda/Miniconda setup on your system.
Installation instructions for Miniconda can be found
at https://docs.conda.io/en/latest/miniconda.html#linux-installers
After installation of Anaconda/Miniconda
execute the following commands:

.. code:: bash

  $ conda env create -f environment.yml

The above command creates a new conda environment called ``pansim``.

Step 3: Install PanSim in the environment
.........................................

PanSim can be installed using pip.

.. code:: bash

  $ conda activate pansim
  $ pip install -U -e .

Step 4: Test Pansim
...................

Executing the following command to figure if installation was successful.

.. code:: bash

  $ pansim --help

To run the simple tests using the serial and parallel version do the following.

.. code:: bash

  $ cd tests
  $ ./simplesim_test_cva_1.sh
  $ ./distsim_test_cva_1.sh

Local Test Instructions with Java
---------------------------------

Step 1: Compile the simple java behavior model using maven
..........................................................

.. code:: bash

  $ mvn -U clean compile assembly:single

Step 2: Run the simple tests (using java behavior model)
........................................................

.. code:: bash

  $ cd tests
  $ ./simplesim_java_test_cva_1.sh
  $ ./distsim_java_test_cva_1.sh

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
