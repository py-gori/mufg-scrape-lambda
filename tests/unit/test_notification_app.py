import os
import pytest

from mufg_notification.app import make_message, send_line


@pytest.fixture
def test_data():
    return {
        'summary': {
            'yields': 0,
            'valuation': 0,
            'contribution_amount': 0,
            'gain_loss': 0,
        },
        'products': [
            {
                'product_name': 'productA',
                'valuation': 0,
                'contribution_amount': 0,
                'gain_loss': 0,
                'gain_loss_rate': 0,
            },
            {
                'product_name': 'productB',
                'valuation': 0,
                'contribution_amount': 0,
                'gain_loss': 0,
                'gain_loss_rate': 0,
            },
        ]
    }


def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, text, status_code, ok):
            self.__text = text
            self.__status_code = status_code
            self.__ok = ok

        @property
        def text(self):
            return self.__text

        @property
        def ok(self):
            return self.__ok

        def raise_for_status(self):
            if self.__status_code != 200:
                raise Exception("requests error")

    if args[0] == 'https://notify-api.line.me/api/notify'\
            and 'Authorization' in kwargs['headers'] \
            and 'message' in kwargs['params']:
        return MockResponse('test_line_send', 200, True)

    return MockResponse(None, 404, False)


def test_send_line(mocker):
    mocker.patch('requests.post', side_effect=mocked_requests_post)
    print(dir(mocker))
    print('test')
    os.environ['LINE_TOKEN'] = 'test_token'
    r = send_line(message='test message')


def test_make_message(test_data):
    message = make_message(test_data)

    assert type(message) == str
    assert '確定拠出年金レポート' in message
    assert '全体利回り: 0%' in message
    assert '商品名: productA' in message


def test_make_message_ng(test_data):
    test_data.pop('products')
    with pytest.raises(KeyError):
        make_message(test_data)

    test_data.pop('summary')
    with pytest.raises(KeyError):
        make_message(test_data)
