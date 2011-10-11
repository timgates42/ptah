""" introspect module """
import ptah
import pkg_resources, inspect, os, sys
from pyramid.interfaces import IRoutesMapper, IRouteRequest
from pyramid.interfaces import IViewClassifier, IExceptionViewClassifier

from zope import interface
from zope.interface.interface import InterfaceClass

from memphis import config, view
from memphis.config import directives
from memphis.config.api import exclude, loadPackages

from ptah.manage import INTROSPECTIONS
from ptah.uri import resolvers, resolversTitle


class IntrospectModule(ptah.PtahModule):
    """ Introspection various aspects of memphis & ptah. """

    title = 'Introspect'
    ptah.manageModule('introspect')

    packagesDict = None

    def _init_packages(self):
        packages = loadPackages()
        packages.sort()
        self.packages = [pkg_resources.get_distribution(pkg) for
                         pkg in packages]
        self.packagesDict = dict((p.project_name.replace('-', '_'), p)
                                 for p in self.packages)

    def __getitem__(self, key):
        if self.packagesDict is None:
            self._init_packages()

        key = key.replace('-','_')
        return Package(self.packagesDict[key], self, self.request)


class Package(object):

    def __init__(self, pkg, mod, request):
        self.__name__ = pkg.project_name
        self.__parent__ = mod

        self.pkg = pkg
        self.request = request

    def actions(self):
        pkg = self.pkg.project_name.replace('-', '_')
        actions = directives.scan(pkg, set(), exclude)

        info = {}

        for action in actions:
            d = action.discriminator[0]
            d_data = info.setdefault(d, {})
            mod_data = d_data.setdefault(action.info.module.__name__, [])
            mod_data.append(action)

        return info


class MainView(view.View):
    view.pyramidView(
        context = IntrospectModule,
        template = view.template('ptah_modules:templates/introspect.pt'))

    __doc__ = 'Introspection module view.'
    __intr_path__ = '/ptah-manage/introspect/index.html'

    def update(self):
        self.packages = self.context.packages


view.registerPagelet(
    'ptah-module-actions', IntrospectModule,
    template = view.template('ptah_modules:templates/introspect-actions.pt'))


class PackageView(view.View):
    view.pyramidView(
        context = Package,
        template = view.template('ptah_modules:templates/introspect-pkg.pt'))

    __doc__ = 'Package introspection page.'
    __intr_path__ = '/ptah-manage/introspect/${pkg}/index.html'

    def update(self):
        self.data = self.context.actions()

        self.ndata = ndata = {}
        for tp, d in self.data.items():
            actions = []
            for k, ac in d.items():
                actions.extend(ac)

            ndata[tp] = actions

        itypes = []
        for key, cls in INTROSPECTIONS.items():
            if key in self.data:
                itypes.append((cls.title, cls(self.request)))

        itypes.sort()
        self.itypes = [it for _t, it in itypes]


class EventsView(view.View):
    view.pyramidView(
        'events.html', IntrospectModule,
        template = view.template('ptah_modules:templates/introspect-events.pt'))

    __doc__ = 'Events introspection page.'
    __intr_path__ = '/ptah-manage/introspect/events.html'

    events = None
    actions = None

    def lineno(self, ob):
        return inspect.getsourcelines(ob)[-1]

    def update(self):
        ev = self.request.params.get('ev')
        self.event = event = directives.events.get(ev)

        if event is None:
            events = []
            for n, ev in directives.events.items():
                if isinstance(n, basestring):
                    events.append((ev.title, ev))

            events.sort()
            self.events = [ev for _t, ev in events]
        else:
            pkgs = loadPackages()
            evinst = event.instance

            seen = set()
            actions = []
            for pkg in pkgs:
                for action in directives.scan(pkg, seen, exclude):
                    if action.discriminator[0] == 'memphis.config:subscriber':
                        required = action.args[2]
                        if len(required) == 2 and required[1] == evinst:
                            actions.append(action)
                        elif required[0] == evinst:
                            actions.append(action)

            self.actions = actions


def lineno(ob):
    if ob is not None:
        return inspect.getsourcelines(ob)[-1]

