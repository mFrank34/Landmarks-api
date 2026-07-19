#!/bin/sh
set -e

DB_DIR=/data
DB_PATH="$DB_DIR/GeoLite2-City.mmdb"

mkdir -p "$DB_DIR"

if [ -z "$MAXMIND_LICENSE_KEY" ]; then
  echo "ERROR: MAXMIND_LICENSE_KEY environment variable is not set."
  echo "Get a free key at https://www.maxmind.com/en/geolite2/signup"
  exit 1
fi

if [ ! -f "$DB_PATH" ] || [ "$REFRESH_DB" = "true" ]; then
  echo "Downloading GeoLite2-City database..."
  curl -sSL "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=${MAXMIND_LICENSE_KEY}&suffix=tar.gz" -o /tmp/geolite2.tar.gz
  tar -xzf /tmp/geolite2.tar.gz -C /tmp
  find /tmp -name "GeoLite2-City.mmdb" -exec mv {} "$DB_PATH" \;
  rm -rf /tmp/GeoLite2-City_* /tmp/geolite2.tar.gz
  echo "Database ready at $DB_PATH"
else
  echo "Using existing database at $DB_PATH"
fi

exec gunicorn --bind 0.0.0.0:8080 --workers 2 app:app
