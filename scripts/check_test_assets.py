"""Check the isolated Compose instance using its demo administrator."""

import http.cookiejar
import json
import re
import sys
import time
import urllib.request

HOST = "http://127.0.0.1:18119"
DATABASE = sys.argv[1]
client = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
)


def fetch(path):
    with client.open(HOST + path, timeout=25) as response:
        return response.read()


def check_assets(html, stylesheet):
    paths = set(re.findall(rb'(?:href|src)="(/web/assets/[^"]+)"', html))
    assert any(path.endswith(stylesheet) for path in paths), stylesheet
    for path in sorted(paths):
        content = fetch(path.decode())
        assert content and b"CSS error message" not in content, path
        if path.endswith(b"web.assets_backend.min.css"):
            assert b".ba-editor-card" in content, path


login_path = f"/web/login?db={DATABASE}"
for attempt in range(30):
    try:
        html = fetch(login_path)
        break
    except OSError:
        if attempt == 29:
            raise
        time.sleep(2)

check_assets(html, b"web.assets_frontend.min.css")
payload = {"jsonrpc": "2.0", "params": {"db": DATABASE, "login": "admin", "password": "admin"}}
request = urllib.request.Request(
    HOST + "/web/session/authenticate",
    json.dumps(payload).encode(),
    {"Content-Type": "application/json"},
)
with client.open(request, timeout=25) as response:
    result = json.load(response)["result"]
assert result["db"] == DATABASE and result["is_system"]
check_assets(fetch("/web?debug=0"), b"web.assets_backend.min.css")
print("Login and backend assets loaded successfully.")