class RoutesView(view.View):
    view.pyramidView(
        'routes.html', IntrospectModule,
        template = view.template('ptah_modules:templates/introspect-routes.pt'))

    __doc__ = 'Routes introspection page.'
    __intr_path__ = '/ptah-manage/introspect/routes.html'

    def update(self):
        #ev = self.request.params.get('ev')
        self.route = route = None #directives.events.get(ev)

        if route is None:
            packages = loadPackages()

            viewactions = []

            seen = set()
            routes = {}
            for pkg in packages:
                actions = directives.scan(pkg, seen, exclude)

                for action in actions:
                    d = action.discriminator[0]
                    if d == 'memphis.view:route':
                        name, pattern, factory = action.args[:3]
                        routes[name] = (pattern, name, factory, [])
                    elif d == 'memphis.view:view':
                        factory = action.info.context
                        if inspect.isclass(factory):
                            isclass = True
                            name = action.args[0]
                            context = action.args[1]
                            route = action.args[3]
                        else:
                            isclass = False
                            factory = action.args[0]
                            name = action.args[1]
                            context = action.args[2]
                            route = action.args[4]
                        if route:
                            viewactions.append(
                                (route, name, context, factory, action))

            sm = self.request.registry

            # add pyramid routes
            for route in sm.getUtility(IRoutesMapper).get_routes():
                if route.name not in routes:
                    routes[route.name] = (
                        route.pattern, route.name, route.factory, [])

            # attach views to routes
            for route, name, context, factory, action in viewactions:
                try:
                    rdata = routes[route][3]
                except:
                    continue
                rdata.append([getattr(factory, '__intr_path__', name),
                              action.info.module.__name__, lineno(factory),
                              factory, action.discriminator[-1]])
                rdata.sort()

            routes = routes.values()
            routes.sort()
            self.routes = routes

            # views
            route_requests = [i for n, i in sm.getUtilitiesFor(IRouteRequest)]

            views = []
            data = sm.adapters._adapters[3]
            for classifier, data in data.items():
                if classifier in (IViewClassifier, IExceptionViewClassifier):
                    for req, data2 in data.items():
                        if req in route_requests:
                            continue

                        for context, data3 in data2.items():
                            if isinstance(context, InterfaceClass):
                                context = '%s.%s'%(
                                    context.__module__, context.__name__)
                            else:
                                context = context.__name__

                            for provides, adapters in data3.items():
                                for name, factory in adapters.items():
                                    views.append(
                                        (context,name,classifier,req,factory))

            views.sort()
            self.views = views


class SourceView(view.View):
    view.pyramidView(
        'source.html', IntrospectModule,
        template = view.template('ptah_modules:templates/introspect-source.pt'))

    __doc__ = 'Source introspection page.'
    __intr_path__ = '/ptah-manage/introspect/source.html'

    source = None
    format = None

    def update(self):
        name = self.request.params.get('pkg')

        pkg_name = name
        while 1:
            try:
                dist = pkg_resources.get_distribution(pkg_name)
                if dist is not None:
                    break
            except pkg_resources.DistributionNotFound:
                if '.' not in pkg_name:
                    break
                pkg_name = pkg_name.rsplit('.',1)[0]

        if dist is None:
            self.source = None

        names = name[len(pkg_name)+1:].split('.')
        path = '%s.py'%os.path.join(*names)
        abspath = pkg_resources.resource_filename(pkg_name, path)

        if os.path.isfile(abspath):
            self.file = abspath
            self.name = '%s.py'%names[-1]
            self.pkg_name = pkg_name
            source = open(abspath, 'rb').read()

            if not self.format:
                from pygments import highlight
                from pygments.lexers import PythonLexer
                from pygments.formatters import HtmlFormatter

                html = HtmlFormatter(
                    linenos='inline',
                    lineanchors='sl',
                    anchorlinenos=True,
                    noclasses = True,
                    cssclass="ptah-source")

                def format(self, code, highlight=highlight,
                           lexer = PythonLexer()):
                    return highlight(code, lexer, html)
                self.__class__.format = format

            self.source = self.format(source)


class UriIntrospection(object):
    """ """

    title = 'Uri resolver'
    ptah.introspection('ptah:uri-resolver')

    actions = view.template('ptah_modules:templates/directive-uriresolver.pt')

    def __init__(self, request):
        self.request = request

    def renderAction(self, action):
        pass

    def renderActions(self, *actions):
        return self.actions(
            resolvers = resolvers,
            resolversTitle = resolversTitle,
            actions = actions,
            request = self.request)


