import requests


SUPPORTED_CURRENCIES = ['USD', 'GBP', 'EUR']


def is_valid_amount(amount):
    return amount >= 0


def is_valid_currency_code(code):
    return code in SUPPORTED_CURRENCIES


class FixerApi:
    def __init__(self, access_key):
        self.access_key = access_key
        self.latest_url = 'http://data.fixer.io/api/latest'
        self.convert_url = 'http://data.fixer.io/api/convert'

    def do_request(self, url, params):
        full_params = {
            'access_key': self.access_key,
            **params,
        }

        api_response = {}
        try:
            response = requests.get(url, params=full_params)
            api_response = response.json()
        except ValueError:
            api_response = {}

        if not api_response.get('success'):
            code = api_response.get('error', {}).get('code')
            info = api_response.get('error', {}).get('info')
            if code:
                """
                I am greatly oversimplifying here. Fixer includes useful error
                codes for things like getting rate-limited. Anyway, if we don't
                reject your request for bad parameters AND Fixer returns a well-
                formed error, something is wrong in this service.
                """
                raise RuntimeError(info)
            else:
                """
                Requests cannot parse the JSON returned by Fixer, which usually
                returns JSON errors with codes. This means something is probably
                wrong on their end.
                """
                raise RuntimeError('fixer API is unavailable')

        return api_response


    def latest(self):
        params = {
            'symbols': ','.join(SUPPORTED_CURRENCIES), # the dreaded join
        }
        return self.do_request(self.latest_url, params)


    def latest_rate(self, source, target):
        if not (is_valid_currency_code(source) and is_valid_currency_code(target)):
            raise ValueError('unsupported currency')

        params = {
            'base': source,
            'symbols': target,
        }
        api_response = self.do_request(self.latest_url, params)

        if target not in api_response.get('rates', {}):
            raise RuntimeError('target conversion rate not in response')

        return api_response['rates'][target]


    def convert_amount(self, source, target, amount):
        if not (is_valid_currency_code(source) and is_valid_currency_code(target)):
            raise ValueError('unsupported currency')

        if not is_valid_amount(amount):
            raise ValueError('invalid amount')

        params = {
            'from': source,
            'to': target,
            'amount': amount
        }
        api_response = self.do_request(self.convert_url, params)

        if 'result' not in api_response:
            raise RuntimeError('result not in response')

        return api_response['result']
