import pytest
from unittest.mock import MagicMock
import requests
from fixer import *


LATEST = {
    "success": True,
    "base": "EUR",
    "rates": {
        "GBP": 0.882047,
    }
}

CONVERT = {
    "success": True,
    "query": {
        "from": "EUR",
        "to": "GBP",
        "amount": 100
    },
    "result": 88.2047
}

CONVERT_BAD = {
    "success": True,
    "query": {
        "from": "EUR",
        "to": "GBP",
        "amount": 100
    },
}

CONVERT_ZERO = {
    "success": False,
    "error": {
        "code": 403,
        "info": "You have not specified an amount to be converted.",
    }
}


def mock_fixer_api(status_code, json_response):
    class FakeResponse:
        def __init__(self, status_code, json_response):
            self.status_code = status_code
            self.json_response = json_response

        def json(self):
            return self.json_response

    requests.get = MagicMock(return_value=FakeResponse(status_code, json_response))
    fixer_api = FixerApi('secret_key')
    return fixer_api


def test_good_looking_currency_codes():
    assert is_valid_currency_code('USD') is True
    assert is_valid_currency_code('GBP') is True
    assert is_valid_currency_code('EUR') is True
    assert is_valid_currency_code('JPY') is False
    assert is_valid_currency_code('SIM') is False


def test_bad_looking_currency_codes():
    assert is_valid_currency_code(5) is False
    assert is_valid_currency_code({}) is False
    assert is_valid_currency_code('usd') is False
    assert is_valid_currency_code('xyz') is False
    assert is_valid_currency_code('DROP TABLE users') is False


def test_valid_amounts():
    assert is_valid_amount(0) is True
    assert is_valid_amount(100.30) is True
    assert is_valid_amount(-0.5) is False
    assert is_valid_amount('100') is False
    assert is_valid_amount('xyz') is False


def test_api_failures():
    fixer_api = mock_fixer_api(500, {})

    with pytest.raises(UpstreamError) as excinfo:
        fixer_api.latest_rate('EUR', 'USD')
    assert 'fixer API is unavailable' in str(excinfo.value)

    fixer_api = mock_fixer_api(200, {'success': False, 'error': {'code': 418, 'info': 'you are a teapot'}})

    with pytest.raises(UnknownError) as excinfo:
        fixer_api.convert_amount('EUR', 'USD', 100)
    assert 'teapot' in str(excinfo.value)


def test_latest_rate():
    fixer_api = mock_fixer_api(200, LATEST)

    # Invalid currency
    with pytest.raises(InvalidArgumentsError) as excinfo:
        fixer_api.latest_rate('EUR', 'SIM')
    assert 'unsupported currency' in str(excinfo.value)

    # Valid currencies with a strange response
    with pytest.raises(UnknownError) as excinfo:
        fixer_api.latest_rate('EUR', 'USD')
    assert 'target conversion rate not in response' in str(excinfo.value)

    # Valid currencies with the correct response
    assert fixer_api.latest_rate('EUR', 'GBP') == 0.882047


def test_convert_amount():
    fixer_api = mock_fixer_api(200, CONVERT)

    # Invalid currency
    with pytest.raises(InvalidArgumentsError) as excinfo:
        fixer_api.convert_amount('EUR', 'SIM', 100)
    assert 'unsupported currency' in str(excinfo.value)

    # Invalid amount
    with pytest.raises(InvalidArgumentsError) as excinfo:
        fixer_api.convert_amount('EUR', 'GBP', -0.5)
    assert 'invalid amount' in str(excinfo.value)

    assert fixer_api.convert_amount('EUR', 'GBP', 100) == 88.2047


def test_bad_convert_amount():
    fixer_api = mock_fixer_api(200, CONVERT_BAD)

    # Valid currencies with a strange response
    with pytest.raises(UnknownError) as excinfo:
        fixer_api.convert_amount('EUR', 'GBP', 100)
    assert 'result not in response' in str(excinfo.value)


def test_convert_zero():
    fixer_api = mock_fixer_api(200, CONVERT_ZERO)

    assert fixer_api.convert_amount('USD', 'GBP', 0) == 0