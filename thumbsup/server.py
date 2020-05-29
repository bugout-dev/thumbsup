"""
Thumbsup web server
"""
import json

from flask import Flask, redirect, request, render_template
from flaskext.markdown import Markdown

from .emojis import GITHUB_EMOJIS
from .summary import github_issue

app = Flask(__name__, static_url_path='/')
Markdown(app)

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

    results = github_issue(url)

    return render_template('results.html.jinja', url=url, results=results, emojis=GITHUB_EMOJIS)
