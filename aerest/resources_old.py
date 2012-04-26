# -*- coding: utf-8 -*-
"""
    aerest.resources_old
    ========================

    :copyright: 2012 by Kyle Finley.
    :license: Apache Software License, see LICENSE for details.

    :copyright: 2010 by Daniel Lindsley.
    :license: BSD License, see LICENSE for details.

"""

import json
import webapp2
from google.appengine.ext import ndb

from aerest.exceptions import ImmediateHttpResponse
from aerest.authentication import Authentication
from aerest.authorization import AdminAuthorization
from aerest.authorization import ReadAuthorization



class Resource(ndb.Model):

    data = ndb.JsonProperty()

    def to_dict(self):
        d = self._to_dict()
        d['id'] = self.key.id()
        return d

    @classmethod
    def get_by_str_id(cls, id):
        return cls.get_by_id(long(id))

    @classmethod
    def _get_entity(cls, **kwargs):
        obj =  cls.get_by_str_id(kwargs['id'])
        if obj is None: return None
        data = obj.data
        if data.get('id') is None:
            data['id'] = obj.key.id()
        return data
    get_entity = _get_entity

    @classmethod
    def _get_entities(cls, **kwargs):
        ids = kwargs['ids']
        ids = ids.split(';')
        es = []
        for id in ids:
            kwargs['id'] = id
            e = cls.get_entity(**kwargs)
            es.append(e)
        return es
    get_entities = _get_entities

    @classmethod
    def _create_entity(cls, **kwargs):
        r = kwargs['obj']
        obj = cls(data=r)
        obj.put()
        data = obj.data
        data['id'] = obj.key.id()
        return data
    create_entity = _create_entity

    @classmethod
    def _create_entities(cls, **kwargs):
        ros = []
        for o in kwargs['objs']:
            kwargs['obj'] = o
            ro = cls.create_entity(**kwargs)
            ros.append(ro)
        return ros
    create_entities = _create_entities

    @classmethod
    def _update_entity(cls, **kwargs):
        r = kwargs['obj']
        try:
            obj = cls.get_by_str_id(r['id'])
        except KeyError:
            raise Exception('Object must contain an id.')
        if obj is None:
            raise Exception('Entity not found.')
        obj.data = r
        obj.put()
        return obj.data
    update_entity = _update_entity

    @classmethod
    def _update_entities(cls, **kwargs):
        ros = []
        for o in kwargs['objs']:
            kwargs['obj'] = o
            ro = cls.update_entity(**kwargs)
            ros.append(ro)
        return ros
    update_entities = _update_entities

    @classmethod
    def _create_key(cls, id):
        return ndb.Key(cls, long(id))
    create_key = _create_key

    @classmethod
    def _delete_entity(cls, id):
        return cls._create_key(id).delete()
    delete_entity = _delete_entity

    @classmethod
    def _delete_entities(cls, ids):
        keys = [cls._create_key(id) for id in ids]
        ndb.delete_multi(keys)
    delete_entities = _delete_entities


