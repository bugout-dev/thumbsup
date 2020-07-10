"""
Thumbsup web server
"""
import json
import logging
import os
import time
from urllib.parse import unquote
import uuid

from atomicwrites import atomic_write
from flask import Flask, redirect, request, render_template
from flaskext.markdown import Markdown
from flask_cors import CORS

from .summary import summarize

app = Flask(__name__, static_url_path='/')
Markdown(app)
CORS(app)

QUERIES_DIR = os.environ.get('THUMBSUP_QUERIES_DIR')

@app.route('/')
def index():
    return redirect('/index.html')

@app.route('/summary', methods=['GET', 'POST'])
def summary():
    response_format = 'html'

    # For POST requests, get form fields. For GET requests, get query parameters.
    if request.method == 'POST':
        content_type = request.content_type
        if content_type != 'application/x-www-form-urlencoded':
            return (
                f'Invalid content type: {content_type}. '
                'Use "Content-Type: application/x-www-form-urlencoded"'
            ), 415

        url = request.form.get('url')
        if url is None or url == '':
            return redirect('/index.html')

        response_format = request.form.get('format', 'html')
    else:
        url_raw = request.args.get('url')
        response_format = request.args.get('format', 'html')
        url = unquote(url_raw)

    if response_format not in {'html', 'json'}:
        return (f'Invalid response format: {response_format}. Valid formats: html, json', 400)

    if QUERIES_DIR is not None:
        query_time = int(time.time())
        outfile = os.path.join(QUERIES_DIR, f'{query_time}-{uuid.uuid4()}.csv')
        logging.info(f'Writing URL={url} to file={outfile}')
        try:
            with atomic_write(outfile, overwrite=False) as ofp:
                print(f'{query_time},{url}', file=ofp)
        except Exception as err:
            logging.warning(f'Could not write URL={url} to QUERIES_DIR={QUERIES_DIR}')

    summary = summarize(url)

    response = {'url': url, 'summary': summary}

    if response_format == 'html':
        response = render_template('results.html.jinja', **response)

    return response
