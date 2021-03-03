import os
from flask import Flask, jsonify, abort
from fixer import *


FIXER_API_KEY = os.environ['FIXER_API_KEY']
fixer_api = FixerApi(FIXER_API_KEY)
app = Flask(__name__)


@app.route('/health')
def health():
    api_response = fixer_api.latest()
    return {
        'fixer_ok': api_response.get('success', False),
        # 'response': api_response, # uncomment this for all rates in the health check
    }


@app.route('/rates/<string:source>/<string:target>')
def conversion_rate(source, target):
    source = source.upper()
    target = target.upper()

    try:
        conversion_rate = fixer_api.latest_rate(source, target)
    except InvalidArgumentsError as e:
        app.logger.error(str(e))
        abort(400) # Bad Request
    except UnknownError as e:
        app.logger.error(str(e))
        abort(500) # Internal Server Error
    except UpstreamError as e:
        app.logger.error(str(e))
        abort(502) # Bad Gateway

    return jsonify({
        'source': source,
        'target': target,
        'conversion_rate': conversion_rate,
    })


@app.route('/convert/<string:source>/<string:target>/<int:amount>')
@app.route('/convert/<string:source>/<string:target>/<float:amount>')
def convert_amount(source, target, amount):
    source = source.upper()
    target = target.upper()

    try:
        converted = fixer_api.convert_amount(source, target, amount)
    except InvalidArgumentsError as e:
        app.logger.error(str(e))
        abort(400) # Bad Request
    except UnknownError as e:
        app.logger.error(str(e))
        abort(500) # Internal Server Error
    except UpstreamError as e:
        app.logger.error(str(e))
        abort(502) # Bad Gateway

    original_round, original_formatted, _, _ = format_currency_value(amount)
    converted_round, converted_formatted, major_units, minor_units = format_currency_value(converted)

    return jsonify({
        'source': source,
        'target': target,
        'original': original_round,
        'original_str': original_formatted,
        'converted': converted_round,
        'converted_str': converted_formatted,
        'major_units': major_units,
        'minor_units': minor_units,
    })


def format_currency_value(exact):
    """
    This just rounds the currency to two decimals exactly, since most languages
    don't support trailing zeroes. I also included major and minor units in
    case a frontend wants to visually format those differently.
    """
    converted = round(exact, 2)
    formatted = '{:0.2f}'.format(converted)
    major_units = int(converted)
    minor_units = round(100 * (exact - major_units))
    return converted, formatted, major_units, minor_units
