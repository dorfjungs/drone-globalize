import sys
import os
import subprocess

SECRET_PREFIX = os.getenv('SECRET_PREFIX')
SECRET_STRING = os.getenv('DRONE_SECRETS')
DB_SECRET_DIFF_CHECK = int(os.getenv('DB_SECRET_DIFF_CHECK', 0))
SQLITE_ENABLED = int(os.getenv('SQLITE_ENABLED', 0))

def create_secret(name, data = '', pull_request = 0, pull_request_push = 0):
    return {
        'name': name,
        'data': data,
        'pull_request': pull_request,
        'pull_request_push': pull_request_push
    }

def parse_secrets():
    secrets = []
    secret_splitted = [ string for string in SECRET_STRING.split(',') if string != "" ]

    if len(secret_splitted) > 0:
        for secret in secret_splitted:
            parts = secret.split(':')

            secrets.append(create_secret(
                SECRET_PREFIX + parts[0],
                parts[1],
                parts[2] if len(parts) > 2 else 0,
                parts[3] if len(parts) > 3 else 0
            ))

    return secrets

def get_secret_state(orgs, secrets):
    state = {
        'add': [],
        'update': [],
        'remove': []
    }

    process = subprocess.run(
        [ 'drone', 'orgsecret', 'ls', '--format={{ .Namespace }}:{{ .Name }}' ],
        stdout=subprocess.PIPE
    )

    # if SQLITE_ENABLED == 1:
    #     if DB_SECRET_DIFF_CHECK:
    #         @todo: get secrets from database

    org_secrets = str(process.stdout, 'utf8').splitlines()

    # Detect updates and additions
    for org in orgs:
        for secret in secrets:
            org_secret_item = org + ':' + secret['name']
            secret_item = { 'org': org, 'secret': secret }

            if org_secret_item in org_secrets:
                state['update'].append(secret_item)

            if org_secret_item not in org_secrets:
                state['add'].append(secret_item)

    # Detect deletetions
    for org_secret in org_secrets:
        org_secret_namespace = org_secret.split(':')[0]
        org_secret_name = org_secret.split(':')[1]

        if org_secret_name.startswith(SECRET_PREFIX):
            mark_as_removed = True

            for secret in secrets:
                if secret['name'] == org_secret_name:
                    mark_as_removed = False
                    break

            if (mark_as_removed):
                state['remove'].append({
                    'org': org_secret_namespace,
                    'secret': create_secret(org_secret_name)
                })

    return state

def drone_secret_action(
    action,
    org,
    name,
    data = '',
    pull_request = 0,
    pull_request_push = 0
):
    cmd = [
        'drone',
        'orgsecret',
        action,
        org,
        name
    ]

    if action != 'rm':
        cmd.append(data)
        cmd.append('--allow-pull-request=' + str(pull_request))
        cmd.append( '--allow-push-on-pull-request=' + str(pull_request_push))

    subprocess.run(cmd, stdout=subprocess.DEVNULL)

def main():
    orgs = sys.argv[1:]
    secrets = parse_secrets()
    state = get_secret_state(orgs, secrets)

    if (len(state['add']) == 0 and
        len(state['remove']) == 0 and
        len(state['update']) == 0):
            print('[drone/globalize] No changes detected. Looks good!')

    # Add secrets
    for item in state['add']:
        secret = item['secret']

        print('[drone/globalize] add secret "' + secret['name'] + '" to "' + item['org'] + '"')

        drone_secret_action(
            'add',
            item['org'],
            secret['name'],
            secret['data'],
            secret['pull_request'],
            secret['pull_request_push']
        )

    # Update secrets
    for item in state['update']:
        secret = item['secret']

        print('[drone/globalize] update secret "' + secret['name'] + '" in "' + item['org'] + '"')

        drone_secret_action(
            'update',
            item['org'],
            secret['name'],
            secret['data'],
            secret['pull_request'],
            secret['pull_request_push']
        )

    # Remove secrets
    for item in state['remove']:
        secret = item['secret']

        print('[drone/globalize] remove secret "' + secret['name'] + '" from "' + item['org'] + '"')

        drone_secret_action('rm', item['org'], secret['name'])


if __name__ == "__main__":
    main()
