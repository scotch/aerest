# -*- coding: utf-8 -*-
"""
    aerest.resources
    ====================

    :copyright: 2012 by Kyle Finley.
    :license: Apache Software License, see LICENSE for details.

    :copyright: 2010 by Daniel Lindsley.
    :license: BSD License, see LICENSE for details.

"""

import json
import webapp2
from google.appengine.ext import ndb

from aerest.authentication import Authentication
from aerest.authorization import AdminAuthorization
from aerest.authorization import ReadAuthorization


class NDBResource(webapp2.RequestHandler):

    authentication = Authentication
    authorization = [ReadAuthorization, AdminAuthorization]
    resource_model = None
    resource_name = None
    resource_name_plural = None
    id_type = long

    @property
    def _resource_model(self):
        """
        Helper method for resource_model
        """
        return self.resource_model

    @property
    def _resource_name(self):
        """
        Helper method for resource_name
        """
        return self.resource_name

    @property
    def _resource_name_plural(self):
        """
        Helper method for resource_name_plural
        """
        if self.resource_name_plural is not None:
            return self.resource_name_plural
        else:
            return "{}s".format(self.resource_name)

    @property
    def _id_type(self):
        """
        Helper method for self.id_type
        """
        return self.id_type

    def _generate_key(self, id):
        return ndb.Key(self._resource_model, self._id_type(id))

    def dispatch(self):
        # Check if the user is authenticated.
        self.is_authenticated()
        # Check if the user is authorized.
