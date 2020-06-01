"""
Thumbsup summaries
"""
import os
import re
from typing import Any, Dict, List
from urllib.parse import urlsplit

import requests

from . access import UNAUTHENTICATED

class SummaryError(Exception):
    pass

class RateLimitError(Exception):
    pass

RE_GITHUB_ISSUE_EXTRACTOR = re.compile('github.com/([^/]+)/([^/]+)/issues/(\d+)')
GITHUB_ACCEPT_HEADER = (
    "application/vnd.github.v3+json, application/vnd.github.squirrel-girl-preview"
)
GITHUB_RATE_LIMIT_URL = 'https://api.github.com/rate_limit'

RE_STACKOVERFLOW_QUESTION_EXTRACTOR = re.compile('stackoverflow.com/questions/(\d+)/')
STACKEXCHANGE_API_PREFIX = 'https://api.stackexchange.com/2.2/'

def github_num_reactions(comment_object: Dict[str, Any]) -> int:
    """
    Returns the number of reactions in an issue comment.
    """
    return comment_object.get('reactions', {}).get('total_count', 0)

def github_num_positive_reactions(comment_object: Dict[str, Any]) -> int:
    """
    Returns the number of positive reactions in an issue comment.
    """
    num_positive_reactions = 0
    positive_emojis = {'+1', 'laugh', 'hooray', 'heart', 'rocket', 'eyes'}
    reactions = comment_object.get('reactions', {})
    for emoji in positive_emojis:
        num_positive_reactions += reactions.get(emoji, 0)
    return num_positive_reactions

def github_issue(issue_url: str, check_rate_limit: bool = True) -> Dict[str, Any]:
    """
    Summarizes a GitHub issue.

    The current implementation simply sorts the comments on the issue by the number of emoji
    reactions.

    Returns a dictionary of the form
    {
        "issue": <issue object>,
        "comments": <list of comment objects>
    }

    Issues follow the GitHub API schema for that object:
    https://developer.github.com/v3/issues/#response-4

    Comments follow the GitHub API schema for that object:
    https://developer.github.com/v3/issues/comments/#list-comments-on-an-issue

    The individual issue and comment objects include the "reactions" key.
    """
    user_agent = os.environ.get('THUMBSUP_USER_AGENT', 'thumbsup')
    headers = {
        'Accept': GITHUB_ACCEPT_HEADER,
        'User-Agent': user_agent,
    }
    github_token_file = os.environ.get('THUMBSUP_GITHUB_TOKEN_FILE')
    if github_token_file is not None:
        with open(github_token_file, 'r') as ifp:
            github_token = ifp.read().strip()
        if github_token != UNAUTHENTICATED and github_token != '':
            headers['Authorization'] = f'token {github_token}'

    if check_rate_limit:
        r = requests.get(GITHUB_RATE_LIMIT_URL, headers=headers)
        rate_limit_response = r.json()
        remaining_rate_limit = (
            rate_limit_response.get('resources', {}).get('core', {}).get('remaining', 0)
        )
        rate_limit_bound = os.environ.get('THUMBSUP_RATE_LIMIT_BOUND', '10')
        rate_limit_bound = int(rate_limit_bound)
        if remaining_rate_limit < rate_limit_bound:
            raise RateLimitError(f'Remaining GitHub rate limit too low: {remaining_rate_limit}')

    match = RE_GITHUB_ISSUE_EXTRACTOR.search(issue_url)
    if not match:
        raise SummaryError(f'URL does not match form of link to GitHub Issue: {issue_url}')

    owner, repo, issue_number = match.groups()

    issue_url = f'https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}'
    r = requests.get(issue_url, headers=headers)
    issue_response = r.json()

    comments_url = f'{issue_url}/comments'
    r = requests.get(comments_url, headers=headers)
    comment_response = r.json()
    comment_response.sort(
        key=lambda c: github_num_reactions(c) + github_num_positive_reactions(c),
        reverse=True
    )
    return {'issue': issue_response, 'comments': comment_response}

