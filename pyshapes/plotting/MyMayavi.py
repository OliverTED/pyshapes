
import json
import logging

from mayavi.core.ui.api import (
    MayaviScene, SceneEditor, MlabSceneModel)
from traits.api import (
    HasTraits, Range, Instance,
    on_trait_change)
from traitsui.api import View, Item, Group, RangeEditor
from tvtk.api import tvtk

import mayavi.mlab as mlab
import numpy as np


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)



def show():
    mlab.show()


class BaseFigure(object):

    def __init__(self, figure, fg=None, bg=None, size=None, view=None):
        self.figure = figure

        if fg is not None:
            self.set_fg_color(*fg)
        if bg is not None:
            self.set_bg_color(*bg)
        if view is not None:
            self.set_view(**view)
        if size is not None:
            self.set_size(size)

    def mlab_figure(self):
        return self.figure

    def close(self):
        mlab.close(self.figure)

    def clear(self):
        mlab.clf(self.figure)

    def set_fg_color(self, r, g, b):
        scene = self.figure.scene
        scene.foreground = (r, g, b)

    def set_bg_color(self, r, g, b):
        scene = self.figure.scene
        scene.background = (r, g, b)

    def get_size(self):
        w = self.figure.scene.render_window
        return tuple(w.size)

    def set_size(self, size):
        scene = self.figure
        viewer = scene.parent.get_viewer(scene)
        w, h = size
        viewer.size = (w, h + 44)

        if self.get_size() != size:
            logger.warn('requested window of size (%i,%i), but got size (%i, %i)' % tuple(list(size) + list(self.get_size())))



    def register_on_keypress(self, callback):
        # callback:  your_function(event)
        def func(vtk_obj, event):
            logger.info('key event: %s', repr(vtk_obj.GetKeyCode()))
            callback(vtk_obj.GetKeyCode())

        self.figure.scene._get_interactor().add_observer('KeyPressEvent', func)



    def set_view(self, *, azimuth=None, elevation=None, distance=None,
                 focalpoint=None, roll=None, parallel_scale=None, parallel_view=None, size=None):
        fig = self.figure
        mlab.view(azimuth=azimuth, elevation=elevation, distance=distance, focalpoint=focalpoint, roll=roll, figure=fig)

        if parallel_scale is not None:
            fig.scene.camera.parallel_scale = parallel_scale

            parallel_view = parallel_view or True

        if distance is not None:
            parallel_view = parallel_view or False

        if parallel_view is not None:
            fig.scene.parallel_projection = parallel_view

        if size is not None:
            self.set_size(size)


    def _get_view(self, *, interactive=False):
        if interactive:
            # let use change figure and press button
            mlab.show(stop=True)

        fig = self.figure

        azimuth, elevation, distance, focalpoint = mlab.view()
        roll = mlab.roll()
        if roll == 0.0:
            roll = None  # fix ?!? figures disappear
        parallel_scale = fig.scene.camera.parallel_scale
        parallel_view = fig.scene.parallel_projection

        return azimuth, elevation, distance, focalpoint, roll, parallel_scale, parallel_view



    def get_view(self, *, interactive=False):
        azimuth, elevation, distance, focalpoint, roll, \
            parallel_scale, parallel_view = self._get_view(interactive=interactive)

        view_data = dict(
            azimuth=azimuth, elevation=elevation, distance=distance,
            focalpoint=focalpoint, roll=roll, parallel_scale=parallel_scale, parallel_view=parallel_view)
        return view_data

    def set_view_from_string(self, view_data):
        if view_data is None:
            view_data = {}

        if isinstance(view_data, str):
            view_data = json.loads(view_data)

        assert isinstance(view_data, dict)

        self.set_view(**view_data)

    def get_view_as_string(self, *, interactive=False):
        azimuth, elevation, distance, focalpoint, roll, \
            parallel_scale, parallel_view = self._get_view(interactive=interactive)

        res = ('dict('
               'focalpoint=[{0[0]:.3f}, {0[1]:.3g}, {0[2]:.3g}], '
               'azimuth={1:.3g}, roll={2:.3g}, elevation={3:.3g}, '
               '{4[0]}={4[1]:.3g}, '
               'size=({5[0]}, {5[1]})'
               ')')
        res = res.format(tuple(focalpoint), azimuth, roll, elevation,
                         ('parallel_scale', parallel_scale) if parallel_view else ('distance', distance),
                         self.get_size())

        return res

    def show(self):
        mlab.show()


