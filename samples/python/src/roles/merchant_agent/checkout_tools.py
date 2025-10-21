import base64
import hashlib
import json
import logging
import uuid

import requests

from common.c7_models import C7Response

from ap2.types.mandate import CartContents, CartMandate
from ap2.types.payment_request import (
    PaymentCurrencyAmount,
    PaymentDetailsInit,
    PaymentItem,
    PaymentRequest,
)


http_proxy = 'http://proxy.jpmchase.net:8443'
proxies = {'http': http_proxy, 'https': http_proxy}

default_mid = '999959695028-smoke-tests-upg-diu'


def get_token(merchant_id):
    """Retrieve an authentication token for the specified merchant.

    Parameters
    ----------
    merchant_id : str
        The merchant ID for which to obtain the token.

    Returns
    -------
    bytes
        The authentication token as bytes.
    """
    token_url = 'https://api.checkout-dev.jpmchase.com/ms-api/v2/token/plain?type=merchant'
    header_key = 'x-checkout-merchant-id'
    r = requests.get(
        token_url, headers={header_key: merchant_id}, proxies=proxies
    )
    return r.content


logging.basicConfig(level=logging.INFO)


def generate_order_number():
    """Generates a base64-encoded UUID string."""
    return uuid.uuid4().hex[0:16]


def create_payment_link(
    merchant_id, product_name: str, unit_price: int, quantity: int = 1
):
    paylink_url = (
        'https://merchant-api.checkout-dev.jpmchase.com/v1/payment-links'
    )
    body = {
        'merchantOrderNumber': generate_order_number(),
        'name': 'LINK_NAME',
        'description': 'LINK_DESCRIPTION',
        'items': [
            {
                'product': {
                    'name': product_name,
                    'productName': product_name,
                    'stockKeepingUnit': 'PRODUCT_SKU',
                    'productDescription': 'PRODUCT_DESCRIPTION',
                },
                'quantity': quantity,
                'unitPrice': unit_price,
            }
        ],
        'expirationTimestamp': '2025-04-18T22:32:42.866966Z',
        'currencyCode': 'USD',
        'totalTransactionAmount': quantity * unit_price,
    }
    token = get_token(merchant_id)
    headers = {
        'authorization': token,
        'x-checkout-version': 'developer',
        'merchantId': merchant_id,
    }

    resp = requests.post(
        paylink_url, headers=headers, json=body, proxies=proxies
    )
    return resp


def _lookup_merchant(merchant_name: str) -> str:
    # TODO: to implement a function to return the actual merchant id by name.
    return default_mid


def _setup_intent(
    merchant_id: str, order_number: str, currency: str, value: int
) -> C7Response:
    logging.info('==== Checkout: Setup checkout intent ...')

    api_url = (
        'https://merchant-api.checkout-dev.jpmchase.com/v1/checkout/intent'
    )
    logging.info(
        '==== Args: %s, %s, %s, %s',
        merchant_id,
        order_number,
        currency,
        value,
    )
    body = {
        'merchantOrderNumber': order_number,
        'currencyCode': currency,
        'cart': {
            'totalTransactionAmount': value
            # TODO: shipping address
        },
        'consumer': {
            'email': 'customer@jpmchase.com'
            # TODO: billing address
            # "billingAddress": {
            #     "recipientFullName": "John Smith",
            #     "line1": "1 Main St",
            #     "city": "San Francisco",
            #     "state": "CA",
            #     "country": "US",
            #     "postalCode": "95000"
            # }
        },
        'checkoutOptions': {
            'authorization': {
                'authorizationType': 'AUTH_METHOD_CART_AMOUNT',
                'partial_authorization_support': 'true',
            },
            'capture': {'captureMethod': 'CAPTURE_METHOD_NOW'},
            'consumerProfileOptions': {'isSaveConsumerProfile': 'false'},
        },
    }
    token = get_token(merchant_id)
    headers = {
        'authorization': 'Bearer ' + token.decode('utf-8'),
        'x-checkout-version': 'developer',
        'merchantId': merchant_id,
        'requestId': order_number,
        'content-type': 'application/json',
    }

    logging.info(
        'Checkout: request to checkout: header=%s, body=%s',
        headers,
        json.dumps(body),
    )

    # resp = requests.post(api_url, headers=headers, json=body, proxies=proxies)
    resp = requests.post(api_url, headers=headers, json=body)
    logging.info(
        'Checkout: response from checkout intent: %s, text=%s, json=%s',
        resp,
        resp.text,
        resp.json(),
    )
    # jwt = resp.json()["checkoutSessionToken"]
    return C7Response(api='checkent/setup_intent', response=resp.json())


