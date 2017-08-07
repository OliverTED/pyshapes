'''
Created on Feb 22, 2017

@author: oliver
'''

import numpy as np
import pyshapes.plotting.MyMayavi as mm


def _interactive_mesh_plot_from_tuples(tris, points, scalars=None, title=None, rgb=None, markers=None):
    def len_(data):
        if isinstance(data, tuple):
            return len(data)

        return 1

    num = max([1] + [len_(d) for d in [tris, points, scalars, rgb, markers]])

    def add(kv, name, data, id_):
        if data is None:
            return None

        if isinstance(data, tuple):
            data = data[id_]

        kv[name] = data
        return data

    def pick(id_):
        kv = {}
        add(kv, 'tris', tris, id_)
        add(kv, 'points', points, id_)
        add(kv, 'scalars', scalars, id_)
        add(kv, 'rgb', rgb, id_)

        add(kv, 'markers', markers, id_)

        return kv

    def update(scene, which):
        draw(**pick(which))

    fig = mm.FigureWithVariables([('which', 0, num - 1)], update, title=title)

    plot, marker_plot = None, None

    def draw(markers=None, **kwargs):
        nonlocal plot, marker_plot
        if plot is None:
            plot = mm.MeshPlot(**kwargs, figure=fig)
        else:
            plot.update(**kwargs)

        if marker_plot is not None:
            marker_plot.clear()

        if markers:
            marker_plot = mm.MarkerPlot(
                points[markers, :],
                points_from_scaling=points, scalars=np.arange(len(markers)), figure=fig)

    draw(**pick(0))

    fig.start()



def scale_rgb_to_unit(rgb):
    rgb = rgb - np.min(rgb, axis=0)[None, :]
    rgb = rgb / np.max(rgb, axis=0)[None, :]
    return rgb



def _interactive_point_chooser(tris, points, rgb=None, scalars=None, selected=None, wait=False):
    if rgb is None:
        rgb = scale_rgb_to_unit(points)

    plot = mm.MeshPlot(tris, points, rgb=rgb, scalars=scalars)
    markers = None

    def pick(vertex_id):
        print(('picked point %i !' % vertex_id))

        if markers:
            markers.clear()

        markers = mm.MarkerPlot(points[[vertex_id], :], points_from_scaling=points)

    plot.register_vertex_picker(pick)

    if selected is not None:
        pick(selected)

    if wait:
        mm.show()

    return plot
