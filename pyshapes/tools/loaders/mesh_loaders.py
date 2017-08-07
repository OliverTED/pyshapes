import logging
import os.path

from pyshapes.tools.loaders import plyfile
import numpy as np


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)





def load_mesh(filename):
    filename_ = filename

    if filename is None or not os.path.exists(filename):
        raise IOError('not found: "' + filename_ + '"')

    logger.info('loading mesh')


    info = {}

    ext = filename.split('.')[-1]
    if ext == 'ply':
        tris, points, colors, _ = load_ply(filename)
        info['colors'] = colors
    elif ext == 'off':
        tris, points = load_off(filename)
    elif ext == 'obj':
        tris, points, info = load_obj(filename)
    else:
        raise RuntimeError('invalid mesh extension')

    return tris, points, info


def check_indices(tris, nv):
    assert (0 <= tris).all(), tris.min()
    assert (tris < nv).all(), tris.max()

    assert tris.dtype in [np.int32, np.int, np.uint32, np.uint16], tris.dtype


def load_ply_data(filename):
    with open(filename) as f:
        data = plyfile.PlyData.read(f)

    return data


def load_ply(filename):
    from plyfile import PlyData
    data = PlyData.read(filename)

    vertices = data['vertex']

    points = np.concatenate([np.atleast_2d(vertices.data[t]).T for t in ('x', 'y', 'z')], axis=1)

    colors = None
    if 'diffuse_red' in vertices.data.dtype.fields:
        colors = np.concatenate([np.atleast_2d(vertices.data[t]).T
                                 for t in ('diffuse_red', 'diffuse_green', 'diffuse_blue')], axis=1)
    elif 'red' in vertices.data.dtype.fields:
        colors = np.concatenate([np.atleast_2d(vertices.data[t]).T
                                 for t in ('red', 'green', 'blue')], axis=1)


    tri_idx = data['face'].data['vertex_indices']
    idx_dtype = tri_idx[0].dtype

    tris = np.fromiter(tri_idx, [('data', idx_dtype, (3,))],
                       count=len(tri_idx))['data']

    check_indices(tris, points.shape[0])

    return tris, points, colors, data



def load_off(filename):
    points = []
    tris = []

    with open(filename) as f:
        it = f.__iter__()

        line = it.next().split()
        assert line == ['OFF']

        line = [int(val) for val in it.next().split()]
        assert len(line) == 3
        nv = line[0]
        nt = line[1]

        for _ in range(nv):
            p = [float(val) for val in it.next().split()]
            assert p is not None and len(p) == 3

            points.append(p)

        for _ in range(nt):
            t = [int(val) for val in it.next().split()]
            assert t is not None and len(t) == 4 and t[0] == 3
            t = t[1:]

            tris.append(t)

    tris = np.array(tris)
    points = np.array(points)

    check_indices(tris, points.shape[0])

    return tris, points



def load_obj(filename):
    V, VN, VT, Fs = [], [], [], []

    with open(filename) as fh:
        for line in fh:
            line = line.strip()

            if len(line) == 0 or line[0] == '#':
                continue

            line = line.strip().split(' ')
            if line[0] == 'v':  # vertex
                V.append([float(v) for v in line[1:]])
            elif line[0] == 'vt':  # tex-coord
                VT.append([float(v) for v in line[1:]])
            elif line[0] == 'vn':  # normal vector
                VN.append([float(v) for v in line[1:]])
            elif line[0] == 'f':  # face
                Fs.append(line[1:])
            else:
                logger.info('load_obj: unknown line prefix: %s', ' '.join(line))

    V = np.array(V)
    VN = np.array(VN)
    VT = np.array(VT)

    def parse_face_vertex(ids_str):
        ids = [int(i) - 1 if i != '' else None for i in ids_str.split('/')]

        while len(ids) < 3:
            ids.append(None)

        assert len(ids) > 0 and len(ids) <= 3, len(ids)
        iv_, it_, in_ = ids

        assert iv_ is not None

        it_ = VT[it_] if it_ is not None else None
        in_ = VN[in_] if in_ is not None else None

        return iv_, it_, in_

    def parse_face(face):
        assert len(face) == 3, len(face)

        if len(face) != 3:
            raise Exception('not a triangle!')

        return [parse_face_vertex(data) for data in face]

    F = [parse_face(f) for f in Fs]

    points = V
    tris = np.array([[d[0] for d in f] for f in F])
    vt_ = [[d[1] for d in f] for f in F]
    vn_ = [[d[2] for d in f] for f in F]
    has_textures = any([d is not None for f in vt_ for d in f])
    has_normals = any([d is not None for f in vn_ for d in f])
    per_tri_vertex_texture = np.array(vt_) if has_textures else None
    per_tri_vertex_normal = np.array(vn_) if has_normals else None

    info = dict(
        tris=tris,
        points=points,
        per_tri_vertex_normal=per_tri_vertex_normal,
        per_tri_vertex_texture=per_tri_vertex_texture,
        tris_uv=per_tri_vertex_texture,
    )

    check_indices(tris, points.shape[0])

    return tris, points, info


def write_obj(filename, tris, points, tris_uvs=None, rgb=None):
    check_indices(tris, points.shape[0])

    if tris_uvs is not None:
        assert tris_uvs.shape == tris.shape + (2,)
    if rgb is not None:
        assert rgb.shape == points.shape

    with open(filename, 'w') as f:
        lines = []
        if rgb is None:
            lines += ['v {:f} {:f} {:f}\n'.format(p[0], p[1], p[2])
                      for p in points]
        else:
            if rgb.shape[1] == 3:
                rgba = np.c_[rgb, np.ones(rgb.shape[0])]
            else:
                rgba = rgb

            rgba = (rgba * 255)
            rgba[rgba > 255] = 255
            rgba[rgba < 0] = 0
            rgba = rgba.astype(np.uint8)

            lines += ['v {:f} {:f} {:f} {:d} {:d} {:d} {:d}\n'.format(p[0], p[1], p[2], c[0], c[1], c[2], c[3])
                      for p, c in zip(points, rgba)]

        if tris_uvs is None:
            lines += ['f {:d}// {:d}// {:d}//\n'.format(t[0], t[1], t[2])
                      for t in tris + 1]
        else:
            lines += ['vt {:f} {:f}\n'.format(p1, p2)
                      for p1, p2 in tris_uvs.reshape(-1, 2)]
            lines += ['f {i1}/{j1}/ {i2}/{j2}/ {i3}/{j3}/\n'.format(i1=t[0], i2=t[1], i3=t[2], j1=t[3], j2=t[4], j3=t[5])
                      for t in np.c_[tris + 1, np.reshape(np.arange(tris.size) + 1, (-1, 3))]]

        f.write("".join(lines))
