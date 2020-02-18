# Drone global secrets
This syncs and distributes secrets among all organizations with the drone database via drone-cli.
The feature of global secrets seems unnecessary to the most ci/cd systems, so here's the "bruteforce way".

## Usage
```yml
backup:
  image: dorfjungs/drone-globalize:v1.0
  environment:
    # The secrets you want to sync with all available organizations
    #
    # ------------------------------------------------------------------
    # | Name      | Value        | Pull requests  | Pull requests push |
    # ------------------------------------------------------------------
    # | my_secret | random_value | 0              | 1                  |
    # ------------------------------------------------------------------
    #
    # Value separator = ":"
    # Secret separator = ","
    #
    DRONE_SECRETS: secret1:843hnx8h4mw,secret2:sadksajdasd:0:1

    # The endpoint of the drone instance
    DRONE_SERVER: drone.company.io

    # Optional
    # If DB (sqlite) is disabled you need to set the token manually
    # This has to be an admin token
    DRONE_TOKEN: '************'

    # Optional, Default = global_
    # A fprefix attached to each secret name.
    # Since we want to achieve a sync without modifying existing
    # secrets, we need a "namespace" to put all the secrets into
    SECRET_PREFIX: custom_prefix_

    # Optional, Default = false
    # This enables the automatic admin token
    # retrieval from the database
    SQLITE_ENABLED: true

    # Optional, Default = database.sql
    # Sets the database file name inside the
    # mounted volume
    SQLITE_DATABASE_NAME: custom_db_name.sqlite

    # Optional, Default = false
    # Since the cli can't output the current secret data
    # we need direct access to the database in order to compare the new data
    # with the old data. If this is disabled all active secrets will be updated
    # on each cycle to ensure that the correct data will be used
    DB_SECRET_DIFF_CHECK: true

    # Optional, Default = 30
    SYNC_TIME: 60 # Seconds
  volumes:
    # Optional
    # If yo're using `SQLITE_ENABLED` you should also mount the database here
    # Read-Only is sufficient
    - drone-data:/data:ro
```