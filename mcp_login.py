"""
mcp_login.py - the sign-in plumbing for 03.   OPTIONAL READING.

When an MCP server needs you to log in, the client does the standard OAuth dance:
  1. the server answers "401, log in at this address"
  2. the client opens your BROWSER so YOU sign in and click Allow (the app never sees your password)
  3. the browser sends a one-time code back to a tiny web page on your own computer (below)
  4. the client swaps the code for a token and uses that token from then on

Real tools like Antigravity do all of this for you. We write it out once so you can see it.
Your login is remembered in a file called .mcp_login.json next to this script (delete it to sign out).
"""

import asyncio
import json
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from mcp.client.auth import OAuthClientProvider
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken

PORT = 8765
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".mcp_login.json")


def stop_with(message):
    """Show one clear message and stop, instead of a page of technical errors."""
    print("\n" + message + "\n")
    os._exit(1)


class SavedLogin:
    """Remembers who we are and our token in a small file, so you only sign in once."""

    def __init__(self, server_url):
        self.server_url = server_url

    def read_everything(self):
        if not os.path.exists(SAVE_FILE):
            return {}
        with open(SAVE_FILE, encoding="utf-8") as file:
            return json.load(file)

    def read_item(self, name):
        everything = self.read_everything()
        if self.server_url not in everything:
            return None
        return everything[self.server_url].get(name)

    def write_item(self, name, value):
        everything = self.read_everything()
        if self.server_url not in everything:
            everything[self.server_url] = {}
        everything[self.server_url][name] = value
        with open(SAVE_FILE, "w", encoding="utf-8") as file:
            json.dump(everything, file)

    async def get_tokens(self):
        saved = self.read_item("tokens")
        if saved is None:
            return None
        return OAuthToken.model_validate(saved)

    async def set_tokens(self, tokens):
        self.write_item("tokens", tokens.model_dump(mode="json"))

    async def get_client_info(self):
        saved = self.read_item("client")
        if saved is None:
            return None
        return OAuthClientInformationFull.model_validate(saved)

    async def set_client_info(self, info):
        self.write_item("client", info.model_dump(mode="json"))


class OnlyOneServer(HTTPServer):
    allow_reuse_address = False  # if the port is already taken, fail loudly instead of sharing it


# Every sign-in link carries a secret "state" value. We remember the newest one, so that a click on
# an OLD browser tab from an earlier run is ignored instead of breaking the current sign-in.
newest_link = {"state": ""}


async def open_browser(url):
    query = parse_qs(urlparse(url).query)
    newest_link["state"] = query["state"][0]
    print("\nOpening your browser so you can sign in and click Allow.")
    print("If it does not open, paste this link into your browser:\n" + url + "\n")
    webbrowser.open(url)


async def wait_for_code():
    """A tiny web page on your own computer that catches the code the browser sends back."""
    got = {"code": "", "state": None, "error": ""}
    done = threading.Event()

    class Page(BaseHTTPRequestHandler):
        def do_GET(self):
            query = parse_qs(urlparse(self.path).query)
            state = ""
            if "state" in query:
                state = query["state"][0]

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            if state != newest_link["state"]:
                # A click from an old browser tab. Ignore it and keep waiting for the newest one.
                self.wfile.write(b"<h2>This sign-in link is out of date. Please use the newest browser tab.</h2>")
                return

            if "code" in query:
                got["code"] = query["code"][0]
            got["state"] = state
            if "error" in query:
                got["error"] = query["error"][0]
            self.wfile.write(b"<h2>Done. You can close this tab and go back to your terminal.</h2>")
            done.set()

        def log_message(self, *args):
            pass  # keep the terminal quiet

    try:
        server = OnlyOneServer(("127.0.0.1", PORT), Page)
    except OSError:
        stop_with("Port " + str(PORT) + " is busy. Close any other example that is still running (Ctrl+C), then run this file again.")

    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        waited = 0
        while not done.is_set() and waited < 600:  # wait up to 10 minutes
            await asyncio.sleep(1)
            waited = waited + 1
    finally:
        server.shutdown()
        server.server_close()

    if got["error"] != "":
        stop_with("The sign-in was cancelled. Run this file again when you are ready.")
    if got["code"] == "":
        stop_with("The sign-in took too long. Run this file again and finish it in the browser.")
    return got["code"], got["state"]


def browser_login(server_url):
    """Give this to the client as "auth" and it will sign you in through your browser."""
    metadata = OAuthClientMetadata(
        client_name="Agentathon Mission 3 agent",
        redirect_uris=["http://127.0.0.1:" + str(PORT) + "/callback"],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        token_endpoint_auth_method="none",
    )
    return OAuthClientProvider(
        server_url=server_url,
        client_metadata=metadata,
        storage=SavedLogin(server_url),
        redirect_handler=open_browser,
        callback_handler=wait_for_code,
    )
