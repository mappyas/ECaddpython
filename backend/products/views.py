from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer

# Create your views here.

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all() # 全てのカテゴリーを取得
    serializer_class = CategorySerializer # カテゴリーのシリアライザーを使用
    permission_classes = [permissions.IsAuthenticated] # 認証されたユーザーのみがアクセスできる

    @action(detail=True, methods=['get']) # 詳細なデータを取得するためのアクション　detail=TrueはカテゴリーのIDを取得するためのアクション
    def products(self, request, pk=None): # カテゴリーのIDを取得
        category = self.get_object() # カテゴリーのオブジェクトを取得   
        products = category.products.all() # カテゴリーに紐づく商品を取得
        serializer = ProductSerializer(products, many=True) # 商品のシリアライザーを使用
        return Response(serializer.data) # 商品のデータを返す

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'stock', 'price']

    def get_queryset(self):
        queryset = Product.objects.all()
        in_stock = self.request.query_params.get('in_stock', None)
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)

        if in_stock == 'true':
            queryset = queryset.filter(stock__gt=0)
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        return queryset
