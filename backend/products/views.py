from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, Category, Cart, CartItem
from .serializers import ProductSerializer, CategorySerializer, CartSerializer, CartItemSerializer

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

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': '商品が見つかりません'}, status=status.HTTP_404_NOT_FOUND)

        if product.stock < quantity:
            return Response({'error': '在庫が不足しています'}, status=status.HTTP_400_BAD_REQUEST)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product_id')

        try:
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
            cart_item.delete()
        except CartItem.DoesNotExist:
            return Response({'error': 'カートに商品がありません'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_quantity(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')

        try:
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
            product = cart_item.product

            if product.stock < quantity:
                return Response({'error': '在庫が不足しています'}, status=status.HTTP_400_BAD_REQUEST)

            cart_item.quantity = quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            return Response({'error': 'カートに商品がありません'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CartSerializer(cart)
        return Response(serializer.data)
