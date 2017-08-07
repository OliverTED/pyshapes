'''
Created on Aug 7, 2017

@author: oliver
'''



from scipy.sparse import coo_matrix

from pyshapes.laplace.LaplaceOperator import LaplaceOperator,\
    _laplacian_make_converge_to_const, _matrix_clip_and_warn,\
    _vector_clip_and_warn
from pyshapes.tools.triangle_metric import triangle_angle_metrics,\
    triangle_vertex_areas
import numpy as np


class CotanLaplace(LaplaceOperator):
    """Build cotan based laplacians.

    Desired Properties:

    * diffusion converges to constant:
    Diffusion converges to a vector in the row null space of L.
    Converging to a constant implies that L * constant = constant * L.sum(0) == 0

    * energy preservation:
    Energy is measured via vertex_area * v. Eenrgy is preserved iff (vertex_area.T * L).sum(1) = 0


    LCotan: This operator has favorable properties: diffusion converges to constant and
    energy (measured as vertex_weight.dot(v(t))) is constant under diffusion.
    It is not symmetric, but has real eigenvalues/eigenvectors v1-vn,l1-lm.

    LCotanSym: This operator does not converge to 0 neither does it preserve
    energies. But it is symmetric and its eigenvectors w1-wn fullfil the property:
    wi = sqrt(vertex_weights)*vi
    """

    def __init__(self, tris, points):
        """Create a cotan laplace operator.

        Extended.

        Args:
            tris (np.array): triangles (m x 3)
            points (np.array): vertex positions (n x 3)

        Returns:
            CotanLaplace: the Laplace operator
        """

        nv = points.shape[0]

        vertIds, _, _, _, _, _, gamma = \
            triangle_angle_metrics(tris, points)

        _, vertex_areas = \
            triangle_vertex_areas(tris, points)

        C1 = coo_matrix((1.0 / 2.0 * 1 / np.tan(gamma), (vertIds[:, 0], vertIds[:, 1])), shape=(nv, nv))
        Cotan = C1 + C1.T

        Cotan = _laplacian_make_converge_to_const(Cotan)
        Cotan = _matrix_clip_and_warn(Cotan)

        vertex_areas = _vector_clip_and_warn(vertex_areas)

        super(CotanLaplace, self).__init__(D=Cotan, vertex_areas=vertex_areas)
