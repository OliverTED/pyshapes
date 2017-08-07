#!/bin/bash

# set -euo pipefail
# IFS=$'\n\t'

rm -rf .env
rm -f .activate.sh


wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p .env/miniconda
rm miniconda.sh

export PATH=".env/miniconda/bin:$PATH"
hash -r
conda config --set always_yes yes --set changeps1 no
conda update -q conda
# Useful for debugging any issues with conda
conda info -a

# CONDA_PARAM=(-c cvxgrp -c mosek -c menpo)
PACKAGES=" scipy numpy cvxopt scikit-learn pytest pip sphinx sphinx-autobuild"
PACKAGES="-c menpo $PACKAGES mayavi pyface traitsui pyqt=4"


conda create -q -n test-env python=3.4

echo "source $(pwd)/.env/miniconda/bin/activate test-env" > .activate.sh
source ./.activate.sh
# source activate test-env

conda install $PACKAGES

# pip install pytest-cov
# pip install coveralls
# pip install sphinx-autobuild
pip install pytest-cov coveralls sphinx-autobuild
