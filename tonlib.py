import ctypes
import pathlib
import json

from os.path import abspath
from os import mkdir as makedir


class tonlib:
    def __init__(self, pathlib, global_config, workdir):
        self.pathlib = pathlib
        self.global_config = global_config

        lib = ctypes.CDLL(self.pathlib)
        lib.tonlib_client_json_create.argtypes = []
        lib.tonlib_client_json_create.restype = ctypes.c_void_p

        lib.tonlib_client_json_send.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        lib.tonlib_client_json_send.restype = None

        lib.tonlib_client_json_receive.argtypes = [ctypes.c_void_p, ctypes.c_double]
        lib.tonlib_client_json_receive.restype = ctypes.c_char_p

        lib.tonlib_client_json_execute.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        lib.tonlib_client_json_execute.restype = ctypes.c_char_p

        lib.tonlib_client_json_destroy.argtypes = [ctypes.c_void_p]
        lib.tonlib_client_json_destroy.restype = None

        self.lib = lib

        self.handle = self.lib.tonlib_client_json_create()
        self._init(global_config, keystore=workdir)

    def __del__(self):
        self.lib.tonlib_client_json_destroy(self.handle)

    def send(self, request):
        self.lib.tonlib_client_json_send(self.handle, ctypes.c_char_p(request.encode('utf-8')))

    def receive(self, timeout=60.0):
        res = self.lib.tonlib_client_json_receive(self.handle, ctypes.c_double(timeout))
        try:
            if res is not None:
                res = json.loads(res.decode('utf-8'))
            return res
        except:
            return None

    def query(self, query, timeout=60.0):
        self.send(query)
        result = None
        tryes = 100
        while (not isinstance(result, dict)) or (result['@type'] == 'updateSyncState') and tryes > 0:
          result = self.receive(timeout)
          tryes -= 1
        if tryes == 0:
            return None
        return result

    def execute(self, request):
        return self.lib.tonlib_client_json_execute(self.handle, ctypes.c_char_p(request.encode('utf-8')))

    def _init(self, global_config, keystore):
        try:
          makedir(abspath(keystore))
        except:
          pass
        keystore_obj = {
            '@type': 'keyStoreTypeDirectory',
            'directory': abspath(keystore)
        }
        init_obj = {
            '@type': 'init',
            'options': {
                '@type': 'options',
                'config': {
                    '@type': 'config',
                    'config': global_config,
                    'use_callbacks_for_network': False,
                    'blockchain_name': '',
                    'ignore_cache': False
                },
                'keystore_type': keystore_obj
            }
        }
        return self.query(json.dumps(init_obj))


def estimateFee(tonlib, address, body, init_code, init_data):
    data = {
        '@type': 'raw.createQuery',
        'body': body,
        'init_code': init_code,
        'init_data': init_data,
        'destination': {
          'account_address': address
        }
    }
    query_info = tonlib.ton_exec(data)
    data = {
        '@type': 'query.estimateFees',
        'id': query_info['id'],
        'ignore_chksig': True
    }
    return tonlib.ton_exec(data)


if __name__ == "__main__":

    with open('test.rocks.config.json', 'r') as f:
        global_config = f.read()

    t = tonlib('/home/user/gram/gram-ton/build/tonlib/', global_config, './workdir')

    request = '''
    {
        "@type":"raw.getAccountState",
        "account_address": {
            "@type":"accountAddress",
            "account_address": "-1:0000000000000000000000000000000000000000000000000000000000000000",
            "@extra":""
        }
    }
    '''
    answer = t.query(request)
    print(answer)


