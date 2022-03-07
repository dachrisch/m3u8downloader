#!/bin/bash

chrome_version=$(google-chrome --version|cut -d' ' -f3)
driver_version=$(./chromedriver --version|cut -d' ' -f2)

if [ "$chrome_version" != "$driver_version" ];then
  echo "chrome driver up to date. exit!"
  exit 0
else
  echo "chrome driver need update..."
  download_url="https://chromedriver.storage.googleapis.com/$chrome_version/chromedriver_linux64.zip"
  chromedriver_zip=$(mktemp /tmp/chromedriver.zip.XXXXXX)
  wget "$download_url" -O "$chromedriver_zip"
  unzip -o "$chromedriver_zip"
fi
