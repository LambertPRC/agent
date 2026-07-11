import ssl
import sys


def _configure_console_encoding():
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


_configure_console_encoding()

_original_load_windows_store_certs = ssl.SSLContext._load_windows_store_certs

def _patched_load_windows_store_certs(self, storename, purpose):
    try:
        _original_load_windows_store_certs(self, storename, purpose)
    except ssl.SSLError:
        pass

ssl.SSLContext._load_windows_store_certs = _patched_load_windows_store_certs

import os, certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

from infra.openai_client import SendMessage
from agent import agent_invoke

def print_hi():
    msg = SendMessage([
        {"role": "system", "content": "明天杭州的天气如何"}
    ])
    print(msg)

if __name__ == '__main__':
    agent_invoke([
        {"role": "user", "content": "明天杭州的天气如何"}
    ])
