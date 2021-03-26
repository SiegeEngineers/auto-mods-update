#! /usr/bin/env python3
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

HEADERS = {
    'authority': 'api.ageofempires.com',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'dnt': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
    'origin': 'https://www.ageofempires.com',
    'sec-fetch-site': 'same-site',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://www.ageofempires.com/mods/details/17219/',
    'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
}


class Config:
    def __init__(self, json_path):
        config = json.loads(json_path.read_text())
        self.username = config['username']
        self.password = config['password']
        self.chromelocation = config['chromelocation']
        self.chromedriverlocation = config['chromedriverlocation']
        self.mods = config['mods']


def create_webdriver(config):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1420,1080')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.binary_location = config.chromelocation
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(config.chromedriverlocation, options=chrome_options)
    return driver


def get_config():
    config_file = Path(__file__).with_name('config.json')
    if not config_file.exists():
        print("Credentials file is missing")
        sys.exit()
    return Config(config_file)


def get_mod_details(mod_id, cookies):
    data = {
        'ModId': mod_id,
    }
    result = requests.post('https://api.ageofempires.com/api/v1/mods/Detail', json=data, headers=HEADERS,
                           cookies=cookies)
    if result.status_code != 200:
        print(f'Received status code {result.status_code}')
        print('Cookie seems invalid!')
        sys.exit(1)
    return result.json()


def upload_new_mod_version(mod_id, filename, cookies):
    existing_data = get_mod_details(mod_id, cookies)
    today = datetime.utcnow().strftime('%Y-%m-%d')
    data_edit = {
        'ModId': mod_id,
        'ModName': existing_data['modName'],
        'ModVisibility': 1,
        'GameTitleId': existing_data['gameTitleId'],
        'ModType': existing_data['modTypeId'],
        'Description': existing_data['description'],
        'ChangeList': f'<p>Version of {today}</p>',
        'modTags': existing_data['modTags'],
        'ImageMetaData': json.dumps(existing_data['imageUrls']),
    }
    zip_file = Path(__file__).with_name(filename)
    files = [
        ('modFiles', (filename, zip_file.open('rb'), 'application/zip'))
    ]

    url_edit = 'https://api.ageofempires.com/api/v1/mods/Edit'
    result_edit = requests.post(url_edit, data=data_edit, headers=HEADERS, cookies=cookies, files=files)
    if result_edit.status_code != 200:
        print(f'Edit result status code was {result_edit.status_code}')
        print(result_edit.text)
        sys.exit(1)
    else:
        print(f'Successfully updated mod {mod_id}.')


def get_cookies(config):
    driver = create_webdriver(config)
    driver.get('https://auth.ageofempires.com/')
    time.sleep(5)
    search_box = driver.find_element_by_name('loginfmt')
    search_box.send_keys(config.username)
    search_box.send_keys(Keys.RETURN)
    time.sleep(5)
    password_box = driver.find_element_by_name('passwd')
    password_box.send_keys(config.password)
    password_box.send_keys(Keys.RETURN)
    time.sleep(5)
    try:
        yes_button = driver.find_element_by_id('idSIButton9')
        yes_button.click()
    except NoSuchElementException:
        print(f'current url: {driver.current_url}')
        Path(__file__).with_name('error.png').write_bytes(driver.get_screenshot_as_png())
        #sys.exit(1)
    time.sleep(10)

    cookies = {}
    for i in range(10):
        cookie_name = '.AgeOfEmpiresServices'
        if i > 0:
            cookie_name = f'.AgeOfEmpiresServicesC{i}'
        single_cookie_result = driver.get_cookie(cookie_name)
        if single_cookie_result is not None:
            cookies[cookie_name] = single_cookie_result['value']
    driver.quit()
    return cookies


def main():
    config = get_config()
    cookies = get_cookies(config)

    for mod_id in config.mods:
        upload_new_mod_version(mod_id, config.mods[mod_id], cookies)


if __name__ == '__main__':
    main()
