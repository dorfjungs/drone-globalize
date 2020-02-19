import sys
import os
import subprocess

VALUE_SEPARATOR = ':'
SECRET_SEPARATOR = ','
SECRET_PREFIX = os.getenv('SECRET_PREFIX')
SECRET_STRING = os.getenv('DRONE_SECRETS')
DB_SECRET_DIFF_CHECK = int(os.getenv('DB_SECRET_DIFF_CHECK', 0))
SQLITE_DATABASE_PATH = os.getenv('SQLITE_DATABASE_PATH')
SQLITE_ENABLED = os.path.isfile(SQLITE_DATABASE_PATH)

def log_line(message):
  print('[drone/globalize] ' + message)


def create_secret(name, data = '', pull_request = 0, pull_request_push = 0):
  return {
    'name': name,
    'data': data,
    'pull_request': pull_request,
    'pull_request_push': pull_request_push
  }


def parse_secrets():
  secrets = []
  secret_splitted = [
    string for string in SECRET_STRING.split(SECRET_SEPARATOR) if string != ""
  ]

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

def update_secret_state_sqlite(orgs, secrets, state):
  table = 'orgsecrets'
  columns = [
    'secret_namespace',
    'secret_name',
    'secret_data',
    'secret_pull_request',
    'secret_pull_request_push'
  ]

  sqlite_proc = subprocess.run(
    [ 'sqlite3', '-separator', VALUE_SEPARATOR, '-readonly', SQLITE_DATABASE_PATH ],
    input='SELECT ' + (','.join(columns)) + ' FROM ' + table,
    encoding='ascii',
    stdout=subprocess.PIPE
  )

  org_secrets = sqlite_proc.stdout.splitlines()

  # Detect updates and additions
  for org in orgs:
    for secret in secrets:
      secret_item = { 'org': org, 'secret': secret }
      secret_str = VALUE_SEPARATOR.join([ org, secret['name'] ])
      secret_exists = False

      # Check if secret needs and update
      for org_secret in org_secrets:
        if org_secret.startswith(secret_str) == True:
          secret_exists = True
          secret_str_detail = VALUE_SEPARATOR.join([
            org,
            secret['name'],
            secret['data'],
            str(secret['pull_request']),
            str(secret['pull_request_push'])
          ])

          if secret_str_detail != org_secret:
            state['update'].append(secret_item)

          break

      if secret_exists == False:
        state['add'].append(secret_item)

  return org_secrets


def update_secret_state_cli(orgs, secrets, state):
  process = subprocess.run(
    [
      'drone',
      'orgsecret',
      'ls',
      '--format={{ .Namespace }}' + VALUE_SEPARATOR + '{{ .Name }}'
    ],
    stdout=subprocess.PIPE,
    encoding='ascii'
  )

  org_secrets = process.stdout.splitlines()

  # Detect updates and additions
  for org in orgs:
    for secret in secrets:
      org_secret_item = org + ':' + secret['name']
      secret_item = { 'org': org, 'secret': secret }

      if org_secret_item in org_secrets:
        state['update'].append(secret_item)

      if org_secret_item not in org_secrets:
        state['add'].append(secret_item)

  return org_secrets


def get_secret_state(orgs, secrets):
  state = { 'add': [], 'update': [], 'rm': [] }

  if SQLITE_ENABLED == True and DB_SECRET_DIFF_CHECK == 1:
    org_secrets = update_secret_state_sqlite(orgs, secrets, state)
  else:
    org_secrets = update_secret_state_cli(orgs, secrets, state)

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
        state['rm'].append({
          'org': org_secret_namespace,
          'secret': create_secret(org_secret_name)
        })

  return state


def drone_secret_action(action, org, secret):
  cmd = [ 'drone', 'orgsecret', action, org, secret['name'] ]

  if action != 'rm':
    cmd.append(secret['data'])
    cmd.append('--allow-pull-request=' + str(secret['pull_request']))
    cmd.append('--allow-push-on-pull-request=' + str(secret['pull_request_push']))

  subprocess.run(cmd, stdout=subprocess.DEVNULL)


def apply_secret_state(state, action, message = ''):
  for item in state[action]:
    secret = item['secret']
    org = item['org']

    log_line(message.format(secret['name'], org))
    drone_secret_action(action, org, secret)


def state_is_empty(state):
  addCount = len(state['add'])
  updateCount = len(state['update'])
  rmCount = len(state['rm'])

  return addCount == 0 and updateCount == 0 and rmCount == 0


def main():
  state = get_secret_state(sys.argv[1:], parse_secrets())

  if state_is_empty(state):
    log_line('No changes detected!')
  else:
    apply_secret_state(state, 'add', 'Add secret "{0}" to "{1}"')
    apply_secret_state(state, 'update', 'Update secret "{0}" in "{1}"')
    apply_secret_state(state, 'rm', 'Remove secret "{0}" from "{1}"')


if __name__ == "__main__":
  main()
