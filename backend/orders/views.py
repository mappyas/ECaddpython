from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Order
from .serializers import OrderSerializer, CreateOrderSerializer

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateOrderSerializer
        return OrderSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """注文をキャンセルする"""
        order = self.get_object()
        
        # すでにキャンセル済みの場合
        if order.status == 'cancelled':
            return Response(
                {'error': 'すでにキャンセルされています'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 発送済みの場合はキャンセル不可
        if order.status in ['shipped', 'delivered']:
            return Response(
                {'error': '発送済みの注文はキャンセルできません'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 在庫を戻す
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()

        # 注文をキャンセル
        order.status = 'cancelled'
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data)
