#!/usr/bin/env python3

import argparse
import json
import math
import os
import re
import sys
from datetime import datetime, timedelta
from time import sleep, time

import requests

TOKEN_ENV_VAR = 'GITHUB_PAT_SAML_AUTHS_REPORT_TOKEN'
API_BASE = 'https://api.github.com'

def get_timestamp():
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d_%H-%M-%S')
    return now_str

def setup_parser():
    parser = argparse.ArgumentParser(description='Get SAML authorizations for PATs in one or multiple GitHub org(s)')
    parser.add_argument('-o', '--orgs', help='Specific GitHub org(s) to check repos in', nargs='*')
    parser.add_argument('-j', '--json', help='Output results to a json file', default=f'github_orgs_saml_auths_{get_timestamp()}.json')
    args = parser.parse_args()
    return args

def get_token():
    token = os.getenv(TOKEN_ENV_VAR)
    if not token:
        print(f"ERROR: Token not found in environment variable: {TOKEN_ENV_VAR}")
        sys.exit(1)
    if token.startswith('github_pat_'):
        print("This script requires a classic PAT with read:org scope but a fine-grained PAT was provided.")
        sys.exit(1)
    return token

def make_request(endpoint, token=get_token(), custom_headers=None, params=None):
    headers = {"Accept": "application/vnd.github+json",  "X-GitHub-Api-Version": "2022-11-28"}
    url = f'{API_BASE}{endpoint}'
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if custom_headers:
        headers.update(custom_headers)

    all_results = []
    while url:
        try:
            response = requests.get(url, headers=headers, params=params)
            while response.status_code == 403:
                # handle rate limit
                remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                if remaining == 0:
                        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                        sleep_time = max(reset_time - time(), 0)
                        now = datetime.now()
                        resume_time = now + timedelta(seconds=sleep_time)
                        print(f"Rate limit exceeded at {now.strftime('%Y-%m-%d %H:%M:%S')}, sleeping for {math.ceil(sleep_time / 60)} minutes until {resume_time.strftime('%Y-%m-%d %H:%M:%S')}. Hit Ctrl-C to exit.")
                        sleep(sleep_time)
                        response = requests.get(url, headers=headers)
            if response.status_code == 404:
                print(f'  API returned a 404. Check that the provided token has the correct scope and SAML authorization. Check also that the org exists and has SAML SSO configured.')
                return []
            else:
                response.raise_for_status()
            if isinstance(response.json(), dict):
                return response.json()
            # if response is a list, extend all_results with it and see if there's a next page
            all_results.extend(response.json())
            if 'next' in response.links:
                url = response.links['next']['url']
                current_page = re.match(r'.*page=(\d+)', url).group(1)
                last_page = re.match(r'.*page=(\d+)', response.links['last']['url']).group(1) if 'last' in response.links else current_page
                print(f'\r  {current_page}/{last_page} pages with max 100 SAML authorizations for PATs each in org parsed for checking...', end='')
            else:
                break
        except requests.exceptions.RequestException as e:
            print(f'Error occurred while making the request: {e}')
            sys.exit(1)
    #print(all_results)
    return all_results

def get_orgs():
    response = make_request('/user/orgs')
    orgs = [org['login'] for org in response]
    if not orgs:
        print("ERROR: No orgs found with provided token.")
        sys.exit(1)
    return orgs

def get_saml_authorizations(org):
    response = make_request(f'/orgs/{org}/credential-authorizations', params={'per_page': 100})
    pat_saml_authorizations = []
    for saml_authorization in response:
        if saml_authorization['credential_type'] == 'personal access token':
            pat_saml_authorizations.append(saml_authorization)
    return pat_saml_authorizations

def write_to_json(all_saml_authorizations, json_file):
    with open(json_file, 'w') as f:
        json.dump(all_saml_authorizations, f, indent=4)
    print(f'Wrote SAML authorizations for PATs to file: {json_file}')

def main():
    args = setup_parser()
    if args.orgs:
        orgs = args.orgs
    else:
        orgs = get_orgs()
    print(f'Checking repos in orgs: {", ".join(orgs)}\n')
    all_saml_authorizations = {}
    for org in orgs:
        print(f'Getting SAML authorizations for PATs in org: {org}')
        saml_authorizations = get_saml_authorizations(org)
        print(f'  Found {len(saml_authorizations)} SAML authorizations for PATs in org: {org}')
        if saml_authorizations:
            all_saml_authorizations[org] = saml_authorizations
        print()
    if all_saml_authorizations and args.json:
        write_to_json(all_saml_authorizations, args.json)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nKeyboard interrupt detected, exiting...')
        sys.exit(1)
