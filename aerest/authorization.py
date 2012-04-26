# -*- coding: utf-8 -*-
"""
    aerest.authorization
    ========================

    :copyright: 2012 by Kyle Finley.
    :license: Apache Software License, see LICENSE for details.

    :copyright: 2010 by Daniel Lindsley.
    :license: BSD License, see LICENSE for details.

"""


class Authorization(object):
    """
    A base class that provides no permissions checking.
    """

    def __get__(self, instance, owner):
        """
        Makes ``Authorization`` a descriptor of ``ResourceOptions`` and creates
        a reference to the ``ResourceOptions`` object that may be used by
        methods of ``Authorization``.
        """
        self.resource_meta = instance
        return self

    def is_authorized(self, request, object=None):
        """
        Checks if the user is authorized to perform the request. If ``object``
        is provided, it can do additional row-level checks.

        Should return either ``True`` if allowed, ``False`` if not or an
        ``HttpResponse`` if you need something custom.
        """
        return True


class ReadAuthorization(Authorization):
    """
    Default Authentication class for ``Resource`` objects.

    Only allows GET requests.
    """

    def is_authorized(self, request, object=None):
        """
        Allow any ``GET`` request.
        """
        if request.method == 'GET':
            return True
        else:
            return False


class AdminAuthorization(Authorization):
    """
    Allows a ``User`` with the 'admin' ``roles`` to modify  ``Resource`` objects.
    """

    def is_authorized(self, request, object=None):
        """
        Allow an admin full access.
        """
        try:
            if 'admin' in request.user.roles:
                return True
            else:
                return False
        except AttributeError:
            raise Exception('To use AdminAuthorization aecore '
                            'must be installed.')


class UserOwnedAuthorization(Authorization):
    """
    Allows a ``User`` with modify resources that they own. For this to work
    the model must have an `owners` property of type list containing the
    Users id.
    """

    def is_authorized(self, request, object=None):

        # CREATE is always allowed.
        if request.method == 'POST':
            return True

        # user must be logged in to check permissions
        # authentication backend must set request.user
        if request.user is None:
            return False

        try:
            is_owner = object.is_owner(request.user.key.id())
        except Exception:
            raise ("To use the UserOwnedAuthorization you must add "
                   "a 'is_owner()' method to your ResourceModel. "
                   "Given a User.key.id() this method should return "
                   "a boolean. True if authorized False if not.")

        if is_owner:
            return True

        return False


class ACLAuthorization(Authorization):
    """
    W.I.P Uses permission checking from ``aecore.models.`` to map ``POST``,
    ``PUT``, and ``DELETE`` to their equivalent django auth permissions.
    """

    def is_authorized(self, request, object=None):
        # GET is always allowed
        if request.method == 'GET':
            return True

        # user must be logged in to check permissions
        # authentication backend must set request.user
        if request.user is None:
            return False

        klass = self.resource_meta.resource_model

        # cannot check permissions if we don't know the model
        if not klass or not getattr(klass, 'resource_model', None):
            return True

        permission_codes = {
            'POST': 'create_{}',
            'PUT': 'updated_{}',
            'DELETE': 'delete_{}',
            }

        # cannot map request method to permission code name
        if request.method not in permission_codes:
            return True

        permission_code = permission_codes[request.method].format(
            klass._get_kind())

        return request.user.has_perm(permission_code)