class EventDirective(object):
    """ zca event declarations """

    title = 'Events'
    ptah.introspection('memphis.config:event')

    actions = view.template('ptah_modules:templates/directive-event.pt')

    def __init__(self, request):
        self.request = request

    def renderAction(self, action):
        pass

    def renderActions(self, *actions):
        return self.actions(
            actions = actions,
            events = directives.events,
            request = self.request)


class AdapterDirective(object):
    """ zca adapter registrations """

    title = 'Adapters'
    ptah.introspection('memphis.config:adapter')

    actions = view.template('ptah_modules:templates/directive-adapter.pt')

    def __init__(self, request):
        self.request = request

    def renderAction(self, action):
        pass

    def getInfo(self, action):
        context = action.info.context

        if inspect.isclass(context):
            isclass = True
            requires, name = action.args[:2]
        else:
            context = action.args[1]
            requires = action.args[2]
            name = action.kw['name']

        provided = list(interface.implementedBy(context))
        if len(provided):
            iface = provided[0]
        else:
            iface = 'unknown'
        return locals()

    def renderActions(self, *actions):
        return self.actions(
            actions = actions,
            getInfo = self.getInfo,
            request = self.request)


class PageletTypeDirective(object):
    """ memphis pagelet types """

    title = 'Pagelet Types'
    ptah.introspection('memphis.view:pageletType')

    actions = view.template('ptah_modules:templates/directive-ptype.pt')

    def __init__(self, request):
        self.request = request

    def renderAction(self, action):
        pass

    def renderActions(self, *actions):
        return self.actions(
            actions = actions,
            ptypes = sys.modules['memphis.view.pagelet'].ptypes,
            events = directives.events,
            request = self.request)


class RouteDirective(object):
    """ pyramid routes """

    title = 'Routes'
    ptah.introspection('memphis.view:route')

    actions = view.template('ptah_modules:templates/directive-route.pt')

    def __init__(self, request):
        self.request = request

    def renderAction(self, action):
        pass

    def renderActions(self, *actions):
        return self.actions(
            actions = actions,
            request = self.request)


class SubscriberDirective(object):
    """ zca event subscribers """

    title = 'Event subscribers'
    ptah.introspection('memphis.config:subscriber')

    actions = view.template('ptah_modules:templates/directive-subscriber.pt')

    def __init__(self, request):
        self.request = request

    def renderAction(self, action):
        pass

    def getInfo(self, action):
        factory, ifaces = action.args[1:]
        factoryInfo = '%s.%s'%(action.info.module.__name__, factory.__name__)

        if len(action.args[2]) > 1:
            obj = action.args[2][0]
            klass = action.args[2][-1]
            event = directives.events.get(action.args[2][-1], None)
        else:
            obj = None
            klass = action.args[2][0]
            event = directives.events.get(action.args[2][0], None)

        return locals()

    def renderActions(self, *actions):
        return self.actions(
            getInfo = self.getInfo,
            actions = actions,
            request = self.request)


class ViewDirective(object):
    """ pyramid views """

    title = 'Views'
    ptah.introspection('memphis.view:view')

    actions = view.template('ptah_modules:templates/directive-view.pt')

    def __init__(self, request):
        self.request = request

    def renderAction(self, action):
        pass

    def getInfo(self, action):
        info = action.info
        factory = action.info.context

        if inspect.isclass(factory):
            isclass = True
            name,context,template,route,layout,permission = action.args
        else:
            isclass = False
            factory,name,context,template,route,layout,permission = action.args

        if route:
            if name:
                view = 'view: "%s" route: "%s"'%(name, route)
            else:
                view = 'route: "%s"'%route
        else:
            view = 'view: %s'%name

        if isclass:
            factoryInfo = '%s.%s'%(factory.__module__, factory.__name__)
        else:
            factoryInfo = '%s.%s'%(info.module.__name__, factory.__name__)

        if template:
            template = template.spec
        else:
            template = ''

        return locals()

    def renderActions(self, *actions):
        return self.actions(
            getInfo = self.getInfo,
            actions = actions,
            request = self.request)