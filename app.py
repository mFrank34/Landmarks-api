import os
import re
import socket

from flask import Flask, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import geoip2.database
import geoip2.errors

app = Flask(__name__)

DB_PATH = os.environ.get("GEOIP_DB_PATH", "/data/GeoLite2-City.mmdb")
reader = geoip2.database.Reader(DB_PATH)

# Basic rate limiting, since this is a publicly reachable lookup endpoint.
# Adjust the limits to taste — these are conservative defaults.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["60 per minute", "1000 per day"],
)

# Loose hostname validation — not a full RFC 1035 parser, just enough to
# reject obviously-malformed input before we hand it to gethostbyname().
HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$"
)


@app.after_request
def add_cors_headers(response):
    # Not strictly required for the extension (host_permissions covers that),
    # but harmless and useful if you ever call this from a regular webpage too.
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.route("/json/<hostname>")
def geolocate(hostname):
    if not HOSTNAME_RE.match(hostname):
        return jsonify({"success": False, "message": "Invalid hostname"}), 200

    try:
        ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        return jsonify({"success": False, "message": "Could not resolve hostname"}), 200

    try:
        result = reader.city(ip)
    except geoip2.errors.AddressNotFoundError:
        return jsonify({"success": False, "message": "Address not found in database"}), 200

    return jsonify({
        "success": True,
        "hostname": hostname,
        "ip": ip,
        "latitude": result.location.latitude,
        "longitude": result.location.longitude,
        "city": result.city.name,
        "country": result.country.name,
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
