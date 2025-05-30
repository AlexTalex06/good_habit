import logging
from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from sqlalchemy import engine_from_config
from .models import DBSession, Base

log = logging.getLogger(__name__)

def main(global_config, **settings):
    # Configurar la base de datos
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    try:
        engine.connect()
        log.info("✅ Conexión exitosa a la base de datos.")
    except Exception as e:
        log.exception("❌ Error al conectar a la base de datos")

    # Leer el secreto desde settings
    secret = settings.get('session.secret', 'changeme')

    # Fábrica para sesiones firmadas
    session_factory = SignedCookieSessionFactory(secret)

    # Políticas de autenticación y autorización
    authn_policy = AuthTktAuthenticationPolicy(secret, hashalg='sha256')
    authz_policy = ACLAuthorizationPolicy()

    config = Configurator(settings=settings, session_factory=session_factory)
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    # Plantillas
    config.include('pyramid_jinja2')
    config.include('pyramid_sqlalchemy')
    config.add_jinja2_search_path('good_habit:templates')

    # Archivos estáticos
    config.add_static_view(name='static', path='good_habit:static', cache_max_age=3600)
    config.add_request_method(lambda r: DBSession(), 'dbsession', reify=True)

    # Rutas
    config.add_route('welcome', '/')
    config.add_route('home', '/home')
    config.add_route('login', '/login')
    config.add_route('register', '/register')
    config.add_route('logout', '/logout')
    config.add_route('add_habit', '/add_habit')
    config.add_route('complete_habit', '/complete_habit/{id}')
    config.add_route('delete_habit', '/habit/delete/{id}')
    config.add_route('edit_habit', '/habit/edit/{id}') 
    config.add_route('progress', '/progress')


    # Auto-escanear vistas y configuración adicional
    config.scan()

    return config.make_wsgi_app()


