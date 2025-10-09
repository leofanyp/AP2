import base64
import logging

import requests
#from checkout.fe.v1 import PayRequest, YourResponseMessage
from checkout.fe.v1 import checkout_fe_api_pb2 as c7_fe_api
from checkout.fe.v1 import checkout_fe_api_pb2_grpc as c7_fe_grpc
from common.v1 import common_pb2
from roles.merchant_agent import checkout_tools

    #checkout_dot_fe_dot_v1_dot_checkout__fe__api__pb2

#from your_generated_protos import YourRequestMessage, YourResponseMessage

logging.basicConfig(level=logging.INFO)


# Assuming you have a gRPC-Web proxy at this URL
PROXY_URL = "http://localhost:8080/your.service.Name/YourMethod"
PROXY_URL = "https://api.checkout-dev.jpmchase.com/checkout.fe.v1.CheckoutFrontendV1Service/Pay"
GetEncryptionKey_URL = "https://api.checkout-dev.jpmchase.com/checkout.fe.v1.CheckoutFrontendV1Service/GetEncryptionKey"

#PROXY_URL = "https://localhost:8081/checkout.fe.v1.CheckoutFrontendV1Service/Pay"
MERCHANT_ID = "451207-smoke-tests-orb-diu"
# another one: "999959695028-smoke-tests-upg-diu"
#MERCHANT_ID = "999959695028-smoke-tests-upg-diu"


http_proxy = "http://proxy.jpmchase.net:8443"
proxies = {
            "http"  : http_proxy,
            "https" : http_proxy
            }

def get_token(merchant_id):
    token_url = "https://api.checkout-dev.jpmchase.com/ms-api/v2/token/plain?type=merchant"
    header_key = "x-checkout-merchant-id"
    r=requests.get(token_url, headers={header_key: merchant_id}, proxies=proxies)
    #return r.content.decode('utf-8')
    #return r.content
    return "eyJraWQiOiI3ZTYwYjgyNi0wMDNlLTQ5OTktOTVlZS1jOGE5NzJmZWZlZmIiLCJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjaGVja291dCIsImp0aSI6IjJjZDJhMzNhLTU3OGEtNDljZS1iNWIxLTdiODAzNTRlMWY2NSIsIm1pZCI6Ijk5OTk1OTY5NTAyOC1zbW9rZS10ZXN0cy11cGctZGl1Iiwia3NpIjoiS09VTlRTQjVBRlhJV1RNVTZOREFYQ0NISU5KRFRVTEEiLCJtb3IiOiIxMjMiLCJyaWQiOiIzMjEiLCJwIjoiaW4iLCJSb2xlIjpbIlRSQU5TQUNUSU9OQUxfQ0hFQ0tPVVRfU0hPUFBFUiJdLCJjaWQiOiIwLjM0MDZkMjE3LjE3NTk4NzU0NDUuMTc0ZjkxMTIiLCJpYXQiOjE3NTk4NzU0NDUsImV4cCI6MTc1OTg4MjY0NSwib2QiOiIzYjYzYjQ5MWM0Y2MzMjk0MWM1MTM2MGJkNDNjOWMzZGE5OGZjOGQwMjZhOGQ0ZDhlMzRlYTQ5NWJlNzZmNTExNjg3N2ZjZjU2MmRjNGJjYzIxNzAzYjgwNjQ0N2I2YjUxNDk2OTJkZDIyZDgxZmU0NWQyMGE0N2ViYTJmZGUzYSIsInNwaSI6Ijk4MzcwNGJhLWZjZWItNGM0ZS1iZTUzLWNhMjgwYzZjYjQ0ZiIsIm9pZCI6IjUzZTI2MjNhLWNlNjctNDhjZS05NTk2LWNkYTE4YjJhMDhhZiJ9.JHT1WOnfcCrm0ZuYItDh84TeofaB6v2U8Eos-xU0Z12XPWBmoUILjmcXLfl5QB5co6RvLcMBSzwXiWnUvr5WA0V1BIzui5g520xR6y0UOAAtbtvhK_7lb7vOf6ZAdUOSYP12UKxhr9ddDSyE_eQ_QluzBfps8GKtCvZNAF4nPRb_8CdpFjzmp1blHQHBaZQ1WLxrCS6x0u4lXfLdBnHvFOBgc6Fbuqlhz15lISj8gXuRBgzrGtTWpw04szDJ0SbBdPuoVnIiX1L7Iqif7HAplMqfL2AtKZpvbnoxP6GiDGHop6CXz0rkDacXf3yRVsE4edT35AUsWiEqVgpvglF6YQ"


