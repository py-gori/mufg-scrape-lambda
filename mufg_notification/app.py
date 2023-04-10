import boto3
import json
import logging
import os
import requests

from datetime import date
from bs4 import BeautifulSoup

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def fetch_data(bucket, key) -> str:
    try:
        logger.info('Download start. bucket=%s, key=%s', bucket, key)
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket=bucket, Key=key)
        logger.info('Download end. content-type=%s', response['ContentType'])
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


def extract_top_page(body) -> dict:
    logger.info('Top_page extracting...')
    soup = BeautifulSoup(body, 'html.parser')
    yields = soup.find(id='reviewGroup03').find('span').string.strip()
    valuation = soup.find(id='assetBlanceInfo').find_all('tr')[1].find_all('em')[0].string.strip()
    contribution_amount = soup.find(id='assetBlanceInfo').find_all('tr')[1].find_all('em')[1].string.strip()
    gain_loss = soup.find(id='assetBlanceInfo').find_all('tr')[1].find_all('em')[2].string.strip()
    summary = {
        'yields': yields,
        'valuation': valuation,
        'contribution_amount': contribution_amount,
        'gain_loss': gain_loss,
    }
    logger.info('summary data=%s', summary)
    logger.info('Top_page extracted.')
    return summary


def extract_product_page(body) -> [dict]:
    logger.info('Product_page extracting...')
    soup = BeautifulSoup(body, 'html.parser')
    asset_table = soup.find(class_='asset_table')
    product_elems = asset_table.find_all('a')
    products = []
    for elem in product_elems:
        product_name = elem.string.strip()
        products.append({
            'product_name': product_name,
        })

    products_info = asset_table.find_all('em')
    for i in range(len(products)):
        products[i]['valuation'] = products_info[(i*4)].string.strip()
        products[i]['contribution_amount'] = products_info[(i*4)+1].string.strip()
        products[i]['gain_loss'] = products_info[(i*4)+2].string.strip()
        products[i]['gain_loss_rate'] = products_info[(i*4)+3].string.strip()
        logger.info('product_data=%s', products[i])
    logger.info('Product_page extracted.')
    return products


def make_message(data) -> str:
    today = date.today().strftime('%Y-%m-%d')
    message = f"""
{today} 確定拠出年金レポート

全体利回り: {data['summary']['yields']}%
資産評価額: {data['summary']['valuation']}円
拠出金累計: {data['summary']['contribution_amount']}円
評価損益: {data['summary']['gain_loss']}円
"""
    for product in data['products']:
        message += f"""
商品名: {product['product_name']}
資産評価額: {product['valuation']}円
拠出金額累計: {product['contribution_amount']}円
損益: {product['gain_loss']}円
損益率: {product['gain_loss_rate']}%
"""
    return message


def send_line(message) -> None:
    payload = {'message': message}
    token = os.environ.get('LINE_TOKEN')
    r = requests.post(
        'https://notify-api.line.me/api/notify',
        headers={'Authorization': 'Bearer ' + token},
        params=payload
    )
    if not r.ok:
        raise Exception(f'LINE send failed. result={r.text}')
    logger.info('LINE send. result=%s', r)


def handler(event, context) -> dict:
    # bucket = event['Records'][0]['s3']['bucket']['name']
    # key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    bucket = os.environ.get('S3_BUCKET')
    top_html = fetch_data(bucket, 'top_page.html')
    summary = extract_top_page(top_html)

    product_html = fetch_data(bucket, 'product_page.html')
    products = extract_product_page(product_html)
    data = {
        'summary': summary,
        'products': products
    }
    send_line(make_message(data))

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "success",
        }),
    }


if __name__ == '__main__':
    result = handler(event=None, context=None)
    print(result)
