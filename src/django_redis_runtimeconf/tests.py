from django.test import TestCase
from rest_framework.test import APITestCase

from users.models import User

from .interface import get_runtime_client

# Create your tests here.


class models_InterfaceClassTest(TestCase):
    def setUp(self):
        self.runtimeconf = get_runtime_client()

    def test_singleton_behaviour(self):
        new_conf = get_runtime_client()
        self.assertEqual(new_conf, self.runtimeconf)
        self.assertEqual(new_conf.keys(), self.runtimeconf.keys())

    def test_keys_manipulations(self):
        test_setting = {'test_key': False}
        for key in test_setting:
            self.runtimeconf.addnewkey(key, test_setting[key])
            self.assertTrue(
                key in self.runtimeconf.keys(),
                "key added to the instance"
            )
            self.assertTrue(
                key.encode() in self.runtimeconf.client.keys(),
                "key added to the redis"
            )
            self.assertEqual(
                type(test_setting[key]), type(self.runtimeconf.keys()[key]),
                "type remains the same in the instance"
            )
            self.assertEqual(
                bytes, type(self.runtimeconf.client.get(key)),
                "should be byte string in redis"
            )
            self.runtimeconf.removekey(key)
            self.assertFalse(
                key in self.runtimeconf.keys(),
                "key removed from the instance"
            )
            self.assertFalse(
                key.encode() in self.runtimeconf.client.keys(),
                "key removed from the redis"
            )
            self.assertIsNone(
                self.runtimeconf.client.get(key),
                "should return None"
            )


class views_AdminViewsTest(APITestCase):
    def setUp(self):
        self.runtimeconf = get_runtime_client()
        self.profile = User.objects.create_superuser('foo', 'foo@bar.ru', 'password')
        self.client.login(username='foo@bar.ru', password='password')
        self.new_keys = {'newkey_key': 'TESTKEY', 'newkey_value': 'testvalue'}

    def test_change_keys(self):
        old_keys = self.runtimeconf.keys().copy()
        keys = self.runtimeconf.keys().copy()
        keys_before = [keys[item] for item in keys if type(item) == bool]
        for key in keys:
            if type(keys[key]) == bool and keys[key]:
                keys[key] = False
            keys[key] = str(keys[key])
        resp = self.client.post("/admin/runtimeconf/config/", data=keys)
        keys_after = [keys[item] for item in self.runtimeconf.keys() if type(item) == bool]
        self.assertListEqual(
            [False]*len(keys_before),
            keys_after,
            "should all be falses"
        )
        self.assertEqual(
            resp.status_code,
            302,
            "should be redirected to the main view"
        )
        self.client.post("/admin/runtimeconf/config/", data=old_keys)

    def test_new_keys(self):
        resp = self.client.post("/admin/runtimeconf/config/", data=self.new_keys)
        self.assertEqual(
            resp.status_code,
            302,
            "should be redirected to the main view"
        )
        self.assertTrue(
            self.new_keys['newkey_key'] in self.runtimeconf.keys(),
            "key added to the instance"
        )
        self.assertEqual(
            self.new_keys['newkey_value'],
            self.runtimeconf.keys()[self.new_keys['newkey_key']],
            "value is newkey_value field value"
        )
        self.assertTrue(
            self.new_keys['newkey_key'].encode() in self.runtimeconf.client.keys(),
            "key added to the redis"
        )
        self.assertEqual(
            self.new_keys['newkey_value'].encode(),
            self.runtimeconf.client.get(self.new_keys['newkey_key']),
            "value added to the redis"
        )

    def test_delete_keys(self):
        self.client.post("/admin/runtimeconf/config/", data=self.new_keys)
        # logging.critical(self.runtimeconf.keys())
        resp = self.client.post(
            "/admin/runtimeconf/config/delete",
            data={"keys_to_delete": self.new_keys['newkey_key']}
        )
        self.assertEqual(
            resp.status_code,
            302
        )
        self.assertFalse(
            self.new_keys['newkey_key'].encode() in self.runtimeconf.keys(),
            "key removed from the instance"
        )
        self.assertFalse(
            self.new_keys['newkey_key'].encode() in self.runtimeconf.client.keys(),
            "key removed from the redis"
        )
        self.assertIsNone(
            self.runtimeconf.client.get(self.new_keys['newkey_key']),
            "should return None"
        )


class middlewares_UrlToggleTest(APITestCase):
    def setUp(self):
        self.runtimeconf = get_runtime_client()

    def test_toggle_url(self):
        resp = self.client.get('/api/v1/items')
        self.assertEqual(resp.status_code, 200)
        self.runtimeconf.addnewkey('/api/v1/items|GET', False)
        resp = self.client.get('/api/v1/items')
        self.assertEqual(resp.status_code, 405)