class Figure(BaseFigure):

    def __init__(self, *, title=None, size=None, mlab_figure=None, fg=None, bg=None, view=None):
        kwargs = {}
        if size is not None:
            size_ = (size[0], size[1] + 44)
            kwargs['size'] = size_

        figure = mlab_figure or mlab.figure(title, **kwargs)
        if title is not None:
            figure.name = title

        BaseFigure.__init__(self, figure, fg=fg, bg=bg, view=view)

        if size is not None:
            if self.get_size() != size:
                logger.warn('requested window of size (%i,%i), but got size (%i, %i)' % tuple(list(size) + list(self.get_size())))


def _parse_figure(figure):
    if isinstance(figure, str) and figure == 'new':
        figure = Figure()

    if isinstance(figure, str) and figure[:4] == 'new:':
        figure = Figure(title=figure[4:])

    if figure is None:
        figure = Figure()

    return figure


def _parse_figure_to_mayavi(figure):
    return _parse_figure(figure).figure


class Plot(object):

    def __init__(self, plot, figure, *, visible=True, opacity=1.0):
        self.figure = figure
        self.plot = plot

        if not visible:
            self.plot.actor.actor.visibility = 0

        if opacity != 1.0:
            self.set_opacity(opacity)

    def set_colorbar(self, *, caxis=None, visible=True):
        lut_mgr = mlab.colorbar(self.plot)
        if lut_mgr is None:
            return  # when rgb is set

        if caxis is not None:
            lut_mgr.data_range = caxis
        else:
            lut_mgr.use_default_range = True

        lut_mgr.show_scalar_bar = visible

        return lut_mgr

    def set_opacity(self, value):
        self.plot.actor.property.opacity = value
        if value != 1.0:
            self.plot.actor.property.backface_culling = True

    def remove(self):
        if self.plot is not None:
            ch = self.plot.module_manager.source
            obj = ch.mlab_source.m_data
            parent = obj.parent_.value()

            if obj in parent.children:
                parent.remove_child(obj)

    def get_figure(self):
        return self.figure

    def show(self):
        mlab.show()


class MeshPlot(Plot):

    def __init__(self, tris, points, *, rgb=None, scalars=None, figure=None, visible=True, opacity=1.0):
        figure = _parse_figure(figure)

        kwargs = {}
        kwargs['figure'] = figure.mlab_figure()

        if scalars is not None:
            assert scalars.shape == (points.shape[0],)

        if rgb is not None:
            assert scalars is None
            assert len(rgb) == 3 or rgb.shape == (points.shape[0], 3)

        self._points = points

        x, y, z = points[:, 0], points[:, 1], points[:, 2]
        if scalars is not None:
            kwargs['scalars'] = scalars
        plot = mlab.triangular_mesh(x, y, z, tris, **kwargs)
        Plot.__init__(self, plot, figure, visible=visible, opacity=opacity)

        if rgb is not None:
            self._set_rgb(rgb)


    def enable_contour(self, *, number=60):
        p = self.plot
        p.actor.property.color = (0, 0, 0)
        p.actor.mapper.scalar_visibility = 0
        p.enable_contours = True
        p.contour.number_of_contours = number

    def _set_rgb(self, rgb):
        if isinstance(rgb, tuple) and len(rgb) == 3:
            if np.max(rgb) > 1:
                rgb = tuple(np.array(rgb) / 255)
            self.plot.actor.actor.mapper.scalar_visibility = False
            self.plot.actor.actor.property.color = rgb

        else:
            rgb = np.array(rgb)
            assert rgb.shape == self._points.shape

    #        if rgb.dtype in [np.float, np.float64]:
            # assume from 0 to 1
            rgb = rgb * 255
            rgb[rgb > 255] = 255
            rgb[rgb < 0] = 0
            rgb = rgb.astype(np.int)

            sc = tvtk.UnsignedCharArray()  # @UndefinedVariable
            sc.from_array(rgb)

            self.plot.mlab_source.dataset.point_data.scalars = sc
            self.plot.mlab_source.dataset.modified()
            self.plot.actor.mapper.set_input_data_object(self.plot.mlab_source.dataset)

    def update(self, *, points=None, scalars=None, tris=None, rgb=None):
        args = {}
        if points is not None:
            args['x'] = points[:, 0]
            args['y'] = points[:, 1]
            args['z'] = points[:, 2]
            self._points = points

        if scalars is not None:
            args['scalars'] = scalars
        if tris is not None:
            args['tris'] = tris

        self.plot.mlab_source.set(**args)

        if rgb is not None:
            self._set_rgb(rgb)

    # must be enabled, because it does not work well with variables
    def register_vertex_picker(self, callback):
        def picker_callback(picker_obj):
            picked_vtks = [o._vtk_obj for o in picker_obj.actors]

            matching = self.plot.actor.actor._vtk_obj in picked_vtks

            logger.info('pick event%s: %s %s', ' (matched)' if matching else '', repr(picker_obj), picked_vtks)

            if matching:
                vertex_id = picker_obj.point_id
                callback(vertex_id)

        self.get_figure().mlab_figure().on_mouse_pick(picker_callback)


    def set_wireframe(self, line_width=None):
        self.plot.actor.actor.property.representation = 'wireframe'
        if line_width is not None:
            self.plot.actor.actor.property.line_width = line_width



