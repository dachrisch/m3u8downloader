import json
import os.path
import random
import string
from argparse import ArgumentParser
from logging import getLogger
from os import makedirs
from typing import List

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from m3u8downloader import M3u8Downloader


class VideoFile:
    def __init__(self, filename, url):
        self.url = url
        self.filename = filename

    def __repr__(self):
        return f'{self.__class__.__name__}(name={self.filename}, url={self.url})'


class DropboxVideoPage:
    def __init__(self, browser, video_url):
        self.video_url = video_url
        self.browser = browser
        self.log = getLogger(self.__class__.__name__).info

    def __enter__(self):
        self.browser.get(self.video_url)
        source = self.browser.find_element(By.XPATH, '//source')
        self.log(f'obtained video [{self.browser.title}] at [{source.get_attribute("src")}]')
        return VideoFile(self.browser.title, source.get_attribute('src'))

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class DropboxVideoListPage:
    def __init__(self, browser):
        self.browser = browser
        self.wait = WebDriverWait(self.browser, timeout=3)

    def get_video_files(self):
        videos: List[VideoFile] = []
        for video_page in self.collect_video_urls():
            with video_page as video_file:
                videos.append(video_file)

        return videos

    def collect_video_urls(self):
        self.wait.until(item_present)
        video_links = self.browser.find_elements(By.XPATH, '//td/a')
        video_urls = list(map(lambda video: DropboxVideoPage(self.browser, video.get_attribute('href')), video_links))
        return video_urls


class DropboxLoginPage:
    def __init__(self, browser, url):
        self.browser = browser
        self.url = url
        self.log = getLogger(self.__class__.__name__).info
        self.wait = WebDriverWait(self.browser, timeout=3)

    def __enter__(self):
        self.browser.get(self.url)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.quit()

    def login(self, password):
        self._login(self.url, password)
        return DropboxVideoListPage(self.browser)

    def no_login(self):
        self.log(f'calling page at: {self.url}')
        return DropboxVideoListPage(self.browser)

    def _login(self, url, password):
        self.log(f'logging into page at: {url}')
        self.wait.until(button_enabled)
        self.browser.find_element(By.NAME, 'shared-link-password').send_keys(password)
        self.browser.find_element(By.CLASS_NAME, 'mc-button-content').click()


class DropboxM3u8Retriever:
    def __init__(self):
        self.browser = WebDriver(service=Service('./chromedriver'))
        self.browser.implicitly_wait(10)

    def load(self, url) -> DropboxLoginPage:
        return DropboxLoginPage(self.browser, url)


def main():
    parser = ArgumentParser(prog='m3u8downloader',
                            description="download video and audio at m3u8 url")
    parser.add_argument('url_file', help='file containing m3u8 urls')
    parser.add_argument('directory', help='directory to download files')
    args = parser.parse_args()
    log = getLogger(__name__).info
    makedirs(args.directory, exist_ok=True)
    with open(args.url_file, 'r') as urls_file:
        video_json = json.load(urls_file)

    with DropboxM3u8Retriever().load(video_json['url']) as page:
        if 'password' in video_json:
            video_page = page.login(video_json['password'])
        else:
            video_page = page.no_login()

        video_files = video_page.get_video_files()

    for video_file in video_files:
        filename = f'{args.directory}/{video_file.filename}'
        if os.path.isfile(filename):
            log(f'skipping already present [{video_file.filename}]')
        else:
            downloader = M3u8Downloader(video_file.url, filename, tempdir=args.directory)
            log(f'downloading {video_file}...')
            downloader.start()


def button_enabled(driver: WebDriver):
    element = driver.find_element(By.NAME, 'shared-link-password')
    element.send_keys(random.choice(string.ascii_letters))
    ready = driver.find_element(By.CLASS_NAME, 'mc-button-large').is_enabled()
    element.clear()
    return ready


def item_present(driver: WebDriver):
    return driver.find_element(By.CLASS_NAME, 'download-button')


if __name__ == '__main__':
    main()
