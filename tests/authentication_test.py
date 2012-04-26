
from aecore.test_utils import BaseTestCase
from aerest.resources import NDBResource

from aerest.authentication import AECoreAuthentication
from aerest.authorization import Authorization

from google.appengine.ext import ndb
from aecore.models import Config
from aecore.models import User
from aecore.models import UserProfile

import webapp2
from webapp2_extras.routes import PathPrefixRoute
import json

class Person(ndb.Model):
    data = ndb.JsonProperty()
    name = ndb.StringProperty()

class PersonResource(NDBResource):
    resource_model = Person
    resource_name = 'person'
    resource_name_plural = 'people'
    # this requires a logged in user.
    authentication = AECoreAuthentication
    # anyone can CRUD
    authorization = [Authorization]

routes = [
    PathPrefixRoute(r'/api', PersonResource.get_routes()),
    ]


application = webapp2.WSGIApplication(routes)

def create_request(method_type, resource_path, request_dict=None, user=None):
    request = webapp2.Request.blank(resource_path)
    request.method = method_type
    request.user = user
    if request_dict is not None:
        request.body = json.dumps(request_dict)
    response = request.get_response(application)
    try:
        body = json.loads(response.body)
    except Exception:
        body = request.body
    return response.status, response, body

def create_person(name):
    fid, lid = Person.allocate_ids(1)
    data = {'id':fid, 'name': name}
    p = Person(id=fid, data=data)
    p.put()
    return p

def create_user(role='admin', id=1):
    u =User()
    u._key = ndb.Key('User', id)
    u.roles = [role]
    u.put()
    return u

