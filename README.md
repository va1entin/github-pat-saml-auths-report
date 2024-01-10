# github-pat-saml-auths-report

This Python script checks all or selected orgs that you have access to for *classic* PATs with [SAML authorization](https://docs.github.com/en/enterprise-cloud@latest/rest/orgs/orgs?apiVersion=2022-11-28#list-saml-sso-authorizations-for-an-organization) in them and generates a JSON report with such tokens sorted by org.
It does **not** include fine-grained tokens. There is a separate [API endpoint](https://docs.github.com/en/rest/orgs/personal-access-tokens?apiVersion=2022-11-28#list-fine-grained-personal-access-tokens-with-access-to-organization-resources) and [UI](https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/reviewing-and-revoking-personal-access-tokens-in-your-organization#reviewing-and-revoking--fine-grained-personal-access-tokens) for those.

## Requirements

- Python 3
- `requests` library (install with `pip install requests`)

## Usage

1. Create a [**classic** GitHub personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic) with `read:org` scope and SAML authorize it to orgs that you want to check.

2. Run the script with the following command:

```bash
export GITHUB_PAT_SAML_AUTHS_REPORT_TOKEN="<your token>"

# Get classic PATs with SAML authorization from all orgs that the token can access
python3 github-pat-saml-auths-report.py
# OR
# Check specific org(s)
python3 github-pat-saml-auths-report.py -o org1 org2 org3

# OPTIONAL, get only classic PATs with SAML authorization in org2 from report
cat github_orgs_saml_auths_YYYY-MM-DD_HH-MM-SS.json | jq '.org2'
```

### Options

- `-o` or `--orgs`: List of GitHub organizations to check. If not specified, all organizations that the token can access will be checked.
- `-j` or `--json`: Filename for JSON report. Default: `github_orgs_saml_auths_YYYY-MM-DD_HH-MM-SS.json`

### Environment variables
- `GITHUB_PAT_SAML_AUTHS_REPORT_TOKEN`: GitHub personal access token with `read:org` scope
