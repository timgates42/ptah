""" uri resolve """
import inspect
import ptah.form
import ptah.renderer
from pyramid.view import view_config

import ptah
from ptah import config
from ptah.uri import ID_RESOLVER
from ptah.manage.manage import PtahManageRoute


@view_config(
    name='uri.html', context=PtahManageRoute,
    renderer=ptah.renderer.layout('ptah-manage:uri.lt', 'ptah-manage'))

class UriResolver(ptah.form.Form):
    """ Uri resolver form """

    fields = ptah.form.Fieldset(
        ptah.form.LinesField(
            'uri',
            title = 'Uri',
            description = "List of uri's",
            klass = 'xxlarge'))

    uri = None
    rst_to_html = staticmethod(ptah.rst_to_html)

    def form_content(self):
        return {'uri': [self.request.GET.get('uri','')]}

    @ptah.form.button2('Show', actype=ptah.form.AC_PRIMARY)
    def show_handler(self, data):
        self.uri = data['uri']

    def update(self):
        uri = self.uri
        if uri is None:
            uri = [self.request.GET.get('uri','')]

        resolvers = config.get_cfg_storage(ID_RESOLVER)

        self.data = data = []
        for u in uri:
            if u:
                schema = ptah.extract_uri_schema(u)
                resolver = resolvers.get(schema)
                info = {'uri': u,
                        'resolver': None,
                        'module': None,
                        'line': None,
                        'obj': None,
                        'cls': None,
                        'clsdoc': None}

                if resolver is not None:
                    info['resolver'] = resolver.__name__
                    info['r_doc'] = ptah.rst_to_html(resolver.__doc__ or '')
                    info['module'] = resolver.__module__
                    info['name'] = '%s.%s'%(
                        resolver.__module__, resolver.__name__)
                    info['line'] = inspect.getsourcelines(resolver)[-1]

                    obj = ptah.resolve(u)
                    info['obj'] = obj

                    if obj is not None:
                        cls = getattr(obj, '__class__', None)
                        info['cls'] = cls
                        info['clsdoc'] = ptah.rst_to_html(
                            getattr(cls, '__doc__', '') or '')

                        if cls is not None:
                            info['clsmod'] = cls.__module__
                            info['clsline'] = inspect.getsourcelines(cls)[-1]

                data.append(info)