class TestResources(BaseTestCase):

    def setUp(self):
        super(TestResources, self).setUp()
        self.register_model('Person', Person)
        self.register_model('Config', Config)
        self.register_model('User', User)
        self.register_model('UserProfile', UserProfile)
        self.user = create_user()


    def test_find(self):
        p1 = create_person('Bill Clinton')
        url = '/api/people/{}'.format(p1.key.id())
        status, response, body = create_request('GET', url, user=self.user)
        self.assertEqual(status, '200 OK')
        self.assertEqual(body['person']['id'], p1.key.id())
        self.assertEqual(body['person']['name'], p1.data['name'])

    def test_find_many(self):
        p1 = create_person('Bill Clinton')
        p2 = create_person('George Washington')
        p3 = create_person('Ronald Reagan')
        ids = [p.key.id() for p in [p1, p2, p3]]

        # Find by ids
        url = '/api/people'
        request_dict = {'ids': ids}
        s1, r1, b1 = create_request('GET', url, request_dict, user=self.user)

        self.assertEqual(s1, '200 OK')
        self.assertEqual(type(b1['people']), list)
        self.assertEqual(b1['people'][0]['id'],   p1.key.id())
        self.assertEqual(b1['people'][0]['name'], p1.data['name'])
        self.assertEqual(b1['people'][1]['id'],   p2.key.id())
        self.assertEqual(b1['people'][1]['name'], p2.data['name'])
        self.assertEqual(b1['people'][2]['id'],   p3.key.id())
        self.assertEqual(b1['people'][2]['name'], p3.data['name'])

        # find_all
        url = '/api/people'
        s1, r1, b1 = create_request('GET', url, user=self.user)

        self.assertEqual(s1, '200 OK')
        self.assertEqual(type(b1['people']), list)
        self.assertEqual(b1['people'][0]['id'],   p1.key.id())
        self.assertEqual(b1['people'][0]['name'], p1.data['name'])
        self.assertEqual(b1['people'][1]['id'],   p2.key.id())
        self.assertEqual(b1['people'][1]['name'], p2.data['name'])
        self.assertEqual(b1['people'][2]['id'],   p3.key.id())
        self.assertEqual(b1['people'][2]['name'], p3.data['name'])

        # TODO: find_query

    def test_create(self):
        n1 = 'Ronald Reagan'
        request_dict = {'person': {'name': n1}}
        url = '/api/people'
        s1, r1, b1 = create_request('POST', url, request_dict, user=self.user)
        self.assertEqual(s1, '200 OK')
        self.assertTrue(b1['person']['id'] is not None)
        self.assertEqual(b1['person']['name'], n1)

        # Make sure that it's in the datastore
        q1 = Person.get_by_id(b1['person']['id'])
        self.assertEqual(q1.data['name'], n1)

    def test_create_many(self):
        n1 = 'Bill Clinton'
        p1 = {'name': n1}
        n2 = 'Ronald Reagan'
        p2 = {'name': n2}

        url = '/api/people'
        request_dict = {'people': [p1, p2]}
        s1, r1, bs = create_request('POST', url, request_dict, user=self.user)

        self.assertEqual(s1, '200 OK')
        self.assertEqual(type(bs['people']), list)
        self.assertTrue(bs['people'][0]['id'] is not None)
        self.assertEqual(bs['people'][0]['name'], n1)
        self.assertTrue(bs['people'][1]['id'] is not None)
        self.assertEqual(bs['people'][1]['name'], n2)

        # Make sure that it's in the datastore
        q1 = Person.get_by_id(bs['people'][0]['id'])
        self.assertEqual(q1.data['name'], n1)

        q2 = Person.get_by_id(bs['people'][1]['id'])
        self.assertEqual(q2.data['name'], n2)

    def test_update(self):
        p1 = create_person('Prince')
        nn1 = 'Symbol'

        url = '/api/people/{}'.format(p1.key.id())
        request_dict = {'person': {'id': p1.key.id(), 'name':nn1}}
        s1, r1, b1 = create_request('PUT', url, request_dict, user=self.user)

        self.assertEqual(s1, '200 OK')
        self.assertTrue(b1['person']['id'] is not None)
        self.assertEqual(b1['person']['name'], nn1)

        # Make sure that it's in the datastore
        q1 = Person.get_by_id(b1['person']['id'])
        self.assertEqual(q1.data['name'], nn1)

    def test_update_many(self):
        d1 = create_person('William Clinton')
        n1 = 'Bill "Slicky Willy" Clinton'
        p1 = {'id': d1.key.id(), 'name': n1}

        d2 = create_person('Ronald Reagan')
        n2 = 'Ron "Tear down that wall" Reagan'
        p2 = {'id': d2.key.id(), 'name': n2}

        url = '/api/people'
        request_dict = {'people': [p1, p2]}
        s1, r1, b = create_request('PUT', url, request_dict, user=self.user)

        bs = b['people']
        self.assertEqual(s1, '200 OK')
        self.assertEqual(type(bs), list)
        self.assertEqual(bs[0]['id'], d1.key.id())
        self.assertEqual(bs[0]['name'], n1)
        self.assertEqual(bs[1]['id'], d2.key.id())
        self.assertEqual(bs[1]['name'], n2)

        # Make sure that it's in the datastore
        q1 = Person.get_by_id(bs[0]['id'])
        self.assertEqual(q1.data['name'], n1)

        q2 = Person.get_by_id(bs[1]['id'])
        self.assertEqual(q2.data['name'], n2)

    def test_delete(self):
        p1 = create_person('Bill Clinton')

        url = '/api/people/{}'.format(p1.key.id())
        s1, r1, b1 = create_request('DELETE', url, user=self.user)

        self.assertEqual(s1, '200 OK')
        self.assertEqual(b1, None)

        # try querying
        p1ds = Person.get_by_id(p1.key.id())
        self.assertEqual(p1ds, None)

    def test_delete_list(self):
        p1 = create_person('Bill Clinton')
        p2 = create_person('George Washington')
        p3 = create_person('Ronald Reagan')
        ids = [p.key.id() for p in [p1, p2, p3]]

        url = '/api/people'
        request_dict = {'ids': ids}
        s1, r1, b1 = create_request('DELETE', url, request_dict, user=self.user)

        self.assertEqual(s1, '200 OK')
        self.assertEqual(b1, [None, None, None])

        p1ds = Person.get_by_id(p1.key.id())
        self.assertEqual(p1ds, None)
        p2ds = Person.get_by_id(p2.key.id())
        self.assertEqual(p2ds, None)
        p3ds = Person.get_by_id(p3.key.id())
        self.assertEqual(p3ds, None)
