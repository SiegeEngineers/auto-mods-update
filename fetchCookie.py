#! /usr/bin/env python3
import imaplib
import json
import re
import ssl
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
        self.mail_username = config['mail.username']
        self.mail_password = config['mail.password']
        self.mail_hostname = config['mail.hostname']
        self.chromelocation = config['chromelocation']
        self.chromedriverlocation = config['chromedriverlocation']


class MailChecker:
    def __init__(self, hostname: str, username: str, password: str):
        self.mail = None
        self.hostname = hostname
        self.username = username
        self.password = password

    def __enter__(self):
        self.mail = imaplib.IMAP4_SSL(host=self.hostname, ssl_context=ssl.create_default_context(), timeout=30)
        self.mail.login(self.username, self.password)
        self.mail.enable('UTF8=ACCEPT')
        self.mail.select()
        return self

    def get_latest_code(self) -> str | None:
        result, data = self.mail.search(None, 'ALL')
        for num in reversed(data[0].split()):
            result, data = self.mail.fetch(num, 'BODY[TEXT]')
            text = data[0][1].decode('utf-8')
            if m := re.search(r"Sicherheitscode: (\d+)", text):
                return m.group(1)
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.mail:
            self.mail.close()
            self.mail.logout()


def print_indented(text: str):
    text = text.replace(">", ">\n")
    lines = text.split("\n")
    modified_lines = [f"\t{l}" for l in lines if l]
    print("\n".join(modified_lines))


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


def get_cookies(config, checker):
    last_code = checker.get_latest_code()
    driver = create_webdriver(config)
    driver.get('https://auth.ageofempires.com/')
    time.sleep(5)
    try:
        print_indented(driver.page_source)
        print("Looking for name=loginfmt")
        if len(driver.find_elements('name', 'loginfmt')):
            search_box = driver.find_element('name', 'loginfmt')
        else:
            print("Did not find that")
            print("Looking for id=usernameEntry instead")
            search_box = driver.find_element('id', 'usernameEntry')
        print("Entering username")
        search_box.send_keys(config.username)
        search_box.send_keys(Keys.RETURN)
        time.sleep(5)
        print_indented(driver.page_source)
        print("Looking for span.fui-Link")
        my_element = driver.find_elements('css selector', 'span.fui-Link')
        if len(my_element):
            print('found span')
            print(my_element[0].get_attribute("innerText"))
            print("clicking on it")
            my_element[0].click()
            time.sleep(5)
            print_indented(driver.page_source)
        print("Looking for span.fui-Link")
        my_element = driver.find_elements('css selector', 'span.fui-Link')
        if len(my_element) and my_element[0].get_attribute("innerText") == 'Ihr Kennwort verwenden':
            print('found span again hrrm and it says Ihr Kennwort verwenden')
            print(my_element[0].get_attribute("innerText"))
            print("clicking on it")
            my_element[0].click()
            time.sleep(5)
            print_indented(driver.page_source)

        print("Looking for name=passwd")
        password_box = driver.find_element('name', 'passwd')
        print("Entering password")
        password_box.send_keys(config.password)
        password_box.send_keys(Keys.RETURN)
        time.sleep(5)
        print_indented(driver.page_source)
        print("Looking for span.fui-Link")
        my_element = driver.find_elements('css selector', "span.fui-Link")
        if len(my_element) and 'mods@siegeengineers.org' in my_element[0].get_attribute("innerText"):
            print(f"Found it and it says {my_element[0].get_attribute('innerText')}")
            print("clicking on it")
            my_element[0].click()
            time.sleep(5)
            print_indented(driver.page_source)
            print("Looking for id=codeEntry-0")
            driver.find_element('id', "codeEntry-0")
            new_code = last_code
            rounds = 60
            print(f"last code was {last_code}")
            while new_code == last_code and rounds > 0:
                print(f"checking for new code ({rounds})")
                new_code = checker.get_latest_code()
                time.sleep(10)
                rounds -= 1
            print(f"using code {new_code}")
            numbers = new_code.split()
            for i in range(len(numbers)):
                print(f"Typing code {numbers[i]} into id=codeEntry-{i}")
                input_element = driver.find_element('id', f"codeEntry-{i}")
                input_element.send_keys(numbers[i])
            time.sleep(5)
            print_indented(driver.page_source)

        print("Looking for id=idSIButton9")
        if len(driver.find_elements('id', 'idSIButton9')):
            print("found id=idSIButton9")
            yes_button = driver.find_element('id', 'idSIButton9')
        elif len(driver.find_elements('id', 'acceptButton')):
            print("found id=acceptButton instead")
            yes_button = driver.find_element('id', 'acceptButton')
        else:
            print("Looking for button[data-testid='primaryButton']")
            yes_button = driver.find_element('css selector', "button[data-testid='primaryButton']")
        print("clicking on it")
        yes_button.click()
    except NoSuchElementException as e:
        print(f'current url: {driver.current_url}')
        print(str(e))
        Path(__file__).with_name('error.png').write_bytes(driver.get_screenshot_as_png())
    time.sleep(10)

    cookies = {}
    print(driver.get_cookies())
    for i in range(10):
        cookie_name = '.AgeOfEmpiresServices'
        if i > 0:
            cookie_name = f'.AgeOfEmpiresServicesC{i}'
        single_cookie_result = driver.get_cookie(cookie_name)
        if single_cookie_result is not None:
            cookies[cookie_name] = single_cookie_result['value']
        print(cookies)
    driver.quit()
    if cookies:
        Path(__file__).with_name('cookies.json').write_text(json.dumps(cookies))
    return cookies


def main():
    config = get_config()
    with MailChecker(hostname=config.mail_hostname, username=config.mail_username, password=config.mail_password) as checker:
        get_cookies(config, checker)


if __name__ == '__main__':
    main()
