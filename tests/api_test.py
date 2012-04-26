from aecore.test_utils import BaseTestCase
from aerest.resources import NDBResource
from aerest.api import Api

from google.appengine.ext import ndb

import webapp2
from webapp2_extras.routes import PathPrefixRoute


class Person(ndb.Model):
    name = ndb.StringProperty()

class House(ndb.Model):
    address = ndb.StringProperty()


class PersonResource(NDBResource):
    resource_model = Person
    resource_name = 'person'
    resource_name_plural = 'people'

class HouseResource(NDBResource):
    resource_model = House
    resource_name = 'address'
    resource_name_plural = 'addresses'


api_v1 = Api()
api_v1.register(PersonResource)
api_v1.register(HouseResource)

routes = [
    PathPrefixRoute(r'/api/v1', api_v1.get_routes()),
    ]

application = webapp2.WSGIApplication(routes)


class TestApi(BaseTestCase):

    def setUp(self):
        super(TestApi, self).setUp()

    def test_get_routes(self):
        routes = api_v1.get_routes()
        self.assertEqual(len(routes), 14)
