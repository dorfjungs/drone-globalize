#!/bin/sh
export DRONE_SECRETS=${DRONE_SECRETS:-''}
export SECRET_PREFIX=${SECRET_PREFIX:-global_}
export SQLITE_DATABASE_NAME=${SQLITE_DATABASE_NAME:-database.sqlite}
export SQLITE_DATABASE_PATH=/data/$SQLITE_DATABASE_NAME
export DRONE_SERVER=${DRONE_SERVER?Variable DRONE_SERVER is not defined}

# Get token from database and export it
if [[ -f "$SQLITE_DATABASE_PATH" ]]; then
  query="SELECT user_hash FROM users WHERE user_login='$DRONE_USER' LIMIT 1;"
  token=$(echo "$query" | sqlite3 -readonly $SQLITE_DATABASE_PATH)

  export DRONE_TOKEN=$token
fi

while :; do
  # Sync and get organizations
  orgs=$(drone repo sync | sed -r 's/(.*)\/.*/\1/g' | uniq)

  # Call sync script
  python3 /globalize.py $orgs

  sleep ${SYNC_SLEEP_TIME:-30}
done
