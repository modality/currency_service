import requests


SUPPORTED_CURRENCIES = ['USD', 'GBP', 'EUR']


def is_valid_amount(amount):
    return amount >= 0


def is_valid_currency_code(code):
    return code in SUPPORTED_CURRENCIES


class CurrencyConverter:
    def __init__(self, base, rates):
        """
        Constructor.

        Args:
            base (str): string currency code for the base currency, e.g. "EUR"
            rates (dict): dictionary of conversion rates
        """

        if not is_valid_currency_code(base):
            raise ValueError('unsupported base currency')

        if not all(c in rates for c in SUPPORTED_CURRENCIES):
            raise ValueError('rates does not contain all supported currencies')

        if not all(r > 0 for r in rates.values()):
            raise ValueError('invalid conversion rate')

        self.base = base
        self.rates = rates


    def get_conversion_rate(self, source, target):
        """
        Produces a conversion rate from the source to target currency.

        Args:
            source (str): starting currency
            target (str): ending currency

        Returns:
            Floating point conversion rate from source to target.
        """
        if not (is_valid_currency_code(source) and is_valid_currency_code(target)):
            raise ValueError('unsupported currency')

        if source == target:
            return 1

        if source == self.base:
            return self.rates[target]

        if target == self.base:
            return 1.0 / self.rates[source]

        return self.get_conversion_rate(source, self.base) * self.get_conversion_rate(self.base, target)


    def convert_currency(self, source, target, amount):
        """
        Converts an amount from a source to a target currency.

        Args:
            source (str): starting currency
            target (str): ending currency
            amount (float): amount of money to convert
        """
        if not is_valid_amount(amount):
            raise ValueError('invalid amount')

        conversion_rate = self.get_conversion_rate(source, target)

        return amount * conversion_rate


class FixerApi:
    def __init__(self, access_key):
        self.access_key = access_key
        self.latest_url = 'http://data.fixer.io/api/latest'


    def latest(self):
        params = {
            'access_key': self.access_key,
            'symbols': ','.join(SUPPORTED_CURRENCIES), # the dreaded join
        }

        try:
            response = requests.get(self.latest_url, params=params)
            json_response = response.json()
            return json_response
        except ValueError:
            return {}
