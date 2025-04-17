from rest_framework import serializers
from .models import Order, OrderItem, Payment
from products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'subtotal']
        read_only_fields = ['id', 'price']

    def get_subtotal(self, obj):
        return obj.get_subtotal()

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'status', 'status_display', 'shipping_address', 'total_price', 'items', 'created_at']
        read_only_fields = ['id', 'total_price', 'created_at']

class CreateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['shipping_address']

    def create(self, validated_data):
        user = self.context['request'].user
        cart = user.cart

        # カートが空の場合はエラー
        if not cart.items.exists():
            raise serializers.ValidationError({'error': 'カートが空です'})

        # 在庫チェック
        for cart_item in cart.items.all():
            if cart_item.quantity > cart_item.product.stock:
                raise serializers.ValidationError({
                    'error': f'{cart_item.product.name}の在庫が不足しています'
                })

        # 注文を作成
        order = Order.objects.create(
            user=user,
            shipping_address=validated_data['shipping_address'],
            total_price=cart.get_total_price()
        )

        # カートの商品を注文商品に変換
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            # 在庫を減らす
            product = cart_item.product
            product.stock -= cart_item.quantity
            product.save()

        # カートを空にする
        cart.items.all().delete()

        return order

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'amount', 'payment_method',
            'status', 'created_at'
        ]
        read_only_fields = ['status', 'created_at']

class CreatePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['payment_method'] 