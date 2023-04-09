from selenium import webdriver
import boto3
import json
import logging
import os
import time

from scrape import MufgScrape

# UA = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.0 (KHTML, like Gecko) Chrome/86.0.842.0 Safari/535.0'
UA = 'Mozilla/5.0 (Windows NT 5.01) AppleWebKit/536.2 (KHTML, like Gecko) Chrome/64.0.818.0 Safari/536.2'
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def upload_s3(html, filename) -> None:
    bucket_name = os.environ.get('S3_BUCKET')
    key = f'{filename}.html'
    logger.info('S3 Uploading... bucket=%s, filename=%s', bucket_name, key)

    s3 = boto3.resource('s3')
    try:
        bucket = s3.Bucket(bucket_name)
        bucket.put_object(
            Body=html,
            Key=key
        )
        logger.info('S3 Uploaded bucket=%s, filename=%s', bucket_name, key)
    except Exception as e:
        logger.error(e, exc_info=True)


def set_driver_options() -> webdriver.chrome.options.Options:
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--user-agent=' + UA)
    options.add_argument('--disable-gpu')
    options.add_argument('--hide-scrollbars')
    options.add_argument('--single-process')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--window-size=880x996')
    options.add_argument('--window-size=1920x1080')
    options.add_argument('--no-sandbox')
    options.add_argument('--homedir=/tmp')
    options.binary_location = '/opt/python/bin/headless-chromium'
    return options


def handler(event, context, is_lambda=True) -> dict:
    # fake = Faker()
    # ua = fake.chrome(version_from=86, version_to=86)

    if is_lambda:
        options = set_driver_options()
        browser = webdriver.Chrome(
            executable_path='/opt/python/bin/chromedriver',
            options=options
        )
    else:
        browser = webdriver.Chrome()

    scrape = MufgScrape(browser)
    html_list = []
    filename_list = []
    try:
        logger.info('Scrape start...')
        scrape.open_page()
        time.sleep(1)
        scrape.to_login_page()
        time.sleep(1)
        scrape.login()
        time.sleep(1)
        top_page_html = scrape.scrape_top_page()
        time.sleep(1)
        scrape.to_product_page()
        time.sleep(1)
        product_page_html = scrape.scrape_product_page()
        time.sleep(1)
        scrape.logout()

    except Exception as e:
        logger.error(e, exc_info=True)
        error_html = scrape.driver.page_source
        html_list = [error_html]
        filename_list = ['error_page']
        status_code = 500
        message = 'Failed'

    else:
        html_list = [top_page_html, product_page_html]
        filename_list = ['top_page', 'product_page']
        status_code = 200
        message = 'Success'

    finally:
        for html, filename in zip(html_list, filename_list):
            upload_s3(html, filename)
        scrape.driver_close()
        logger.info('Scrape end')

    return {
        'statusCode': status_code,
        'body': json.dumps({
            'message': message,
            # 'location': ip.text.replace('\n', '')
        }),
    }


if __name__ == '__main__':
    result = handler(event=None, context=None, is_lambda=False)
    print(result)
