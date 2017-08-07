
import logging

from pyshapes.laplace.CotanLaplace import CotanLaplace
from pyshapes.laplace.LaplaceSpectrum import compute_laplace_spectrum
from pyshapes.tools.loaders.mesh_loaders import load_mesh


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _plot_eigenvectors(tris, points, evecs, evals=None, title='eigenvectors'):
    from pyshapes.plotting.helpers import _interactive_mesh_plot_from_tuples

    _interactive_mesh_plot_from_tuples(tris, points, scalars=tuple(evecs.T))




if True:
    nev = 30
    tris, points, _ = load_mesh('../datasets/lowres/cat0.obj')

    evecs, evals = compute_laplace_spectrum(CotanLaplace(tris, points), 10)

    _plot_eigenvectors(tris, points, evecs)

