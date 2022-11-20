from datetime import date
from apps.products.models import PriceInterval
from datetime import timedelta


class PriceIntervalInserter:

    def __init__(self, serializer, queryset):
        self.serializer = serializer
        self.interval_data = self.serializer.validated_data
        self.queryset = queryset
        self.error_message = ''

    def is_valid_date_range(self):
        self.error_message = ''
        if not self.interval_data['end_date']:
            return True
        if self.interval_data['start_date'] <= self.interval_data['end_date']:
            return True
        self.error_message = f"Invalid date range: {self.interval_data['start_date']}>{self.interval_data['end_date']}"
        return False

    def _get_edge_interval(self, hit_date: date):
        interval = self.queryset.filter(start_date__lt=hit_date, end_date__gt=hit_date)
        if len(interval):
            return interval[0]
        return None

    def _shift_edge_intervals(self, left_interval, right_interval):
        if left_interval != right_interval:
            if left_interval:
                left_interval.end_date = self.interval_data['start_date'] - timedelta(days=1)
                left_interval.save()
            if right_interval:
                right_interval.start_date = self.interval_data['end_date'] + timedelta(days=1)
                right_interval.save()
        else:
            if left_interval:
                left_interval.end_date = self.interval_data['start_date'] - timedelta(days=1)
                left_interval.save()
                new_right_interval = PriceInterval(
                    product=right_interval.product,
                    price=right_interval.price,
                    start_date=self.interval_data['end_date'] + timedelta(days=1),
                    end_date=right_interval.end_date
                )
                new_right_interval.save()

    def _insert(self):
        # delete ranges thar are inside start_date - end_date interval, because they will be overridden
        self.queryset.filter(
            start_date__gte=self.interval_data['start_date'], end_date__lte=self.interval_data['end_date']
        ).delete()
        self.queryset = self.queryset.all()
        if len(self.queryset):
            self._shift_edge_intervals(
                left_interval=self._get_edge_interval(self.interval_data['start_date']),
                right_interval=self._get_edge_interval(self.interval_data['end_date'])
            )
        self.serializer.save()

    def _convert_null_end_date_to_max_date(self):
        last_interval = self.queryset.last()
        if not last_interval.end_date:
            last_interval.end_date = date.max
            last_interval.save()
        self.queryset = self.queryset.all()
        if not self.interval_data['end_date']:
            self.interval_data['end_date'] = date.max

    def _convert_max_date_to_null(self):
        intervals = self.queryset.filter(end_date__gte=date.max)  # equals
        for interval in intervals:
            interval.end_date = None
            interval.save()

    def insert_interval(self):
        self.queryset = self.queryset.filter(product=self.interval_data['product']).order_by('start_date')
        if not len(self.queryset):  # first price interval
            self.serializer.save()
        else:
            self._convert_null_end_date_to_max_date()
            self._insert()
            self._convert_max_date_to_null()
