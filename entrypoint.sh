#!/bin/sh
export DRONE_SECRETS=${DRONE_SECRETS:-''}
export SECRET_PREFIX=${SECRET_PREFIX:-global_}

while :; do
  # Ensure drone server is available
  export DRONE_SERVER=${DRONE_SERVER?Variable DRONE_SERVER is not defined}

  # Get token from database
  if [ ! -z "$SQLITE_ENABLED" ]; then
    SQLITE_DATABASE=/data/${SQLITE_DATABASE_NAME:-database.sqlite}

    # Export as droen token from database
    export DRONE_TOKEN=$(echo "SELECT user_hash FROM users WHERE user_admin=1 LIMIT 1" | sqlite3 $SQLITE_DATABASE)
  fi

  # Sync and get organizations
  orgs=$(drone repo sync | sed -r 's/(.*)\/.*/\1/g' | uniq)

  # Call sync script
  python3 /globalize.py $orgs

  sleep ${SYNC_INTERVAL:-30}
done
