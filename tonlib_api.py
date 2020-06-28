from tonlib import tonlib

class tonlib_api:
    def __init__(self, pathlib, global_config, workdir='./workdir'):
        self.tonlib = tonlib(pathlib, global_config, workdir)

    def raw_getAccountState(self, address, timeout=60):
        request = f'''
        {{
            "@type":"raw.getAccountState",
            "account_address": {{
                "@type":"accountAddress",
                "account_address": "{address}",
                "@extra":""
            }}
        }}
        '''
        #print(request)
        return self.tonlib.query(request, timeout=timeout)

    def getAccountState(self, address, timeout=60):
        request = f'''
        {{
            "@type":"getAccountState",
            "account_address": {{
                "@type":"accountAddress",
                "account_address": "{address}",
                "@extra":""
            }}
        }}
        '''
        return self.tonlib.query(request, timeout=timeout)

    def raw_getTransactions(self, address, lt, hash_, timeout=60):
        request = f'''
        {{
            "@type":"raw.getTransactions",
            "account_address": {{
                "@type":"accountAddress",
                "account_address": "{address}",
                "@extra":""
            }},
            "from_transaction_id": {{
                "@type": "from_transaction_id",
                "lt": "{lt}",
                "hash": "{hash_}"
            }}
        }}
        '''
        #print(request)
        return self.tonlib.query(request, timeout=timeout)

    def smc_load(self, address, timeout=60):
        request = f'''
        {{
            "@type":"smc.load",
            "account_address": {{
                "@type":"accountAddress",
                "account_address": "{address}",
                "@extra":""
            }}
        }}
        '''
        #print(request)
        return self.tonlib.query(request, timeout=timeout)

    def smc_runGetMethod(self, address, method, stack, timeout=60):
        smc = self.smc_load(address)
        if smc['@type'] != 'smc.info' or 'id' not in smc:
            return smc

        if type(method) == str:
            m = f'''
            {{
            "@type": "smc.methodIdName",
            "name": "{method}"
            }}
            '''
        else:
            m = f'''
            {{
            "@type": "smc.methodIdNumber",
            "number": "{method}"
            }}
            '''

        request = f'''
        {{
            "@type":"smc.runGetMethod",
            "id": {smc['id']},
            "method": {m},
            "stack": {stack}
        }}
        '''
        #print(request)
        return self.tonlib.query(request, timeout=timeout)


    def raw_sendMessage(self, boc, timeout=60):
        request = f'''
        {{
            "@type":"raw.sendMessage",
            "body": "{boc}"
        }}
        '''
        #print(request)
        return self.tonlib.query(request, timeout=timeout)

    def raw_createQuery(self, address, body, init_code, init_data, timeout=60):
        request = f'''
        {{
            "@type":"raw.createQuery",
            "destination": {{
                "@type":"accountAddress",
                "account_address": "{address}",
                "@extra":""
            }},
            "body": "{body}",
            "init_code": "{init_code}",
            "init_data": "{init_data}"
        }}
        '''
        #print(request)
        return self.tonlib.query(request, timeout=timeout)

    def query_estimateFees(self, address, body, init_code, init_data, ignore_chksig, timeout=60):
        query = self.raw_createQuery(address, body, init_code, init_data, timeout)
        #print(query)
        if query['@type'] != 'query.info' or 'id' not in query:
            return query
        request = f'''
        {{
            "@type":"query.estimateFees",
            "id": "{query['id']}",
            "ignore_chksig": {'true' if ignore_chksig else 'false'}
        }}
        '''
        #print(request)
        reply = self.tonlib.query(request, timeout=timeout)
        #print(reply)
        return reply


    def getAddressInformation(self, addr, timeout):
        return self.raw_getAccountState(addr, timeout=timeout)

    def getExtendedAddressInformation(self, addr, timeout):
        return self.getAccountState(addr, timeout=timeout)

    def getTransactions(self, addr, limit, lt, hash_, to_lt, timeout):
        if lt == -1:
            account = self.raw_getAccountState(addr, timeout=timeout)
            if account['@type'] == "error":
                return account
            lt = int(account['last_transaction_id']['lt'])
            hash_ = account['last_transaction_id']['hash']
        res = {
            '@type': 'raw.transactions',
            'transactions': [],
            'previous_transaction_id': {
                '@type': "internal.transactionId",
                "lt": "0",
                "hash": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
            }
        }
        if lt == 0:
            return res
        limit_cnt = 0
        list_full = False
        while True:
            if lt == 0 or (to_lt > 0 and lt <= to_lt) or (limit > 0 and limit_cnt >= limit):
                res['previous_transaction_id']['lt'] = str(lt)
                res['previous_transaction_id']['hash'] = hash_
                break
            print('get from lt %d' % lt)
            result = self.raw_getTransactions(addr, lt, hash_, timeout)
            print('got %d transactions' % len(result['transactions']))
            if result['@type'] == 'raw.transactions':
                for t in result['transactions']:
                    if t['@type'] == 'raw.transaction':
                        if (limit < 0 or limit_cnt < limit) and (to_lt < 0 or to_lt < int(t['transaction_id']['lt'])):
                            res['transactions'].append(t)
                            limit_cnt += 1
                        elif not list_full:
                            res['previous_transaction_id'] = t['transaction_id']
                            list_full = True
                            break

                if not list_full and 'previous_transaction_id' in result:
                    lt = int(result['previous_transaction_id']['lt'])
                    hash_ = result['previous_transaction_id']['hash']
                else:
                    break

        return res


    def run_method(self, method, arg, timeout=60):
        try:
            if method == 'getAddressInformation':
                address = arg['address']
                return self.getAddressInformation(address, timeout=timeout)

            elif method == 'getExtendedAddressInformation':
                address = arg['address']
                return self.getExtendedAddressInformation(address, timeout=timeout)

            elif method == 'getAddressBalance':
                address = arg['address']
                res = self.getAddressInformation(address, timeout=timeout)
                return res['balance']

            elif method == 'getAddressState':
                address = arg['address']
                res = self.getExtendedAddressInformation(address, timeout=timeout)
                if res['account_state']['@type'] == 'uninited.accountState':
                    return 'uninitialized'
                elif res['account_state']['@type'] == 'raw.accountState':
                    if res['account_state']['frozen_hash'] != '':
                        return 'frozen'
                    else:
                        return 'active'
                else:
                    return 'unknown'

            elif method == 'getTransactions':
                address = arg['address']
                limit = int(arg['limit']) if 'limit' in arg else -1
                lt = int(arg['lt']) if 'lt' in arg else -1
                hash_ = arg['hash'] if 'hash' in arg else ''
                to_lt = int(arg['to_lt']) if 'to_lt' in arg else -1
                return self.getTransactions(address, limit, lt, hash_, to_lt, timeout)

            elif method == 'runGetMethod':
                address = arg['address']
                m = arg['method']
                stack = arg['stack']
                return self.smc_runGetMethod(address, m, stack, timeout)

            elif method == 'sendBoc':
                boc = arg['boc']
                return self.raw_sendMessage(boc, timeout)

            elif method == 'estimateFee':
                address = arg['address']
                body = arg['body']
                init_code = arg['init_code'] if 'init_code' in arg else ''
                init_data = arg['init_data'] if 'init_data' in arg else ''
                ignore_chksig = arg['ignore_chksig'] if 'ignore_chksig' in arg else True
                return self.query_estimateFees(address, body, init_code, init_data, ignore_chksig, timeout)

            else:
                return {'@type': 'error', 'code': 500, 'message': 'Unsupported method'}

        except Exception as e:
            print('run_method Exception: ' + str(e), flush=True)
            return {'@type': 'error', 'code': 500, 'message': 'Invalid request'}


if __name__ == "__main__":

    with open('test.rocks.config.json', 'r') as f:
        global_config = f.read()

    address = '-1:0000000000000000000000000000000000000000000000000000000000000000'
    t = tonlib_api('/home/user/gram/gram-ton/build/tonlib/', global_config)
    '''
    account = t.raw_getAccountState(address)
    try:
        transactions = t.raw_getTransactions(address, account['last_transaction_id']['lt'], account['last_transaction_id']['hash'])
        print(account)
        print(transactions)
    except:
        pass
    '''

    #try:
    transactions = t.run_method('getTransactions', {'address': address, 'limit': 22})
    print(transactions)
    #except:
    #    pass
