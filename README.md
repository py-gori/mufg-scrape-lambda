# mufg-scrape-lambda

## install headleass-chromium
> curl -SL https://github.com/adieuadieu/serverless-chrome/releases/download/v1.0.0-37/stable-headless-chromium-amazonlinux-2017-03.zip > headless-chromium.zip

> unzip headless-chromium.zip -d headless/bin/

> rm headless-chromium.zip

## install chromedriver
> curl -SL https://chromedriver.storage.googleapis.com/2.37/chromedriver_linux64.zip > chromedriver.zip

> unzip chromedriver.zip -d headless/bin/

> rm chromedriver.zip

## install selenium
Lambdaで実行可能なSeleniumパッケージをインストールする為に  
Lambda用Dockerイメージを使用してSeleniumをインストール
- Dockerfile
```
FROM lambci/lambda:build-python3.6

WORKDIR /work

CMD pip install --upgrade pip && \
  pip install selenium retry -t /python/lib/python3.7/site-packages && \
  zip -r selenium.zip /python/
```
コンテナからSeleniumパッケージを取得し/selenium配下に配置
> docker run selenium

> docker cp <CONTAINER ID>:/python/lib ./selenium/

## build
> sam build

## test
> sam local start-api

## deploy
> sam deploy -g