def stackoverflow_question(question_url: str, check_rate_limit: bool = True) -> Dict[str, Any]:
    """
    Summarizes a Stack Overflow question.

    The current implementation checks if there is an accepted answer to the question. If there is,
    it returns the question with the accepted answer. Otherwise, it returns the question with
    an empty answer object.

    Returns a dictionary of the form
    {
        "question": <question object>,
        "accepted_answer": <None or answer object>
    }

    Question objects follow the Stack Exchange API schema:
    https://api.stackexchange.com/docs/types/question

    Answer objects follow the Stack Exchange API schema:
    https://api.stackexchange.com/docs/types/answer
    """
    stackexchange_request_key = os.environ.get('THUMBSUP_STACKEXCHANGE_REQUEST_KEY')
    if stackexchange_request_key is None:
        raise SummaryError('THUMBSUP_STACKEXCHANGE_REQUEST_KEY environment variable not set')

    stackexchange_access_token = os.environ.get('THUMBSUP_STACKEXCHANGE_ACCESS_TOKEN')
    if stackexchange_request_key is None:
        raise SummaryError('THUMBSUP_STACKEXCHANGE_ACCESS_TOKEN environment variable not set')

    stackoverflow_request_params: Dict[str, str] = {
        'site': 'stackoverflow',
        'filter': 'withBody',
        'key': stackexchange_request_key,
        'access_token': stackexchange_access_token,
    }

    match = RE_STACKOVERFLOW_QUESTION_EXTRACTOR.search(question_url)
    question_id = match.group(1)

    question_api_url = f'{STACKEXCHANGE_API_PREFIX}questions/{question_id}'
    r = requests.get(question_api_url, params=stackoverflow_request_params)
    question_response = r.json()
    question_items = question_response.get('items', [])
    if not question_items:
        raise SummaryError(f'No Stack Overflow question with id {question_id}')
    question = question_items[0]
    accepted_answer_id = question.get('accepted_answer_id')
    if accepted_answer_id is None:
        return {'question': question, 'accepted_answer': None}

    if check_rate_limit:
        remaining_rate_limit = question_response.get('quota_remaining', 0)
        rate_limit_bound = os.environ.get('THUMBSUP_STACKEXCHANGE_RATE_LIMIT_BOUND', '100')
        rate_limit_bound = int(rate_limit_bound)
        if remaining_rate_limit < rate_limit_bound:
            raise RateLimitError(
                f'Remaining Stack Exchange rate limit too low: {remaining_rate_limit}'
            )
    accepted_answer_api_url = f'{STACKEXCHANGE_API_PREFIX}answers/{accepted_answer_id}'
    r = requests.get(accepted_answer_api_url, params=stackoverflow_request_params)
    accepted_answer_response = r.json()
    answer_items = accepted_answer_response.get('items', [])
    if not answer_items:
        raise SummaryError(f'No Stack Overflow answer with id {accepted_answer_id}')
    accepted_answer = answer_items[0]
    return {'question': question, 'accepted_answer': accepted_answer}

def summarize(url: str, check_rate_limit: bool = True) -> Dict[str, Any]:
    """
    Top-level summarizer - selects one of the domain-specific summarizers defined in this module and
    returns that summarizer's summary.
    """
    split_url = urlsplit(url)
    if 'github.com' in split_url.hostname:
        return github_issue(url, check_rate_limit)
    elif 'stackoverflow.com' in split_url.hostname:
        return stackoverflow_question(url, check_rate_limit)

    return {}

if __name__ == '__main__':
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Thumbsup Summaries')
    parser.add_argument(
        '--summary_type',
        '-t',
        choices={'github', 'stackoverflow'},
        default=None,
        help='Specific summary type (default: selects automatically)'
    )
    parser.add_argument('url', help='URL to summarize')
    args = parser.parse_args()
    if args.summary_type is None:
        summary = summarize(args.url)
    elif args.summary_type == 'github':
        summary = github_issue(args.url)
    else:
        summary = stackoverflow_question(args.url)
    print(json.dumps(summary))
