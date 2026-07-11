import ssl

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