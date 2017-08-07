
from scipy.sparse import coo_matrix


import numpy as np






def triangle_face_areas(tris, points):
    e1 = points[tris[:, 1], :] - points[tris[:, 0], :]
    e2 = points[tris[:, 2], :] - points[tris[:, 0], :]

    ns = np.cross(e1, e2)
    areas = np.linalg.norm(ns, axis=1)

    return areas


def triangle_vertex_areas(tris, points):
    tri_areas = triangle_face_areas(tris, points)

    vertex_areas = coo_matrix(
        (np.c_[
            tri_areas,
            tri_areas,
            tri_areas].flatten() /
            3.0,
            (tris.flatten(),
             np.zeros(
                tris.shape).flatten())))
    vertex_areas = vertex_areas.todense().A.flatten()

    return tri_areas, vertex_areas


def _compute_vector_angles(v1, v2):
    cos = (v1 * v2).sum(axis=1) / np.linalg.norm(v1, axis=1) / np.linalg.norm(v2, axis=1)

    cos = np.clip(cos, -1, 1)

    angles = np.arccos(cos).real

    return angles


def triangle_angle_metrics(tris, points):
    # nt = tris.shape[0]

    vert_ids = np.c_[tris, tris[:, [1, 2, 0]], tris[:, [2, 0, 1]]].reshape((-1, 3))
    # tri_ids = np.c_[0:nt, 0:nt, 0:nt].reshape((-1,))

    e_a = points[vert_ids[:, 2], :] - points[vert_ids[:, 1], :]
    e_b = points[vert_ids[:, 0], :] - points[vert_ids[:, 2], :]
    e_c = points[vert_ids[:, 1], :] - points[vert_ids[:, 0], :]

    a = np.linalg.norm(e_a, axis=1)
    b = np.linalg.norm(e_a, axis=1)
    c = np.linalg.norm(e_a, axis=1)

    alpha = _compute_vector_angles(e_b, e_c)
    beta = _compute_vector_angles(e_a, e_c)
    gamma = _compute_vector_angles(e_a, e_b)

    return vert_ids, a, b, c, alpha, beta, gamma




def trimesh_adjacency_matrix(tris, num_points):
    edges = np.hstack((tris[:, (0, 1)], tris[:, (1, 2)], tris[:, (2, 0)])).reshape((-1, 2))
    edges = np.vstack((edges, edges[:, [1, 0]]))

    E = coo_matrix((np.ones(edges.shape[0]), (edges[:, 0], edges[:, 1])), shape=(num_points, num_points))
    E = (E != 0)

    assert E[(tris[:, 0], tris[:, 1])].all()
    assert E[(tris[:, 1], tris[:, 2])].all()
    assert E[(tris[:, 2], tris[:, 0])].all()

    assert E[(tris[:, 1], tris[:, 0])].all()
    assert E[(tris[:, 2], tris[:, 1])].all()
    assert E[(tris[:, 0], tris[:, 2])].all()

    return E

