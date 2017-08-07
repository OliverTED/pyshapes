
import logging

import scipy.sparse.linalg

from pyshapes.tools.math_tools import sparse_diagonal
import numpy as np


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LaplaceSpectrum(object):
    def __init__(self, laplace_operator, nev):
        self.vertex_areas = laplace_operator.vertex_areas
        self.D = laplace_operator.D
        self.L = laplace_operator.L

        Op = - laplace_operator.D  # invert once to make spd
        eigen_values, eigen_vectors = _decompose_general_spd(Op, self.vertex_areas, nev)
        eigen_values = -eigen_values  # invert again

        nz = np.sum(np.abs(eigen_values) < 1e-6)
        if nz > 1:
            logging.warning('LaplaceSpectrum: %i zero eigenvalues (are there multiple components?)' % nz)

        self.eigen_values = eigen_values
        self.eigen_vectors = eigen_vectors

    @property
    def num_vertices(self):
        return self.D.shape[0]


    @property
    def nev(self):
        return len(self.eigen_values)


def compute_laplace_spectrum(laplace_operator, nev):
    spectrum = LaplaceSpectrum(laplace_operator, nev)
    return spectrum.eigen_vectors, spectrum.eigen_values


def _decompose_general_spd(C, W, nev):
    logger.info('eigen_decompose_general_spd: starting')

    assert C.shape[0] == C.shape[1]
    assert nev <= C.shape[0]

    if W is None:
        W = scipy.sparse.eye(C.shape[0])

    assert W.shape == (C.shape[0],)

    M = sparse_diagonal(W)
    vals, vecs = scipy.sparse.linalg.eigsh(C, sigma=-1e-8, k=nev, M=M)  # sigma is important

    # sort results
    ids = np.argsort(np.abs(vals))
    vals = vals[ids]
    vecs = vecs[:, ids]

    if not (vals >= -1e-4).all():
        logger.warn('eigen_decompose_general_spd: some eigenvalues less than -1e-4 !')
        logger.warn(str(vals))

#    assert (vals >= -1e-4).all(), vals

    return vals, vecs
