import requests

proxies = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}
response = requests.get('https://api.ipify.org?format=json', proxies=proxies)
print(response.json())

