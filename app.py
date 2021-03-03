import os
from flask import Flask, jsonify, abort
from currency import *


FIXER_API_KEY = os.environ['FIXER_API_KEY']
fixer_api = FixerApi(FIXER_API_KEY)
app = Flask(__name__)


@app.route('/health')
def health():
    api_response = fixer_api.latest()
    return {
        'fixer_ok': api_response.get('success', False),
        #'response': api_response,
    }


@app.route('/rates/<string:source>/<string:target>')
def conversion_rate(source, target):
    source, target = parse_currency_codes(source, target)
    base, rates = get_base_and_rates()

    converter = CurrencyConverter(base, rates)
    conversion_rate = converter.get_conversion_rate(source, target)

    return jsonify({
        'source': source,
        'target': target,
        'conversion_rate': conversion_rate,
    })


@app.route('/convert/<string:source>/<string:target>/<int:amount>')
@app.route('/convert/<string:source>/<string:target>/<float:amount>')
def convert_value(source, target, amount):
    if not is_valid_amount(amount):
        abort(400)

    source, target = parse_currency_codes(source, target)
    base, rates = get_base_and_rates()

    converter = CurrencyConverter(base, rates)
    converted = converter.convert_currency(source, target, amount)

    original_formatted, _, _ = format_currency_value(amount)
    converted_formatted, major_units, minor_units = format_currency_value(converted)

    return jsonify({
        'source': source,
        'target': target,
        'original': original_formatted,
        'converted': converted_formatted,
        'major_units': major_units,
        'minor_units': minor_units,
    })


def parse_currency_codes(source, target):
    """
    I am OK with giving the client some leeway on capitalization.
    """
    source = source.upper()
    target = target.upper()
    if not (is_valid_currency_code(source) and is_valid_currency_code(target)):
        abort(400) # 400 - Bad Request

    return source, target


def get_base_and_rates():
    api_response = fixer_api.latest()

    if not api_response.get('success'):
        code = api_response.get('error', {}).get('code')
        if code:
            """
            I am greatly oversimplifying here. Fixer includes useful error
            codes for things like getting rate-limited. Anyway, if we don't
            reject your request for bad parameters AND Fixer returns a well-
            formed error, something is wrong in this service.
            """
            abort(500) # Internal Server Error
        else:
            """
            Requests cannot parse the JSON returned by Fixer, which usually
            returns JSON errors with codes. This means something is probably
            wrong on their end.
            """
            abort(502) # Bad Gateway

    if 'base' not in api_response or 'rates' not in api_response:
        abort(500) # Internal Server Error

    base = api_response['base']
    rates = api_response['rates']

    return base, rates


def format_currency_value(exact):
    converted = round(exact, 2)
    formatted = '{:0.2f}'.format(converted)
    major_units = int(converted)
    minor_units = round(100 * (exact - major_units))
    return formatted, major_units, minor_units