class PriceNotFound(Exception):

    def __init__(self, **kwargs):
        super().__init__(f"No price found for product {kwargs.get('product', '')}")
