"""
Thumbsup web server
"""
import json
import logging
import os
import time
import uuid

from atomicwrites import atomic_write
from flask import Flask, redirect, request, render_template
from flaskext.markdown import Markdown

from .emojis import GITHUB_EMOJIS
from .summary import github_issue

app = Flask(__name__, static_url_path='/')
Markdown(app)

QUERIES_DIR = os.environ.get('THUMBSUP_QUERIES_DIR')

@app.route('/')
def index():
    return redirect('/index.html')

@app.route('/summary', methods=['POST'])
def summary():
    content_type = request.content_type
    if content_type != 'application/x-www-form-urlencoded':
        return (
            f'Invalid content type: {content_type}. '
            'Use "Content-Type: application/x-www-form-urlencoded"'
        ), 415

    url = request.form.get('url')
    if url is None or url == '':
        return redirect('/index.html')

    if QUERIES_DIR is not None:
        query_time = int(time.time())
        outfile = os.path.join(QUERIES_DIR, f'{query_time}-{uuid.uuid4()}.csv')
        logging.info(f'Writing URL={url} to file={outfile}')
        try:
            with atomic_write(outfile, overwrite=False) as ofp:
                print(f'{query_time},{url}', file=ofp)
        except Exception as err:
            logging.warning(f'Could not write URL={url} to QUERIES_DIR={QUERIES_DIR}')

    result = github_issue(url)
    issue = result['issue']
    comments = result['comments']

    return render_template(
        'results.html.jinja',
        url=url,
        issue=issue,
        comments=comments,
        emojis=GITHUB_EMOJIS,
    )
