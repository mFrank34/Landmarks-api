# Web Landmarks Geo Backend

A small, self-hostable hostname-to-location lookup service, built to power the
[Web Landmarks](../) browser extension's heatmap. Given a hostname, it resolves the IP
and returns an approximate geographic location using a local MaxMind GeoLite2 database.

This is the same service that runs at `geo.frankslab.uk` (the extension's default
backend). Running your own instance means visited hostnames never need to leave your
own infrastructure.

## Before you start: GeoLite2 licensing

This service requires MaxMind's **GeoLite2-City** database, which is free but requires
your own license key — it is **not included in this repo** and cannot be redistributed.

1. Create a free account at [maxmind.com/en/geolite2/signup](https://www.maxmind.com/en/geolite2/signup)
2. Generate a license key from your account dashboard
3. Download `GeoLite2-City.mmdb`, or use MaxMind's [`geoipupdate`](https://github.com/maxmind/geoipupdate)
   tool to keep it current automatically
4. Place the `.mmdb` file somewhere accessible to the container (see `docker-compose.yml`,
   which expects it at `./data/GeoLite2-City.mmdb`)

The database updates periodically — stale data isn't a security issue, just gradually
less accurate. Re-running `geoipupdate` occasionally (e.g. via cron) is enough.

## Running it

With Docker Compose:

```bash
mkdir -p data
# place GeoLite2-City.mmdb inside ./data
docker compose up -d
```

Without Docker:

```bash
pip install -r requirements.txt
export GEOIP_DB_PATH=/path/to/GeoLite2-City.mmdb
gunicorn --bind 0.0.0.0:8080 --workers 2 app:app
```

Check it's running:

```bash
curl http://localhost:8080/health
```

## Pointing the extension at your instance

In the Web Landmarks dashboard, go to **Settings → Geo API backend** and enter your
server's URL, e.g. `https://your-domain.example/json/`. The extension will prompt for
permission to reach that domain the first time you save it.

## API contract

The extension expects:

```
GET /json/<hostname>
```

**Success:**
```json
{
  "success": true,
  "hostname": "example.com",
  "ip": "93.184.216.34",
  "latitude": 42.1596,
  "longitude": -71.5931,
  "city": "Norwell",
  "country": "United States"
}
```

**Failure (hostname couldn't be resolved or located):**
```json
{ "success": false, "message": "Could not resolve hostname" }
```

The extension only reads `success`, `latitude`, and `longitude` — the other fields are
extras you can use for your own debugging/logging.

## Rate limiting

Since hostname resolution is publicly exposed, the service applies a basic per-IP rate
limit (60 requests/minute, 1000/day by default) via Flask-Limiter, to discourage use as
an open DNS-resolution oracle. Adjust the limits in `app.py` to fit your expected traffic.

## What this service logs

By default, Flask/gunicorn will log incoming requests (including the hostname being
looked up and the requester's IP) to stdout/your container logs, per normal HTTP server
behavior. If you're running this publicly, consider your own log retention policy and
disclose it if you're offering the service to others — the same transparency principle
the extension itself follows.
