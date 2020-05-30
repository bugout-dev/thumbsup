"""
Access token manager for Thumbsup
"""
import os
import sys
import time
from typing import Optional

from atomicwrites import atomic_write
import jwt
import requests

UNAUTHENTICATED = "UNAUTHENTICATED"

def github(access_file: str) -> str:
    """
    Generates a GitHub access token and writes it to the given access_file path.

    Token is generated as follows:
    1. Check if the THUMBSUP_GITHUB_TOKEN environment variable is set. If it is, write that token
       to the access_file. (This allows for the use of personal access tokens.)
       DONE
    2. Check if the THUMBSUP_GITHUB_APP_KEYFILE and THUMBSUP_GITHUB_APP_ID environment variables are
       set. If they are, generate a JWT for the app.
    3. Use the THUMBSUP_GITHUB_APP_INSTALLATION_ID environment variable to identify the access token
       endpoint for the installation we want to generate a token for.
    4. POST to the installation endpoint with the JWT and the right Accept header.
    5. Extract the "token" key from the response and write it to the access_file.
       DONE

    Returns the method by which the access token was generated. The possible return values are:
    'personal', 'app', UNAUTHENTICATED
    """
    github_token: Optional[str] = os.environ.get('THUMBSUP_GITHUB_TOKEN')
    method = 'personal'
    if github_token is None:
        keyfile = os.environ.get('THUMBSUP_GITHUB_APP_KEYFILE')
        app_id = os.environ.get('THUMBSUP_GITHUB_APP_ID')
        installation_id = os.environ.get('THUMBSUP_GITHUB_APP_INSTALLATION_ID')
        if keyfile is not None and installation_id is not None:
            method = 'app'
            current_time = int(time.time())
            payload = {
                'iat': current_time,
                'exp': current_time + 600,
                'iss': app_id,
            }
            with open(keyfile) as ifp:
                secret = ifp.read()
            jwt_token = jwt.encode(payload, secret, algorithm='RS256')
            access_token_url = (
                f'https://api.github.com/app/installations/{installation_id}/access_tokens'
            )
            headers = {
                'Accept': 'application/vnd.github.machine-man-preview+json',
                'Authorization': f'Bearer {jwt_token.decode()}',
            }
            try:
                r = requests.post(access_token_url, headers=headers)
                response_body = r.json()
                github_token = response_body.get('token')
            except Exception as err:
                print('Warning: Error retrieving GitHub Installation access token')
                print(f'Access token URL: {access_token_url}')
                print(f'JWT: {jwt_token.decode()}')
                print(f'Error: {repr(err)}')

    if github_token is None:
        method = UNAUTHENTICATED
        github_token = UNAUTHENTICATED

    with atomic_write(access_file, overwrite=True) as ofp:
        ofp.write(github_token)

    return method

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Thumbsup token generator')
    parser.add_argument(
        'service',
        choices={'github'},
        help='Specifies the service for which to generate an access token'
    )
    parser.add_argument(
        'access_file',
        help='Path at which to store token'
    )
    args = parser.parse_args()

    if args.service == 'github':
        method = github(args.access_file)

    print(f'Token stored at {args.access_file} for service={args.service} using method={method}')
