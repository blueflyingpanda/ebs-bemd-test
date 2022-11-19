from django.db.models import Q
from apps.products.models import PriceInterval
from apps.products.utils.exceptions import PriceNotFound
from dataclasses import dataclass
from datetime import timedelta


@dataclass
class AverageInfo:
    price: float
    days: int


class AveragePriceCounter:

    def __init__(self, price_inquiry: dict):
        self.price_inquiry: dict = price_inquiry
        self._selected_records = None

    @property
    def selected_records(self):
        if not self._selected_records:
            self._selected_records = PriceInterval.objects.select_related('product').filter(
                product=self.price_inquiry['product'],
            ).filter(
                Q(end_date__gte=self.price_inquiry['start_date']) | Q(end_date__isnull=True),
                start_date__lte=self.price_inquiry['end_date']
            )
        return self._selected_records

    def get_average(self) -> AverageInfo:
        price_sum = 0
        days_sum = 0
        if not self.selected_records:
            raise PriceNotFound(product=self.price_inquiry['product'].name)
        for price in self.selected_records:
            if not price.end_date:
                price.end_date = self.price_inquiry['end_date']
            start_date = price.start_date if price.start_date > self.price_inquiry['start_date'] \
                else self.price_inquiry['start_date']
            end_date = price.end_date if price.end_date < self.price_inquiry['end_date'] \
                else self.price_inquiry['end_date']
            days = end_date - start_date
            price_sum += price.price * days.days
            days_sum += days.days
        return AverageInfo(price_sum / days_sum, days_sum)
