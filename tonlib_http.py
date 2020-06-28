from flask import Flask
from flask import request
from tonlib_api import tonlib_api
from ton_pool import TonThreadPool, TonWorker
import json

with open('options.json', 'r') as f:
    options = json.load(f)

with open(options['HELP_FILE'], 'r') as f:
    help_string = f.read()

with open(options['GLOBAL_CONFIG'], 'r') as f:
    global_config = f.read()

app = Flask(__name__)

@app.after_request
def after_request(response):
    if options['DEBUG']:
        header = response.headers
        header['Access-Control-Allow-Origin'] = '*'
        header["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS",
        header["Access-Control-Allow-Headers"] = "X-Requested-With, content-type, Authorization"
    return response

def ton_worker(tasks):
    return TonWorker(tasks, tonlib_api, (options['LIB_PATH'], global_config, options['WORKDIR']))

ton_pool = TonThreadPool(ton_worker, options['MIN_WORKERS'], options['MAX_WORKERS'])


@app.route("/api/v1")
def help():
    return help_string


@app.route("/api/v1/jsonRPC", methods=['POST'])
def jsonRPC():
    if request.is_json:
        print('New RPC json request: ' + str(request.json), flush=True)
    else:
        print('New RPC request: ' + str(request), flush=True)


    reply = {'ok': False}

    if request.method != 'POST':
        reply['error'] = 'Must be POST request'
        return reply
    if not request.is_json:
        reply['error'] = 'Must be json request'
        return reply

    if 'id' in request.json:
        reply['id'] = request.json['id']

    try:
        if request.json['jsonrpc'] != '2.0':
            reply['error'] = 'Invalid RPC version'
            return reply
        if not 'params' in request.json:
            reply['error'] = 'No params in request'
            return reply
    except Exception as e:
        reply['error'] = 'Invalid request'
        return reply

    try:
        result = ton_pool.add_task(request.json['method'], request.json['params'], timeout=options['TIMEOUT'])
        if type(result) is dict and '@type' in result and result['@type'] == 'error':
            reply['error'] = result['message']
            reply['code'] = result['code']
        else:
            reply['ok'] = True
            reply['result'] = result
        return reply
    except Exception as e:
        print('Exception: ' + str(e))
        reply['error'] =  'Internal error (12)'
        return reply


if __name__ == "__main__":
    app.run(host=options['HOST'], port=options['PORT'], debug=options['DEBUG'], threaded=True)

