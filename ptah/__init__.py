# ptah api

# layout
from ptah.renderer import layout
from ptah.renderer import layout_config


# config
from ptah import config
from ptah.config import subscriber
from ptah.config import get_cfg_storage
from ptah.config import shutdown
from ptah.config import shutdown_handler

# uri
from ptah.uri import resolve
from ptah.uri import resolver
from ptah.uri import extract_uri_schema
from ptah.uri import UriFactory

# sqla
from ptah.sqlautils import get_base
from ptah.sqlautils import get_session

# events
from ptah import events
from ptah.events import event

# view api
from ptah.view import View

# settings
from ptah.settings import get_settings
from ptah.settings import register_settings
from ptah.settings import load_dbsettings

# security
from ptah.authentication import auth_service
from ptah.authentication import SUPERUSER_URI

from ptah.authentication import auth_checker
from ptah.authentication import auth_provider

from ptah.authentication import search_principals
from ptah.authentication import principal_searcher

# acl
from ptah.security import ACL
from ptah.security import ACLsProperty
from ptah.security import get_acls
from ptah.interfaces import IACLsAware

# role
from ptah.security import Role
from ptah.security import get_roles
from ptah.security import get_local_roles
from ptah.security import roles_provider
from ptah.interfaces import IOwnersAware
from ptah.interfaces import ILocalRolesAware

# permission
from ptah.security import Permission
from ptah.security import get_permissions
from ptah.security import check_permission

# default roles and permissions
from ptah.security import Everyone
from ptah.security import Authenticated
from ptah.security import Owner
from ptah.security import DEFAULT_ACL
from ptah.security import NOT_ALLOWED
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import NO_PERMISSION_REQUIRED

# type information
from ptah.typeinfo import tinfo
from ptah.typeinfo import TypeInformation
from ptah.typeinfo import get_type, get_types
from ptah.interfaces import NotFound, Forbidden

# ptah settings ids
CFG_ID_PTAH = 'ptah'

# password tool
from ptah.password import pwd_tool
from ptah.password import password_changer

# mail templates
from ptah import mail

# pagination
from ptah.util import Pagination

# thread local data
from ptah.util import tldata

# ReST renderer
from ptah.rst import rst_to_html

# sqlalchemy utils
from ptah.sqlautils import QueryFreezer
from ptah.sqlautils import JsonDictType
from ptah.sqlautils import JsonListType
from ptah.sqlautils import set_jsontype_serializer
from ptah.sqla import generate_fieldset
from ptah.sqla import build_sqla_fieldset

# simple ui actions
from ptah.uiactions import uiaction
from ptah.uiactions import list_uiactions

# manage
from ptah import manage

# populate
POPULATE = False
from ptah.populate import populate
from ptah.populate import POPULATE_DB_SCHEMA

# simple test case
from ptah.testing import PtahTestCase

# register migration
from ptah.migrate import register_migration

# json
from ptah.util import json

# extra fields
from ptah.jsfields import TextEditorField
from ptah.jsfields import JSDateField
from ptah.jsfields import JSDateTimeField


def includeme(cfg):
    cfg.include('ptah.form')
    cfg.include('ptah.formatter')
    cfg.include('ptah.message')
    cfg.include('ptah.renderer')
    cfg.include('ptah.static')
    cfg.include('pyramid_chameleon')
    cfg.include('pyramid_mailer')

    # auth
    from ptah.security import PtahAuthorizationPolicy
    from pyramid.compat import configparser
    from pyramid.authentication import AuthTktAuthenticationPolicy

    kwargs = {'wild_domain': False,
              'callback': get_local_roles,
              'secret': cfg.registry.settings.get('ptah.secret', ''),
              'hashalg': cfg.registry.settings.get('ptah.hashalg=', 'sha512')}

    cfg.set_authorization_policy(PtahAuthorizationPolicy())
    cfg.set_authentication_policy(AuthTktAuthenticationPolicy(**kwargs))

    # include extra packages
    cfg.include('pyramid_tm')

    # object events handler
    from zope.interface.interfaces import IObjectEvent
    cfg.registry.registerHandler(
        config.ObjectEventNotify(cfg.registry), (IObjectEvent,))

    # initialize settings
    from ptah import settings
    def pyramid_init_settings(cfg, custom_settings=None,
                              section=configparser.DEFAULTSECT):
        cfg.action('ptah.init_settings',
                   settings.init_settings,
                   (cfg, custom_settings, section), order=999998)

    cfg.add_directive('ptah_init_settings', pyramid_init_settings)

    # initialize sql
    from ptah import ptahsettings
    cfg.add_directive('ptah_init_sql', ptahsettings.initialize_sql)

    # ptah manage ui directive
    cfg.add_directive('ptah_init_manage', ptahsettings.enable_manage)

    # ptah mailer directive
    cfg.add_directive('ptah_init_mailer', ptahsettings.set_mailer)

    # ptah.config directives
    from ptah.config import pyramid_get_cfg_storage
    cfg.add_directive(
        'get_cfg_storage', pyramid_get_cfg_storage)

    # ptah.config.settings directives
    from ptah.settings import pyramid_get_settings
    cfg.add_directive(
        'ptah_get_settings', pyramid_get_settings)

    # ptah.authentication directives
    from ptah import authentication
    cfg.add_directive(
        'ptah_auth_checker', authentication.pyramid_auth_checker)
    cfg.add_directive(
        'ptah_auth_provider', authentication.auth_provider.pyramid)
    cfg.add_directive(
        'ptah_principal_searcher', authentication.principal_searcher.pyramid)

    # ptah.uri directives
    cfg.add_directive('ptah_uri_resolver', resolver.pyramid)

    # ptah.password directives
    cfg.add_directive(
        'ptah_password_changer', password_changer.pyramid)

    # populate
    def pyramid_populate(cfg):
        from ptah.populate import Populate
        if not POPULATE:
            cfg.action('ptah.populate',
                       Populate(cfg.registry).execute, order=9999999)

    cfg.add_directive('ptah_populate', pyramid_populate)
    cfg.add_directive('ptah_populate_step', populate.pyramid)

    # migrations
    from ptah import migrate
    cfg.add_directive('ptah_migrate', migrate.ptah_migrate)

    # template layers
    cfg.add_layer('ptah', path='ptah:templates/ptah/')
    cfg.add_layer('ptah-manage', path='ptah:templates/manage/')
    cfg.add_layer('ptah-intr', path='ptah:templates/intr/')

    # ptah manage layouts
    from ptah.manage.manage import PtahManageRoute, LayoutManage

    cfg.add_layout('ptah', renderer='ptah:layout.lt')
    cfg.add_layout(
        'ptah-manage', PtahManageRoute, root=PtahManageRoute,
        use_global_views=False, renderer="ptah-manage:layout.lt",
        view=LayoutManage, parent='ptah')

    # scan ptah
    cfg.scan('ptah.authentication')
    cfg.scan('ptah.events')
    cfg.scan('ptah.jsfields')
    cfg.scan('ptah.mail')
    cfg.scan('ptah.manage')
    cfg.scan('ptah.password')
    cfg.scan('ptah.populate')
    cfg.scan('ptah.ptahsettings')
    cfg.scan('ptah.security')
    cfg.scan('ptah.settings')
    cfg.scan('ptah.typeinfo')
    cfg.scan('ptah.uri')

    # translation
    cfg.add_translation_dirs('ptah:locale')
