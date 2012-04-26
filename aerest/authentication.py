# -*- coding: utf-8 -*-
"""
    aerest.authentication
    ====================================

    :copyright: 2012 by Kyle Finley.
    :license: Apache Software License, see LICENSE for details.

    :copyright: 2010 by Daniel Lindsley.
    :license: BSD License, see LICENSE for details.

"""


class Authentication(object):
    """
    A simple base class to establish the protocol for auth.

    By default, this indicates the user is always authenticated.
    """

    def is_authenticated(self, request, **kwargs):
        """
        Identifies if the user is authenticated to continue or not.

        Should return either ``True`` if allowed, ``False`` if not or an
        ``HttpResponse`` if you need something custom.
        """
        return True

    def get_identifier(self, request):
        """
        Provides a unique string identifier for the requester.

        This implementation returns a combination of IP address and hostname.
        """
        ip = request.remote_addr if request.remote_addr else 'noaddr'
        host_url = request.host_url if request.host_url else 'nohost'
        return "%s_%s".format(ip, host_url)


class AECoreAuthentication(Authentication):
    """
    Handles AEAuth authentication.

    """

    def is_authenticated(self, request, **kwargs):
        """
        Checks if a user is logged in using AEAuth

        Should return either ``True`` if allowed, ``False`` if not..
        """
        if request.user:
            return True
        else:
            return False

    def get_identifier(self, request):
        """
        Provides a unique string identifier for the requestor.

        This implementation returns the user's id.
        """
        return request.user.id