def deterministic_alphanumeric_hash(input_string, desired_length=None):
    """Generates a deterministic alphanumeric hash of a string.

    Args:
        input_string (str): The string to be hashed.
        desired_length (int, optional): The desired length of the alphanumeric string.
                                        If None, the full Base64 encoded hash is returned.

    Returns:
        str: An alphanumeric string representing the hash of the input string.
    """
    # 1. Encode the input string to bytes (UTF-8 is common)
    input_bytes = input_string.encode('utf-8')

    # 2. Compute a cryptographic hash (e.g., SHA256)
    hashed_bytes = hashlib.sha256(input_bytes).digest()

    # 3. Encode the hash bytes to a Base64 alphanumeric string
    alphanumeric_hash = base64.b64encode(hashed_bytes).decode('ascii')

    # 4. Remove unwanted characters (if any) and potentially truncate to desired length
    for u in ['=', '+', '/', '-', '_']:
        alphanumeric_hash = alphanumeric_hash.replace(u, '')

    if desired_length is not None:
        return alphanumeric_hash[:desired_length]
    else:
        return alphanumeric_hash


def _lookup_order_number(cart_id: str, cart_expiry: str):
    return deterministic_alphanumeric_hash(
        cart_id + cart_expiry, desired_length=12
    )


def setup_intent(cart_mandate: CartMandate) -> C7Response:
    """Set up a checkout intent for the provided cart mandate.

    Parameters
    ----------
    cart_mandate : CartMandate
        The cart mandate containing cart and payment details.

    Returns
    -------
    C7Response
        The response from the checkout intent setup API.
    """
    logging.info('========================================')
    logging.info('Checkout: Setup checkout intent ...')
    logging.info('========================================')
    cart_id = cart_mandate.contents.id
    cart_expiry = cart_mandate.contents.cart_expiry
    payment_request = cart_mandate.contents.payment_request
    currency = payment_request.details.total.amount.currency
    value = int(payment_request.details.total.amount.value * 100)
    merchant_id = _lookup_merchant(cart_mandate.contents.merchant_name)
    order_number = _lookup_order_number(cart_id, cart_expiry)
    return _setup_intent(merchant_id, order_number, currency, value)


def confirm_checkout(cart_mandate: CartMandate) -> C7Response:
    cart_id = cart_mandate.contents.id
    cart_expiry = cart_mandate.contents.cart_expiry
    merchant_id = _lookup_merchant(cart_mandate.contents.merchant_name)
    order_number = _lookup_order_number(cart_id, cart_expiry)
    return _confirm_checkout(merchant_id, order_number=order_number)


def _confirm_checkout(merchant_id, order_number: str) -> C7Response:
    logging.info('========================================')
    logging.info('Checkout: Confirming checkout intent ...')
    logging.info('========================================')
    logging.info(
        '==== Args: %s, %s',
        merchant_id,
        order_number,
    )
    api_url = 'https://merchant-api.checkout-dev.jpmchase.com/v1/checkout/intent/confirm'
    body = {
        'merchantOrderNumber': order_number,
        'paymentMethodType': {
            'card': {
                'accountNumberType': 'PAN',
                'accountNumber': '4444444444444455',
                'expiry': {'month': 12, 'year': 2026},
                'cvv': '123',
            }
        },
    }
    token = get_token(merchant_id)
    headers = {
        'authorization': 'Bearer ' + token.decode('utf-8'),
        'x-checkout-version': 'developer',
        'merchantId': merchant_id,
        'requestId': order_number,
        'content-type': 'application/json',
    }

    logging.info(
        'Checkout: request to checkout: header=%s, body=%s',
        headers,
        json.dumps(body),
    )

    # resp = requests.post(api_url, headers=headers, json=body, proxies=proxies)
    resp = requests.post(api_url, headers=headers, json=body)
    logging.info(
        'Checkout: response: %s, text=%s, json=%s', resp, resp.text, resp.json()
    )
    return C7Response(api='checkout/confirm_intent', response=resp.json())


def _test_with_cart_id(cart_id: str = 'cart_1'):
    order_number = _lookup_order_number(cart_id, '2025-12-31T23:59:59Z')
    resp = _setup_intent(
        default_mid,
        order_number,
        'USD',
        '999',
    )
    logging.info('Setup intent response: %s', resp)
    resp = _confirm_checkout(default_mid, order_number)
    logging.info('Confirm intent response: %s', resp)


def _test_with_cart_mandate(cart_id):
    cart_mandate = CartMandate(
        contents=CartContents(
            id=cart_id,
            merchant_name='Awesome merchant',
            user_cart_confirmation_required=True,
            cart_expiry='2025-12-31T23:59:59Z',
            payment_request=PaymentRequest(
                method_data=[],
                details=PaymentDetailsInit(
                    id='total',
                    display_items=[],
                    total=PaymentItem(
                        label='Total',
                        amount=PaymentCurrencyAmount(
                            currency='USD', value='9.99'
                        ),
                    ),
                ),
            ),
        )
    )

    resp = setup_intent(cart_mandate)
    logging.info('Setup intent response: %s', resp)
    resp = confirm_checkout(cart_mandate)
    logging.info('Confirm intent response: %s', resp)


if __name__ == '__main__':
    _test_with_cart_id('cart_1')
    _test_with_cart_mandate('cart_2')
