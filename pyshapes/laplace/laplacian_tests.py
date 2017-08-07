import scipy.sparse

import numpy as np



def _test_laplacian_converge_to_const(L, const=None):
    nv = L.shape[0]

    if const is not None:
        L = L * scipy.sparse.diags(const, 0, shape=(nv, nv))

    return (np.abs(L.sum(1)) < 1e-6).all()


def _test_laplacian_preserve_energy(L, vertex_area):
    return (np.abs((vertex_area.T * L).sum(0)) < 1e-6).all()
