"""
Thumbsup summaries
"""
import os
import re
from typing import Any, Dict, List

import requests

class SummaryError(Exception):
    pass

class RateLimitError(Exception):
    pass

RE_GITHUB_ISSUE_EXTRACTOR = re.compile('github.com/(\w+)/(\w+)/issues/(\d+)')
GITHUB_ACCEPT_HEADER = (
    "application/vnd.github.v3+json, application/vnd.github.squirrel-girl-preview"
)
GITHUB_RATE_LIMIT_URL = 'https://api.github.com/rate_limit'

def num_reactions(comment_object: Dict[str, Any]) -> int:
    """
    Returns the number of reactions in an issue comment.
    """
    return comment_object.get('reactions', {}).get('total_count', 0)

def num_positive_reactions(comment_object: Dict[str, Any]) -> int:
    """
    Returns the number of positive reactions in an issue comment.
    """
    num_positive_reactions = 0
    positive_emojis = {'+1', 'laugh', 'hooray', 'heart', 'rocket', 'eyes'}
    reactions = comment_object.get('reactions', {})
    for emoji in positive_emojis:
        num_positive_reactions += reactions.get(emoji, 0)
    return num_positive_reactions

def github_issue(issue_url: str, check_rate_limit: bool = True) -> List[Dict[str, Any]]:
    """
    Summarizes a GitHub issue.

    The current implementation simply sorts the comments on the issue by the number of emoji
    reactions.

    Returns a list of comments following the GitHub API schema for that object:
    https://developer.github.com/v3/issues/comments/#list-comments-on-an-issue

    The individual comment objects include the "reactions" key.
    """
    user_agent = os.environ.get('THUMBSUP_USER_AGENT', 'thumbsup')
    headers = {
        'Accept': GITHUB_ACCEPT_HEADER,
        'User-Agent': user_agent,
    }
    github_token = os.environ.get('THUMBSUP_GITHUB_TOKEN')
    if github_token is not None and github_token != '':
        headers['Authorization'] = f'token {github_token}'

    if check_rate_limit:
        r = requests.get(GITHUB_RATE_LIMIT_URL, headers=headers)
        rate_limit_response = r.json()
        remaining_rate_limit = (
            rate_limit_response.get('resources', {}).get('core', {}).get('remaining', 0)
        )
        # TODO(neeraj): For now, magic number 10 is good enough. In future, this could become an
        # environment variable but no need for such complications now.
        if remaining_rate_limit < 10:
            raise RateLimitError(f'Remaining GitHub rate limit too low: {remaining_rate_limit}')

    match = RE_GITHUB_ISSUE_EXTRACTOR.search(issue_url)
    if not match:
        raise SummaryError(f'URL does not match form of link to GitHub Issue: {issue_url}')

    owner, repo, issue_number = match.groups()

    comments_url = f'https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments'
    r = requests.get(comments_url, headers=headers)
    response = r.json()
    summary = [
        comment for comment in response if num_reactions(comment) > 0
    ]
    summary.sort(key=lambda c: num_reactions(c) + num_positive_reactions(c), reverse=True)
    return summary

if __name__ == '__main__':
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Thumbsup Summaries')
    parser.add_argument('url', help='URL to summarize')
    args = parser.parse_args()
    summary = github_issue(args.url)
    print(json.dumps(summary))
