import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

import requests
from ap2.types.mandate import CartMandate


# Configuration
HTTP_PROXY = "http://proxy.jpmchase.net:8443"
PROXIES = {
    "http": HTTP_PROXY,
    "https": HTTP_PROXY
}
DEFAULT_MID = "999959695028-smoke-tests-upg-diu"

# API Endpoints
TOKEN_URL = "https://api.checkout-dev.jpmchase.com/ms-api/v2/token/plain?type=merchant"
PAYMENT_LINKS_URL = "https://merchant-api.checkout-dev.jpmchase.com/v1/payment-links"
CHECKOUT_INTENT_URL = "https://merchant-api.checkout-dev.jpmchase.com/v1/checkout/intent"
CHECKOUT_CONFIRM_URL = "https://merchant-api.checkout-dev.jpmchase.com/v1/checkout/intent/confirm"

# Default values
DEFAULT_CUSTOMER_EMAIL = "customer@jpmchase.com"
DEFAULT_CURRENCY = "USD"
DEFAULT_REQUEST_ID = "321"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CheckoutError(Exception):
    """Custom exception for checkout operations."""
    pass


def get_token(merchant_id: str) -> bytes:
    """Get authentication token for the merchant.

    Args:
        merchant_id: The merchant identifier

    Returns:
        The authentication token as bytes

    Raises:
        CheckoutError: If token retrieval fails
    """
    try:
        headers = {"x-checkout-merchant-id": merchant_id}
        response = requests.get(TOKEN_URL, headers=headers, proxies=PROXIES, timeout=30)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        logger.error(f"Failed to get token for merchant {merchant_id}: {e}")
        raise CheckoutError(f"Token retrieval failed: {e}")


def generate_order_number() -> str:
    """Generate a unique order number using UUID.

    Returns:
        A 16-character hexadecimal string
    """
    return uuid.uuid4().hex[:16]


def _lookup_merchant(merchant_name: str) -> str:
    """Lookup merchant ID by merchant name.

    Args:
        merchant_name: The name of the merchant

    Returns:
        The merchant ID

    Note:
        Currently returns the default merchant ID. This should be implemented
        to perform actual merchant lookup.
    """
    # TODO: Implement actual merchant lookup logic
    logger.info(f"Looking up merchant ID for: {merchant_name}")
    return DEFAULT_MID


def create_payment_link(
    merchant_id: str,
    product_name: str,
    unit_price: int,
    quantity: int = 1
) -> requests.Response:
    """Create a payment link for the given product.

    Args:
        merchant_id: The merchant identifier
        product_name: Name of the product
        unit_price: Price per unit in cents
        quantity: Number of items (default: 1)

    Returns:
        The HTTP response from the payment link creation request

    Raises:
        CheckoutError: If payment link creation fails
    """
    try:
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
            "currencyCode": DEFAULT_CURRENCY,
            "totalTransactionAmount": quantity * unit_price
        }

        token = get_token(merchant_id)
        headers = {
            "authorization": token,
            "x-checkout-version": "developer",
            "merchantId": merchant_id
        }

        logger.info(f"Creating payment link for product: {product_name}")
        response = requests.post(
            PAYMENT_LINKS_URL,
            headers=headers,
            json=body,
            proxies=PROXIES,
            timeout=30
        )
        response.raise_for_status()
        return response

    except requests.RequestException as e:
        logger.error(f"Failed to create payment link: {e}")
        raise CheckoutError(f"Payment link creation failed: {e}")


