import ast
import datetime
import sys

import redis
import fakeredis
from django.conf import settings
from rest_framework.schemas.generators import EndpointEnumerator

fakeredis_server = fakeredis.FakeServer()


def get_fake_redis_client():
    return fakeredis.FakeStrictRedis(server=fakeredis_server)




class RuntimeConfClient(object):
    """
    Interface for using redis for our
    dynamic settings key storage
    """

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, *args, **kwargs):
        self.client = None
        self.last_update = datetime.datetime.now().timestamp()
        self._keys = dict()

    def keys(self):
        now = datetime.datetime.now().timestamp()
        if datetime.timedelta(
            now - self.last_update
        ).seconds > settings.RUNTIMECONF_KEYS_EXPIRE or len(self._keys) == 0:
            self._keys = self.fetch_current_keys()
            self.last_update = now
        return self._keys

    def fetch_current_keys(self):
        """
        Get current keys from redis
        """
        keys = dict()
        for key in self.client.scan_iter():
            try:
                keys.update({key.decode(): ast.literal_eval(self.client.get(key).decode())})
            except ValueError:
                keys.update({key.decode(): self.client.get(key).decode()})
        return keys

    def addnewkey(self, key, value):
        """
        Add new setting
        """
        self.client.set(str(key), str(value))
        self._keys.update({str(key): value})
        self.keys()

    def removekey(self, key):
        """
        Delete key
        """
        self.client.delete(key)
        self._keys.pop(key)
        self.keys()

    def get_endpoints_toggle(self):
        for endpoint in EndpointEnumerator().get_api_endpoints():
            endpoint_name = endpoint[0].rsplit("{pk}")[0].rsplit("{uid}")[0]
            if ('{}|{}'.format(
                endpoint_name,
                endpoint[1]
            )) not in self._keys:
                self.addnewkey(
                    str('{}|{}'.format(
                        endpoint_name,
                        endpoint[1]
                    )), True)


class TestRuntimeConfClient(RuntimeConfClient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = get_fake_redis_client()
        self.get_endpoints_toggle()


class ActualRuntimeConfClient(RuntimeConfClient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = settings.RUNTIMECONF_REDIS_URL
        self.client = redis.from_url(self.url)
        self.get_endpoints_toggle()


def get_runtime_client():
    if 'test' in sys.argv[1:]:
        conf = TestRuntimeConfClient()
    else:
        conf = ActualRuntimeConfClient()
    return conf