class RestHandler(webapp2.RequestHandler):

    resource_class = None

    def dispatch(self):
        # Get a session store for this request.
        self.is_authorized()
        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            pass

    class DefaultOptions:
        authentication = Authentication()
        authorization = [ReadAuthorization(), AdminAuthorization()]
        allowed_methods = ['get', 'post', 'put', 'delete', 'patch']
        list_allowed_methods = None
        detail_allowed_methods = None
        resource_name = None

    class Options:
        # These Options will be overridden by the subclass
        resource_name = None

    def __new__(cls, *args, **kwargs):
        # Handle overrides.
        if cls.Options:
            for override_name in dir(cls.Options):
                # No internals please.
                if not override_name.startswith('_'):
                    setattr(cls.DefaultOptions, override_name,
                        getattr(cls.Options, override_name))
        cls.Options = cls.DefaultOptions
        return super(RestHandler, cls).__new__(cls, *args, **kwargs)

    @classmethod
    def get_routes(cls):
        resource_name = cls.Options.resource_name
        assert resource_name is not None, "You must provide and resource name under Options."
        return [
            webapp2.Route(r'/{}/<id>'.format(resource_name), handler=cls, handler_method='get_detail',    methods=['GET']),
            webapp2.Route(r'/{}/<id>'.format(resource_name), handler=cls, handler_method='post_detail',   methods=['POST']),
            webapp2.Route(r'/{}/<id>'.format(resource_name), handler=cls, handler_method='put_detail',    methods=['PUT']),
            webapp2.Route(r'/{}/<id>'.format(resource_name), handler=cls, handler_method='delete_detail', methods=['DELETE']),
            webapp2.Route(r'/{}/'.format(resource_name), handler=cls, handler_method='get_all',   methods=['GET']),
            webapp2.Route(r'/{}/'.format(resource_name), handler=cls, handler_method='post_list',   methods=['POST']),
            webapp2.Route(r'/{}/'.format(resource_name), handler=cls, handler_method='put_list',    methods=['PUT']),
            webapp2.Route(r'/{}/set/<ids>'.format(resource_name), handler=cls, handler_method='get_list', methods=['GET']),
            webapp2.Route(r'/{}/set/<ids>'.format(resource_name), handler=cls, handler_method='delete_list', methods=['DELETE']),
            ]


    def is_authorized(self, object=None):
        """
        Handles checking of permissions to see if the user has authorization
        to GET, POST, PUT, or DELETE this resource.  If ``object`` is provided,
        the authorization backend can apply additional row-level permissions
        checking.
        """
        auth_result = False

        for auth in self.Options.authorization:
            auth_result = auth.is_authorized(self.request, object)
            if auth_result is True: break

        if isinstance(auth_result, webapp2.Response):
            return

        if not auth_result is True:
            self.abort(401)

    def is_authenticated(self):
        """
        Handles checking if the user is authenticated and dealing with
        unauthenticated users.

        Mostly a hook, this uses class assigned to ``authentication`` from
        ``Resource._meta``.
        """
        # Authenticate the request as needed.
        auth_result = self.Options.authentication.is_authenticated(self.request)

        if isinstance(auth_result, webapp2.Response):
            raise ImmediateHttpResponse(response=auth_result)

        if not auth_result is True:
            self.abort(401)

    def render_json(self, dictionary):
        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
        self.response.out.write(json.dumps(dictionary))

    def get_detail(self, **kwargs):
        obj = self.resource_class.get_entity(**kwargs)
        if obj is None: return self.abort(code=404)
        return self.render_json(obj)

    def get_list(self, **kwargs):
        objs = self.resource_class.get_entities(**kwargs)
        return self.render_json(objs)

    def put_detail(self, **kwargs):
        raise NotImplementedError()

    def put_list(self, **kwargs):
        kwargs['request'] = self.request
        j = json.loads(self.request.body)
        if isinstance(j, list):
            objs = self.resource_class.update_entities(objs=j, **kwargs)
        else:
            objs = self.resource_class.update_entity(obj=j, **kwargs)
        return self.render_json(objs)

    def post_detail(self, **kwargs):
        raise NotImplementedError()

    def post_list(self, **kwargs):
        kwargs['request'] = self.request
        j = json.loads(self.request.body)
        if isinstance(j, list):
            objs = self.resource_class.create_entities(objs=j, **kwargs)
        else:
            objs = self.resource_class.create_entity(obj=j, **kwargs)
        return self.render_json(objs)

    def delete_detail(self, **kwargs):
        id = kwargs['id']
        deleted = self.resource_class.delete_entity(id)
        return self.render_json(deleted)

    def delete_list(self, **kwargs):
        ids = kwargs['ids'].split(';')
        deleted = self.resource_class.delete_entities(ids)
        return self.render_json(deleted)
