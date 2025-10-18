import logging

import requests
from ap2.types.mandate import CartMandate


http_proxy = "http://proxy.jpmchase.net:8443"
proxies = {
            "http"  : http_proxy,
            "https" : http_proxy
            }

default_mid = "999959695028-smoke-tests-upg-diu"


def get_token(merchant_id):
    token_url = "https://api.checkout-dev.jpmchase.com/ms-api/v2/token/plain?type=merchant"
    header_key = "x-checkout-merchant-id"
    r = requests.get(token_url, headers={header_key: merchant_id}, proxies=proxies)
    return r.content


import base64
import json
import uuid


logging.basicConfig(level=logging.INFO)


def generate_order_number():
  """Generates a base64-encoded UUID string."""
  return uuid.uuid4().hex[0:16]

def create_payment_link(merchant_id, product_name : str,  unit_price: int, quantity: int = 1):
    paylink_url = "https://merchant-api.checkout-dev.jpmchase.com/v1/payment-links"
    body = {
          "merchantOrderNumber": generate_order_number(),
          "name": "LINK_NAME",
          "description": "LINK_DESCRIPTION",
          "items": [{
            "product": {
              "name": product_name,
              "productName": product_name,
              "stockKeepingUnit": "PRODUCT_SKU",
              "productDescription": "PRODUCT_DESCRIPTION"
            },
            "quantity": quantity,
            "unitPrice": unit_price
          }],
          "expirationTimestamp": "2025-04-18T22:32:42.866966Z",
          "currencyCode": "USD",
          "totalTransactionAmount": quantity * unit_price
        }
    token = get_token(merchant_id)
    headers = {"authorization": token, "x-checkout-version": "developer",
               "merchantId": merchant_id }

    resp = requests.post(paylink_url, headers=headers, json = body, proxies=proxies)
    return resp



def _lookup_merchant(merchant_name : str):
    # TODO: to implement a function to return the actual merchant id by name.
    return default_mid

import json


def _setup_intent(merchant_id, cart_id : str, currency : str, value : int):
    logging.info("==== Checkout: Setup checkout intent ...")
    api_url = "https://merchant-api.checkout-dev.jpmchase.com/v1/checkout/intent"
    body = {
            "merchantOrderNumber": f"{cart_id}" ,
            "currencyCode": f"{currency}",
            "cart": {
                "totalTransactionAmount": value
                # TODO: shipping address
            },
            "consumer": {
                "email": "customer@jpmchase.com"
                # "billingAddress": {
                #     "recipientFullName": "John Smith",
                #     "line1": "1 Main St",
                #     "city": "San Francisco",
                #     "state": "CA",
                #     "country": "US",
                #     "postalCode": "95000"
                # }
            },
            "checkoutOptions": {
                "authorization": {
                    "authorizationType": "AUTH_METHOD_CART_AMOUNT",
                    "partial_authorization_support": "true"
                },
                "capture": {
                    "captureMethod": "CAPTURE_METHOD_NOW"
                },
                "consumerProfileOptions": {
                    "isSaveConsumerProfile": "false"
                }
            }
        }
    token = get_token(merchant_id)
    headers = {"authorization": "Bearer " +  token.decode('utf-8'),
               "x-checkout-version": "developer",
               "merchantId": merchant_id,
               "requestId": "321",
               "content-type": "application/json" }

    logging.info("Checkout: request to checkout: header=%s, proxies=%s", headers, proxies)
    logging.info("Checkout: request to checkout: body=%s", json.dumps(body))

    #resp = requests.post(api_url, headers=headers, json=body, proxies=proxies)
    resp = requests.post(api_url, headers=headers, json=body)
    logging.info("Checkout: response from checkout intent: %s, text=%s, json=%s", resp, resp.text, resp.json())
    jwt = resp.json()["checkoutSessionToken"]
    return merchant_id, jwt


from datetime import datetime


def setup_intent(cart_mandate : CartMandate):
    logging.info("========================================")
    logging.info("Checkout: Setup checkout intent ...")
    logging.info("========================================")
    cart_id = cart_mandate.contents.id
    payment_request = cart_mandate.contents.payment_request
    currency = payment_request.details.total.amount.currency
    value = int(payment_request.details.total.amount.value * 100)
    merchant_id = _lookup_merchant(cart_mandate.contents.merchant_name)
    # Get the current datetime object
    current_datetime = datetime.now()
    timestamp_string = current_datetime.strftime("%Y%m%d%H%M%S")
    order_ref = "ref" + timestamp_string
    return _setup_intent(merchant_id, order_ref, currency, value)


def confirm_checkout(merchant_id, cart_id : str):
    logging.info("========================================")
    logging.info("Checkout: Confirming checkout intent ...")
    logging.info("========================================")

    api_url = "https://merchant-api.checkout-dev.jpmchase.com/v1/checkout/intent/confirm"
    body = {
        "merchantOrderNumber": cart_id,
        "paymentMethodType": {
            "card": {
                "accountNumberType": "PAN",
                "accountNumber": "4444444444444455",
                "expiry": {
                    "month": 12,
                    "year": 2026
                },
                "cvv": "123"
            }
        }
    }
    token = get_token(merchant_id)
    headers = {"authorization": "Bearer " +  token.decode('utf-8'),
               "x-checkout-version": "developer",
               "merchantId": merchant_id,
               "requestId": "321",
               "content-type": "application/json" }

    logging.info("Checkout: request to checkout: header=%s, proxies=%s", headers, proxies)
    logging.info("Checkout: request to checkout: body=%s", json.dumps(body))

    #resp = requests.post(api_url, headers=headers, json=body, proxies=proxies)
    resp = requests.post(api_url, headers=headers, json=body)
    logging.info("Checkout: response: %s, text=%s, json=%s", resp, resp.text, resp.json())
    return resp.json()


def init_pay(merchant_id, jwt):
    #checkout_grpc_web.pay(merchant_id, jwt)
    logging.info("Checkout: init payment... no op yet")


logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    order = generate_order_number()
    _setup_intent("999959695028-smoke-tests-upg-diu", order, "USD", "999")
    confirm_checkout("999959695028-smoke-tests-upg-diu", order)
