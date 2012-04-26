# -*- coding: utf-8 -*-
"""
    aerest.api
    ====================================

    :copyright: 2012 by Kyle Finley.
    :license: Apache Software License, see LICENSE for details.

    :copyright: 2010 by Daniel Lindsley.
    :license: BSD License, see LICENSE for details.

"""


class Api(object):
    def __init__(self):
        self._registry = {}
        self._canonicals = {}

    def register(self, resource):
        resource_name = getattr(resource, 'resource_name', None)
        if resource_name is None:
            raise Exception(
                "Resource %r must define a 'resource_name'." % resource)

        self._registry[resource_name] = resource


    def unregister(self, resource_name):
        """
        If present, unregisters a resource from the API.
        """
        if resource_name in self._registry:
            del(self._registry[resource_name])

        if resource_name in self._canonicals:
            del(self._canonicals[resource_name])

    def get_routes(self):
        routes_list = []
        for name in sorted(self._registry.keys()):
            routes_list.extend(self._registry[name].get_routes())

        return routes_list