import base64
import logging

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import load_der_public_key


def load_public_key(key_base64):
    """Load a public key from a Base64-encoded string."""
    try:
        # Decode the Base64 string to bytes
        key_bytes = base64.b64decode(key_base64.replace(" ", ""))
        # Load the public key
        return load_der_public_key(key_bytes, backend=default_backend())
    except Exception as e:
        logging.error(f"Error loading public key: {str(e)}")
        raise RuntimeError("Failed to load public key")

def encrypt(pan, public_key):
    """Encrypt data using RSA with OAEP padding."""
    try:
        # Load the public key
        rsa_public_key = load_public_key(public_key)

        # Encrypt the data
        encrypted_data = rsa_public_key.encrypt(
            pan.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Encode the encrypted data as Base64
        return base64.b64encode(encrypted_data).decode('utf-8')
    except Exception as e:
        logging.error(f"Exception encoding key: {str(e)}")
        raise RuntimeError("Failed encryption")



def _test():
    print("testing")


# example:
# merchant_id: "451207-smoke-tests-orb-diu"
# jwt: get from setup-checkout-intent
# api_url: "GetEncryptionKey"
# request_message: c7_fe_api.GetEncryptionKeyRequest()
# response_message: c7_fe_api.GetEncryptionKeyResponse()
def _grpc_web_call(merchant_id, jwt, api_name, request_message, response_message):
    full_url = "https://api.checkout-dev.jpmchase.com/checkout.fe.v1.CheckoutFrontendV1Service/" + api_name

    #request_message = request
    serialized_request = request_message.SerializeToString()
    # Add gRPC-Web framing (1 byte for flags, 4 bytes for length)
    # Flags: 0 for message, 1 for trailers
    # Length: Big-endian 4-byte integer
    framed_request = b'\x00' + len(serialized_request).to_bytes(4, 'big') + serialized_request
    # Base64 encode the framed request
    encoded_request = base64.b64encode(framed_request).decode('utf-8')

    token = jwt
    #merchant_id = MERCHANT_ID
    headers = {
        "Content-Type": "application/grpc-web-text+proto",
        "X-Grpc-Web": "1",
        #"Accept": "application/grpc-web-text+proto",
        "Accept": "application/grpc-web-text+proto",
        #"Accept": "*/*",
        "Locale": "en-US",
            "Authorization": "Bearer " +  token,
            "x-checkout-version": "developer_v888",
            "merchantId": merchant_id,
            "requestId": "321",
            #"content-type": "application/json"
            }
    try:
        logging.info("Request to checkout api: url=%s,\n%s, %s, %s, encoded=%s\n",
            full_url,
            request_message,
            serialized_request, framed_request, encoded_request)
        response = requests.post(full_url, headers=headers, data=encoded_request)
        logging.info("response from checkout [%s]: %s, %s", api_name, response, response.text)

        response.raise_for_status() # Raise an exception for bad status codes

        # Decode the response
        #encoded_response_body = response.content
        encoded_response_body = response.text
         # Add padding if needed
        #if len(encoded_response_body) % 4 != 0:
        #    encoded_response_body += b'=' * (4 - len(encoded_response_body) % 4)
        decoded_response_body = base64.b64decode(encoded_response_body, validate=False)
        logging.info("response from checkout [%s]: %s, content=%s, decoded=%s",
            api_name,
            response,
            encoded_response_body,
            decoded_response_body
        )

        # Parse gRPC-Web framing and Protobuf message from the response
        # This part is highly dependent on the gRPC-Web response structure
        # You would need to extract the message and potentially trailers
        # For simplicity, assuming a single message without trailers here
        flags = decoded_response_body[0]
        message_length = int.from_bytes(decoded_response_body[1:5], 'big')
        message_payload = decoded_response_body[5:5 + message_length]
        #response_message = c7_fe_api.GetEncryptionKeyResponse()
        response_message.ParseFromString(message_payload)

        print("Received response:", response_message)
        return response_message
    except requests.exceptions.RequestException as e:
        #if e.details() == "Expecting value: line 1 column 1 (char 0)":
        print(f"Raw response content (if available): {e.debug_error_string()}") # This might reveal some info
        # You might need to add logging/interceptors to get the full raw response
        print(f"Error making gRPC-Web call: {e}")


def _get_merchant_settings(merchant_id, jwt):
    req = c7_fe_api.GetMerchantSettingsRequest()
    res = c7_fe_api.GetMerchantSettingsResponse()
    _grpc_web_call(merchant_id, jwt, "GetMerchantSettings", req, res)
    logging.info("returned response: %s", res)
    return res



def _get_encryption_key(merchant_id, jwt):
    req = c7_fe_api.GetEncryptionKeyRequest()
    res = c7_fe_api.GetEncryptionKeyResponse()
    _grpc_web_call(merchant_id, jwt, "GetEncryptionKey", req, res)
    logging.info("returned response: %s", res)
    return res



def _pay(merchant_id, jwt, get_settings_resp : c7_fe_api.GetMerchantSettingsResponse):
    encryption_key = _get_encryption_key(merchant_id, jwt)

    logging.info("encrypted key: %s", encryption_key.encryption_key)

    pan = "4242424242424242"
    encrypted_pan = encrypt(pan, encryption_key.encryption_key)
    logging.info("encrypted pan: %s, %s", pan, encrypted_pan)

    encrypted_cvv = encrypt("111", encryption_key.encryption_key)
    logging.info("encrypted cvv: 111, %s", encrypted_cvv)

    pay_method = c7_fe_api.PaymentMethod(
        type=c7_fe_api.PaymentMethod.Type.TYPE_CARD,
        card=common_pb2.EncryptedCard(card_holder_name="Awsome Shoppoer",
                encrypted_pan=encrypted_pan,
                encrypted_cvv=encrypted_cvv,
                encryption_key_id=encryption_key.encryption_key_id
            )
    )

    settings = get_settings_resp.merchant_settings
    mandates = settings.order_mandates
    mlist = [m.mandate_id for m in mandates]

    card_mandate = settings.payment_methods.card_payment_method.mandate
    mlist.append(card_mandate.mandate_id)

    # Create a request message
    request_message = c7_fe_api.PayRequest(
        payment_method=pay_method,
        accepted_mandates=mlist, #["61c6be372a3d41078fa09bccfce478f7"],
        #accepted_mandates=["536dfeb97ea945488cfa5a0a07d33381", "2aa194c8c60b4a03891b32c78f2bf31e"],
        )

    #req = c7_fe_api.GetEncryptionKeyRequest()
    res = c7_fe_api.PayResponse()
    _grpc_web_call(merchant_id, jwt, "Pay", request_message, res)
    logging.info("returned response: %s", res)
    return res


def pay(merchant_id, jwt):
    get_settings_resp = _get_merchant_settings(merchant_id, jwt)
    return _pay(merchant_id, jwt, get_settings_resp)



logging.basicConfig(level=logging.INFO)


import random
import string


def generate_random_digital_string(length):
  """
  Generates a random string composed solely of digits.

  Args:
    length: The desired length of the digital string.

  Returns:
    A string containing random digits of the specified length.
  """
  return ''.join(random.choices(string.digits, k=length))

# Example usage:
#random_digits = generate_random_digital_string(10)
#print(f"Random Digital String: {random_digits}")

if __name__ == "__main__":
    _test()

    order_ref = generate_random_digital_string(10)
    _, jwt = checkout_tools._setup_intent(MERCHANT_ID, order_ref, "USD", "999")
    logging.info("checkout intent token: %s", jwt)
    pay(MERCHANT_ID, jwt)