#        self.is_authorized()
        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            pass

    def is_authenticated(self):
        """
        Handles checking if the user is authenticated and dealing with
        unauthenticated users.

        """
        # Authenticate the request as needed.
        auth_result = self.authentication().is_authenticated(
            self.request)

        if not auth_result is True:
            self.abort(401)

    def is_authorized(self, object=None):
        """
        Handles checking of permissions to see if the user has authorization
        to GET, POST, PUT, or DELETE this resource.  If ``object`` is provided,
        the authorization backend can apply additional row-level permissions
        checking.
        """
        auth_result = False

        for auth in self.authorization:
            auth_result = auth().is_authorized(self.request, object)
            if auth_result is True: break

        if isinstance(auth_result, webapp2.Response):
            return

        if not auth_result is True:
            return self.abort(401)

    @classmethod
    def get_routes(cls):
        resource_name_plural = cls.resource_name_plural
        if resource_name_plural is None:
            resource_name_plural = "{}s".format(cls.resource_name)
        return [
            webapp2.Route(r'/{}'.format(resource_name_plural), handler=cls, handler_method='find_many', methods=['GET']),
            webapp2.Route(r'/{}'.format(resource_name_plural), handler=cls, handler_method='create', methods=['POST']),
            webapp2.Route(r'/{}'.format(resource_name_plural), handler=cls, handler_method='update_many', methods=['PUT']),
            webapp2.Route(r'/{}'.format(resource_name_plural), handler=cls, handler_method='delete_many', methods=['DELETE']),
            webapp2.Route(r'/{}/<id>'.format(resource_name_plural), handler=cls, handler_method='find', methods=['GET']),
            webapp2.Route(r'/{}/<id>'.format(resource_name_plural), handler=cls, handler_method='update', methods=['PUT']),
            webapp2.Route(r'/{}/<id>'.format(resource_name_plural), handler=cls, handler_method='delete', methods=['DELETE']),
            ]

    def render_json(self, data):
        self.response.headers.add_header(
            'content-type', 'application/json', charset='utf-8')
        self.response.out.write(json.dumps(data))

    def _find_entity(self, id):
        e = self._resource_model.get_by_id(self._id_type(id))

        # Check authorization
        self.is_authorized(e)

        return e

    def _find_entities(self, ids):
        assert isinstance(ids, list), 'ids must be a list.'
        keys = [self._generate_key(i) for i in ids]
        entities = ndb.get_multi(keys)

        # Check authorization
        for e in entities:
            self.is_authorized(e)

        return entities
    find_entities = _find_entities

    def _find_entities_query(self, query):
        # TODO: implement
        raise NotImplementedError
    find_entities_query = _find_entities_query

    def _find_entities_all(self):
        entities = self._resource_model.query().fetch(1000)

        # Check authorization
        for e in entities:
            self.is_authorized(e)

        return entities
    find_entities_all = _find_entities_all

    def _create_entity(self, data):
        # allocate_ids so that we can append the id to the `data` prior to the
        # datastore put.
        first_id, last_id = self._resource_model.allocate_ids(1)
        data['id'] = first_id
        e = self._resource_model(id=first_id, data=data)

        # Check authorization
        self.is_authorized(e)

        e.put()
        return e
    create_entity = _create_entity

    def _create_entities(self, data):
        assert isinstance(data, list),\
        "create_entities requires data to be a list."
        # allocate_ids so that we can append the id to the `data` prior to the
        # datastore put.
        res_id, last_id = self._resource_model.allocate_ids(len(data))
        entities = []
        for v in data:
            v['id'] = res_id
            e = self._resource_model(id=res_id, data=v)

            # Check authorization
            self.is_authorized(e)

            entities.append(e)
            res_id += 1
        ndb.put_multi(entities)
        return entities
    create_entities = _create_entities

    def _update_entity(self, id, data):
        e = self._resource_model.get_by_id(int(id))
        if e is None:
            return None

        # Check authorization
        self.is_authorized(e)

        e.data = data
        e.put()
        return e
    update_entity = _update_entity

    def _update_entities(self, data):
        ids = [d['id'] for d in data]
        entities = self.find_entities(ids)
        updated_entities = []
        for i, e in enumerate(entities):

            # Check authorization
            self.is_authorized(e)

            e.data = data[i]
            updated_entities.append(e)
        ndb.put_multi(updated_entities)
        return updated_entities
    update_entities = _update_entities

    def _delete_entity(self, id):

        # Check authorization
        e = self._generate_key(id).get()
        self.is_authorized(e)

        return self._generate_key(id).delete()
    delete_entity = _delete_entity

    def _delete_entities(self, ids):
        keys = [self._generate_key(id) for id in ids]

        # TODO: maybe there is a better way to accomplish this.
        # For certain authorization strategies it is necessary to retrieve
        # the entity to verify that the user is authorized to delete the
        # record.
        entities = ndb.get_multi(keys)
        for e in entities:
            # Check authorization
            self.is_authorized(e)

        return ndb.delete_multi(keys)
    delete_entities = _delete_entities

    # Handlers
    def _find(self, **kwargs):
        e = self._find_entity(kwargs['id'])
        data = {}
        if e is None:
            self.abort(404)
        # if the id is missing from the data, add it.
        if not e.data.get('id'):
            e.data['id'] = e.key.id()
        data[self._resource_name] = e.data
        return self.render_json(data)
    find = _find

    def _find_many(self, **kwargs):
        data = {}
        if not self.request.body:
            entities = self.find_entities_all()
        else:
            j = json.loads(self.request.body)
            # If we have a JSON body determine the type of query
            try:
                d = j['ids']
                entities = self.find_entities(d)
            except KeyError:
                try:
                    d = j['query']
                    entities = self.find_entities_query(d)
                except KeyError:
                    # TODO: return an error message to users
                    raise Exception(
                        "JSON is not properly formed. Must be prefixed with "
                        "'ids' or 'query'")
        data[self._resource_name_plural] = [e.data for e in entities]
        return self.render_json(data)
    find_many = _find_many

    def _create(self, **kwargs):
        j = json.loads(self.request.body)
        # determine if the request was create or create many
        data = {}
        try:
            d = j[self._resource_name]
            e = self.create_entity(d)
            data[self._resource_name] = e.data
        except KeyError, e:
            try:
                d = j[self._resource_name_plural]
                e = self.create_entities(d)
                data[self._resource_name_plural] = [i.data for i in e]
            except KeyError, e:
                # TODO: return an error message to users
                raise Exception(
                    "JSON is not properly formed. Must be prefixed with "
                    "'resource_name' or 'resource_name_plural'")
        return self.render_json(data)
    create = _create

    def _update(self, **kwargs):
        id = kwargs['id']
        j = json.loads(self.request.body)
        data = {}
        try:
            d = j[self._resource_name]
        except KeyError, e:
            # TODO: return an error message to users
            raise Exception(
                "JSON is not properly formed. Must be prefixed with "
                "'resource_name' or 'resource_name_plural'")
        e = self.update_entity(id, d)
        if e is None:
            self.abort(404)
        data[self._resource_name] = e.data
        return self.render_json(data)
    update = _update

    def _update_many(self, **kwargs):
        j = json.loads(self.request.body)
        data = {}
        try:
            d = j[self._resource_name_plural]
        except KeyError, e:
            # TODO: return an error message to users
            raise Exception(
                "JSON is not properly formed. Must be prefixed with "
                "'resource_name' or 'resource_name_plural'")
        e = self.update_entities(d)
        if e is None:
            return self.abort(code=404)
        data[self._resource_name_plural] = [i.data for i in e]

        return self.render_json(data)
    update_many = _update_many

    def _delete(self, **kwargs):
        id = kwargs['id']
        deleted = self.delete_entity(id)
        return self.render_json(deleted)
    delete = _delete

    def _delete_many(self, **kwargs):
        j = json.loads(self.request.body)
        try:
            ids = j['ids']
        except KeyError, e:
            # TODO: return an error message to users
            raise Exception(
                "JSON is not properly formed. "
                "JSON body must contain {'id': [] }")
        e = self.delete_entities(ids)
        return self.render_json(e)
    delete_many = _delete_many