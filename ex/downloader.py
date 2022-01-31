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


class DropboxM3u8Retriever:
    def __init__(self):
        self.videos: List[VideoFile] = []
        self.browser = WebDriver(service=Service('./chromedriver'))
        self.browser.implicitly_wait(10)
        self.wait = WebDriverWait(self.browser, timeout=3)
        self.log = getLogger(self.__class__.__name__).info

    def get_video_files(self, url, password):
        self.login(url, password)
        for video_url in self.collect_video_urls():
            self.load_video_player(video_url)

        return self.videos

    def collect_video_urls(self):
        self.wait.until(item_present)
        video_links = self.browser.find_elements(By.XPATH, '//td/a')
        video_urls = list(map(lambda video: video.get_attribute('href'), video_links))
        return video_urls

    def login(self, url, password):
        self.log(f'logging into page at: {url}')
        self.browser.get(url)
        self.wait.until(button_enabled)
        self.browser.find_element(By.NAME, 'shared-link-password').send_keys(password)
        self.browser.find_element(By.CLASS_NAME, 'mc-button-content').click()

    def load_video_player(self, video_url):
        self.browser.get(video_url)
        source = self.browser.find_element(By.XPATH, '//source')
        self.log(f'obtained video [{self.browser.title}] at [{source.get_attribute("src")}]')
        self.found_video(self.browser.title, source.get_attribute('src'))

    def found_video(self, title, url):
        self.videos.append(VideoFile(title, url))


def main():
    parser = ArgumentParser(prog='m3u8downloader',
                            description="download video and audio at m3u8 url")
    parser.add_argument('url_file', metavar='URL_FILE', help='file containing m3u8 urls')
    args = parser.parse_args()
    log = getLogger(__name__).info
    working_dir = 'down'
    makedirs(working_dir, exist_ok=True)
    with open(args.url_file, 'r') as urls_file:
        video_json = json.load(urls_file)

    video_files = DropboxM3u8Retriever().get_video_files(video_json['url'], video_json['password'])

    for video_file in video_files:
        filename = f'{working_dir}/{video_file.filename}'
        if os.path.isfile(filename):
            log(f'skipping already present {video_file}')
        else:
            downloader = M3u8Downloader(video_file.url, filename, tempdir=working_dir)
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