def _setup_intent(
    merchant_id: str,
    cart_id: str,
    currency: str,
    value: int
) -> Tuple[str, str]:
    """Setup checkout intent with the given parameters.

    Args:
        merchant_id: The merchant identifier
        cart_id: The cart/order identifier
        currency: The currency code (e.g., 'USD')
        value: The transaction amount in cents

    Returns:
        A tuple of (merchant_id, jwt_token)

    Raises:
        CheckoutError: If intent setup fails
    """
    logger.info("=" * 32)
    logger.info("Setting up checkout intent...")
    logger.info("=" * 32)

    try:
        body = {
            "merchantOrderNumber": cart_id,
            "currencyCode": currency,
            "cart": {
                "totalTransactionAmount": value
                # TODO: Add shipping address support
            },
            "consumer": {
                "email": DEFAULT_CUSTOMER_EMAIL
                # TODO: Add billing address support
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
        headers = {
            "authorization": f"Bearer {token.decode('utf-8')}",
            "x-checkout-version": "developer",
            "merchantId": merchant_id,
            "requestId": DEFAULT_REQUEST_ID,
            "content-type": "application/json"
        }

        logger.debug(f"Request headers: {headers}")
        logger.debug(f"Request body: {json.dumps(body, indent=2)}")

        response = requests.post(
            CHECKOUT_INTENT_URL,
            headers=headers,
            json=body,
            timeout=30
        )
        response.raise_for_status()

        response_data = response.json()
        logger.info(f"Checkout intent setup successful: {response.status_code}, data: {json.dumps(response_data, indent=2)}")

        jwt_token = response_data.get("checkoutSessionToken")
        if not jwt_token:
            raise CheckoutError("No checkout session token in response")

        return merchant_id, jwt_token

    except requests.RequestException as e:
        logger.error(f"Failed to setup checkout intent: {e}")
        raise CheckoutError(f"Intent setup failed: {e}")
    except KeyError as e:
        logger.error(f"Missing expected field in response: {e}")
        raise CheckoutError(f"Invalid response format: {e}")


def setup_intent(cart_mandate: CartMandate) -> Tuple[str, str]:
    """Setup checkout intent from cart mandate.

    Args:
        cart_mandate: The cart mandate containing payment details

    Returns:
        A tuple of (merchant_id, jwt_token)

    Raises:
        CheckoutError: If intent setup fails
    """
    logger.info("=" * 50)
    logger.info("Setting up checkout intent from cart mandate")
    logger.info("=" * 50)

    try:
        cart_id = cart_mandate.contents.id
        payment_request = cart_mandate.contents.payment_request
        currency = payment_request.details.total.amount.currency
        value = int(payment_request.details.total.amount.value * 100)
        merchant_id = _lookup_merchant(cart_mandate.contents.merchant_name)

        # Generate timestamp-based order reference
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        order_ref = f"ref{timestamp}"

        logger.info(f"Cart ID: {cart_id}")
        logger.info(f"Currency: {currency}")
        logger.info(f"Amount: {value} cents")
        logger.info(f"Order Reference: {order_ref}")

        return _setup_intent(merchant_id, order_ref, currency, value)

    except AttributeError as e:
        logger.error(f"Invalid cart mandate structure: {e}")
        raise CheckoutError(f"Invalid cart mandate: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in setup_intent: {e}")
        raise CheckoutError(f"Setup intent failed: {e}")


def confirm_checkout(merchant_id: str, cart_id: str) -> Dict[str, Any]:
    """Confirm checkout intent with payment details.

    Args:
        merchant_id: The merchant identifier
        cart_id: The cart/order identifier

    Returns:
        The response data from the checkout confirmation

    Raises:
        CheckoutError: If checkout confirmation fails
    """
    logger.info("=" * 50)
    logger.info("Confirming checkout intent")
    logger.info("=" * 50)

    try:
        # Test card details - in production, this would come from user input
        body = {
            "merchantOrderNumber": cart_id,
            "paymentMethodType": {
                "card": {
                    "accountNumberType": "PAN",
                    "accountNumber": "4444444444444455",  # Test card number
                    "expiry": {
                        "month": 12,
                        "year": 2026
                    },
                    "cvv": "123"
                }
            }
        }

        token = get_token(merchant_id)
        headers = {
            "authorization": f"Bearer {token.decode('utf-8')}",
            "x-checkout-version": "developer",
            "merchantId": merchant_id,
            "requestId": DEFAULT_REQUEST_ID,
            "content-type": "application/json"
        }

        logger.info(f"Confirming checkout for cart: {cart_id}")
        logger.info(f"Request headers: {headers}")
        logger.info(f"Request body: {json.dumps(body, indent=2)}")

        response = requests.post(
            CHECKOUT_CONFIRM_URL,
            headers=headers,
            json=body,
            timeout=30
        )
        response.raise_for_status()

        response_data = response.json()
        logger.info(f"Checkout confirmation successful: {response.status_code}")
        logger.info(f"Response: {json.dumps(response_data, indent=2)}")

        return response_data

    except requests.RequestException as e:
        logger.error(f"Failed to confirm checkout: {e}")
        raise CheckoutError(f"Checkout confirmation failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in confirm_checkout: {e}")
        raise CheckoutError(f"Checkout confirmation failed: {e}")


def init_pay(merchant_id: str, jwt: str) -> None:
    """Initialize payment process.

    Args:
        merchant_id: The merchant identifier
        jwt: The JWT token from checkout session

    Note:
        Currently a placeholder function. Should be implemented to
        handle the actual payment initialization.
    """
    # TODO: Implement actual payment initialization
    # checkout_grpc_web.pay(merchant_id, jwt)
    logger.info(f"Payment initialization for merchant {merchant_id} - currently no-op")


def main() -> None:
    """Main function for testing purposes."""
    try:
        logger.info("Starting checkout tools test")

        # Test setup intent
        merchant_id, jwt = _setup_intent(
            "999959695028-smoke-tests-upg-diu",
            "test123",
            DEFAULT_CURRENCY,
            99900  # $999.00 in cents
        )
        logger.info(f"Setup intent successful: {merchant_id}, JWT: {jwt[:20]}...")

        # Test confirm checkout
        result = confirm_checkout("999959695028-smoke-tests-upg-diu", "test123")
        logger.info(f"Confirm checkout successful: {result.get('status', 'Unknown status')}")

    except CheckoutError as e:
        logger.error(f"Checkout operation failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
