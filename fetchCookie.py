#! /usr/bin/env python3
import json
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import NoSuchElementException


class Config:
    def __init__(self, json_path):
        config = json.loads(json_path.read_text())
        self.username = config['username']
        self.password = config['password']
        self.chromelocation = config['chromelocation']
        self.chromedriverlocation = config['chromedriverlocation']


def create_webdriver(config):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1420,1080')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.binary_location = config.chromelocation
    service = ChromeService(executable_path=config.chromedriverlocation)
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def get_config():
    config_file = Path(__file__).with_name('config.json')
    if not config_file.exists():
        print("Credentials file is missing")
        sys.exit()
    return Config(config_file)


def get_cookies(config):
    driver = create_webdriver(config)
    driver.get('https://auth.ageofempires.com/')
    time.sleep(5)
    try:
        search_box = driver.find_element('name', 'loginfmt')
        search_box.send_keys(config.username)
        search_box.send_keys(Keys.RETURN)
        time.sleep(5)
        password_box = driver.find_element('name', 'passwd')
        password_box.send_keys(config.password)
        password_box.send_keys(Keys.RETURN)
        time.sleep(5)
        if len(driver.find_elements('id', 'idSIButton9')):
            yes_button = driver.find_element('id', 'idSIButton9')
        else:
            yes_button = driver.find_element('id', 'acceptButton')
        yes_button.click()
    except NoSuchElementException as e:
        print(f'current url: {driver.current_url}')
        print(str(e))
        Path(__file__).with_name('error.png').write_bytes(driver.get_screenshot_as_png())
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
    Path(__file__).with_name('cookies.json').write_text(json.dumps(cookies))
    return cookies


def main():
    config = get_config()
    get_cookies(config)


if __name__ == '__main__':
    main()
