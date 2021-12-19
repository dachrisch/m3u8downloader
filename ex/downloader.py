import json
from logging import getLogger
from os import makedirs, path

from m3u8downloader import M3u8Downloader


def main():
    log = getLogger(__name__).info
    working_dir = 'down'
    makedirs(working_dir, exist_ok=True)
    with open('urls1-10.json5', 'r') as urls_file:
        urls = json.load(urls_file)

    for url in urls:
        filename = f'{working_dir}/week_{url["id"]}.mp4'
        downloader = M3u8Downloader(url['url'], filename)
        log(f'downloading {url}...')
        downloader.start()


if __name__ == '__main__':
    main()
