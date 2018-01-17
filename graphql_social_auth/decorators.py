from functools import wraps

from django.contrib.auth import login
from django.utils.translation import ugettext_lazy as _

from promise import Promise, is_thenable
from social_core.exceptions import MissingBackend
from social_django.utils import load_backend, load_strategy

from . import exceptions


def psa(f):
    @wraps(f)
    def wrapper(cls, root, info, provider, access_token, **kwargs):
        import pdb; pdb.set_trace()
        strategy = load_strategy(info.context)
        try:
            backend = load_backend(strategy, provider, redirect_uri=None)
        except MissingBackend:
            raise exceptions.GraphQLSocialError(_('Provider not found'))

        user = backend.do_auth(access_token)

        if user is None:
            raise exceptions.GraphQLSocialError(_('Invalid token'))

        login(info.context, user)
        social = user.social_auth.get(provider=provider)

        return f(cls, root, info, social, **kwargs)
    return wrapper


def social_auth(f):
    @psa
    @wraps(f)
    def wrapper(cls, root, info, social, **kwargs):
        def on_resolve(payload):
            payload.social = social
            return payload

        result = f(cls, root, info, social, **kwargs)

        # Improved mutation with thenable check
        if is_thenable(result):
            return Promise.resolve(result).then(on_resolve)
        return on_resolve(result)
    return wrapper