def _createModel(_callback, variables, title):
    def correct(var):
        if len(var) == 3:
            return list(var) + [None]
        else:
            return var
    variables = [correct(var) for var in variables]


    if title is None:
        title = 'figure'

    variable_names = [v[0] for v in variables]
    variable_items = [Item(v[0], editor=RangeEditor(mode='slider', low=v[1], high=v[2])) for v in variables]

    class MyModel(HasTraits):
        scene_instance = Instance(MlabSceneModel, ())

        @property
        def scene(self):
            return self.scene_instance.mayavi_scene

        @on_trait_change(','.join(['scene.activated'] + variable_names))
        def update_plot(self):
            cur_variables = {name: getattr(self, name) for name, _, _, _ in variables}

            _callback(self.scene, cur_variables)
            self.scene_instance.disable_render = False

        # The layout of the dialog created
        view = View(
            Item('scene_instance', editor=SceneEditor(scene_class=MayaviScene),
                 height=250, width=300, show_label=False),
            Group(*variable_items),
            title=title,
            resizable=True)

    model = MyModel()

    for name, t0, t1, default in variables:
        model.add_trait(name, Range(t0, t1, t0))
        if default is not None:
            model.set({name: default})


    return model



class FigureWithVariables(BaseFigure):

    def __init__(self, variables, callback, title=None):

        def view_callback(scene, vars_):
            logger.info('variables: %s', vars_)
            callback(self, **vars_)

        self.traits_model = _createModel(view_callback, variables, title)

#        self.figure = self.traits_model.scene
        BaseFigure.__init__(self, self.traits_model.scene)

    def start(self):
        self.traits_model.configure_traits()


class MarkerPlot(Plot):

    def __init__(self, points, *,
                 scalars=None,
                 marker_scale=1,
                 figure=None,
                 style=None,
                 max_size='auto',
                 points_from_scaling=None,
                 scale_mode='none',
                 opacity=None,
                 scale_relative=1.0,
                 rgb=None):
        kwargs = {}

        figure = _parse_figure(figure)
        kwargs['figure'] = figure.mlab_figure()

        x, y, z = points.T
        args = [x, y, z]

        if scalars is not None:
            args.append(scalars)

        if max_size == 'auto':
            if points_from_scaling is None:
                points_from_scaling = points

            max_size = np.max(np.max(points_from_scaling, axis=0) - np.min(points_from_scaling, axis=0))
            max_size *= 1.0 / 30.0 * marker_scale * scale_relative

        if max_size is not None:
            kwargs['scale_factor'] = max_size

        if style is not None:
            kwargs['mode'] = style

        if opacity is not None:
            kwargs['opacity'] = opacity

        marker_plot = mlab.points3d(*args, scale_mode=scale_mode, **kwargs)

        Plot.__init__(self, marker_plot, figure)

        if rgb is not None:
            self._set_rgb(rgb)


    def update(self, *, points=None, scalars=None, rgb=None):
        args = {}
        if points is not None:
            args['x'] = points[:, 0]
            args['y'] = points[:, 1]
            args['z'] = points[:, 2]

        if scalars is not None:
            args['scalars'] = scalars

        self.plot.mlab_source.set(**args)

        if rgb is not None:
            self._set_rgb(rgb)


    def _set_rgb(self, rgb):
        rgb = np.array(rgb)

#        if rgb.dtype in [np.float, np.float64]:
        # assume from 0 to 1
        rgb = rgb * 255
        rgb[rgb > 255] = 255
        rgb[rgb < 0] = 0
        rgb = rgb.astype(np.int)

        sc = tvtk.UnsignedCharArray()  # @UndefinedVariable
        sc.from_array(rgb)

        self.plot.mlab_source.dataset.point_data.scalars = sc
        self.plot.mlab_source.dataset.modified()
        # self.plot.actor.mapper.input = self.plot.mlab_source.dataset
