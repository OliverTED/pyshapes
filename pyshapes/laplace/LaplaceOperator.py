'''
Created on Aug 7, 2017

@author: oliver
'''




from warnings import warn
import logging

import scipy.sparse

from pyshapes.tools.math_tools import sparse_diagonal
import numpy as np


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)






def _laplacian_make_converge_to_const(L):
    """diffusion with a Laplace Operator converges to a vector in the row null space.
    This function sets diagonal entries, that the constant vector is in the row null space
    e.g. L.sum(1) == 0
    """

    nv = L.shape[0]

    L = L - scipy.sparse.diags(L.sum(1).A.flatten(), 0, shape=(nv, nv))

    return L




def _matrix_clip_and_warn(L, abs_max=1e10):
    L = L.tocsr()

    if (abs(L) > abs_max).sum() > 0:
        warn('laplacian: values larger than %g found !' % abs_max)
        L[L > abs_max] = abs_max
        L[L < -abs_max] = -abs_max

    return L


def _vector_clip_and_warn(data, rel=1e6):
    mean = np.mean(data[data != 0])

    upper_bound = mean * rel
    lower_bound = mean / rel

    too_large = data > upper_bound
    too_small = data < lower_bound

    if too_large.any() or too_small.any():
        warn('vertex_area: values too small/large !')
        data[too_large] = upper_bound
        data[too_small] = lower_bound

    return data




class LaplaceOperator(object):
    def __init__(self, *, D=None, L=None, vertex_areas):
        nv = len(vertex_areas)

        assert L is not None or D is not None
        if L is None:
            L = scipy.sparse.diags(1 / vertex_areas, 0, shape=(nv, nv)) * D
        if D is None:
            L = scipy.sparse.diags(vertex_areas, 0, shape=(nv, nv)) * D

        self.D, self.L, self.vertex_areas = D, L, vertex_areas

        self.scalar_product = sparse_diagonal(self.vertex_areas)

