from drf_util.views import BaseViewSet, BaseCreateModelMixin, BaseListModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from logging import getLogger
from apps.products.models import Product, PriceInterval
from apps.products.serializers import ProductSerializer, PriceIntervalSerializer, ProductStatsSerializer
from apps.products.utils.average_price_counter import AveragePriceCounter
from apps.products.utils.price_interval_inserter import PriceIntervalInserter
from apps.products.utils.exceptions import PriceNotFound


logger = getLogger('info')


class ProductViewSet(BaseListModelMixin, BaseCreateModelMixin, BaseViewSet):
    permission_classes = AllowAny,
    authentication_classes = ()
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    @action(detail=False, methods=['GET'])
    def get_stats(self, request, *args, **kwargs):
        serializer = ProductStatsSerializer(data=request.query_params)

        if not serializer.is_valid():
            logger.error(f'Invalid request input data: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        avr_counter = AveragePriceCounter(serializer.validated_data)
        try:
            return Response({"average price": avr_counter.get_average()}, status=status.HTTP_200_OK)
        except PriceNotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    # todo atomic
    # todo select for update
    # todo celery tasks
    # todo auth


class ProductPriceViewSet(BaseListModelMixin, BaseCreateModelMixin, BaseViewSet):
    permission_classes = AllowAny,
    authentication_classes = ()
    serializer_class = PriceIntervalSerializer
    queryset = PriceInterval.objects.all()

    def create(self, request, return_instance=False, *args, **kwargs):

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            logger.error(f'Invalid request input data: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        interval_inserter = PriceIntervalInserter(serializer, self.queryset)
        if not interval_inserter.is_valid_date_range():
            logger.error(interval_inserter.error_message)
            return Response({"error": interval_inserter.error_message}, status=status.HTTP_400_BAD_REQUEST)

        interval_inserter.insert_interval()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
