#!/bin/sh
export DRONE_SECRETS=${DRONE_SECRETS:-'ansible_vault_password:j39jfkdldkx'}
export SECRET_PREFIX=${SECRET_PREFIX:-global_}

while :; do
  # Get token from database
  if [ ! -z "$SQLITE_ENABLED" ]; then
    SQLITE_DATABASE=/data/${SQLITE_DATABASE_NAME:-database.sql}
    ADMIN_TOKEN=$(echo "SELECT user_hash FROM users WHERE user_admin=1 LIMIT 1" | sqlite3 $SQLITE_DATABASE)
  fi

  # Add drone authentication
  export DRONE_SERVER=${DRONE_SERVER?Variable DRONE_SERVER is not defined}
  export DRONE_TOKEN=${DRONE_TOKEN:-$ADMIN_TOKEN}

  # Sync and get organizations
  orgs=$(drone repo sync | sed -r 's/(.*)\/.*/\1/g' | uniq)

  # Call sync script
  python3 /sync_secrets.py $orgs

  sleep ${SYNC_INTERVAL:-30}
done
