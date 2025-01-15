#!/usr/bin/env python3
import time
from stem import Signal
from stem.control import Controller
import requests

def change_ip():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password='your_password')
        controller.signal(Signal.NEWNYM)

def get_current_ip():
    proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    try:
        response = requests.get('https://api.ipify.org?format=json', proxies=proxies, timeout=5)
        return response.json().get('ip', 'Unknown')
    except requests.RequestException:
        return "Error: Unable to fetch IP"

if __name__ == "__main__":
    while True:
        print("Changing IP...")
        change_ip()
        time.sleep(5)  # Wait for Tor to stabilize
        print("Current IP:", get_current_ip())
        time.sleep(30)  # Change every 30 seconds

