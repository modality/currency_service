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
        #'response': api_response,
    }


@app.route('/rates/<string:source>/<string:target>')
def conversion_rate(source, target):
    source, target = parse_currency_codes(source, target)

    try:
        conversion_rate = fixer_api.latest_rate(source, target)
    except ValueError:
        abort(400) # Bad Request
    except RuntimeError as e:
        if e.args[0] == 'fixer API is unavailable':
            abort(502) # Bad Gateway
        else:
            abort(500) # Internal Server Error

    return jsonify({
        'source': source,
        'target': target,
        'conversion_rate': conversion_rate,
    })


@app.route('/convert/<string:source>/<string:target>/<int:amount>')
@app.route('/convert/<string:source>/<string:target>/<float:amount>')
def convert_amount(source, target, amount):
    if not is_valid_amount(amount):
        abort(400)

    source, target = parse_currency_codes(source, target)

    try:
        converted = fixer_api.convert_amount(source, target, amount)
    except ValueError:
        abort(400) # Bad Request
    except RuntimeError as e:
        if e.args[0] == 'fixer API is unavailable':
            abort(502) # Bad Gateway
        else:
            abort(500) # Internal Server Error

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


def format_currency_value(exact):
    converted = round(exact, 2)
    formatted = '{:0.2f}'.format(converted)
    major_units = int(converted)
    minor_units = round(100 * (exact - major_units))
    return formatted, major_units, minor_units
