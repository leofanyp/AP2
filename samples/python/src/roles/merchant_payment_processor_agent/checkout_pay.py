import logging

from roles.merchant_agent import checkout_tools

from ap2.types.mandate import CartMandate


logging.basicConfig(level=logging.INFO)


def pay(cart_mandate: CartMandate):
    return checkout_tools.confirm_checkout(cart_mandate)


if __name__ == '__main__':
    import random
    import string

    def generate_random_digital_string(length):
        """Generates a random string composed solely of digits.

        Args:
            length: The desired length of the digital string.

        Returns:
            A string containing random digits of the specified length.
        """
        return ''.join(random.choices(string.digits, k=length))

    # Example usage:
    # random_digits = generate_random_digital_string(10)
    # print(f"Random Digital String: {random_digits}")

    order_ref = generate_random_digital_string(10)
    checkout_tools._setup_intent(
        '999959695028-smoke-tests-upg-diu', order_ref, 'USD', '999'
    )
    checkout_tools._confirm_checkout(
        '999959695028-smoke-tests-upg-diu', order_ref
    )
