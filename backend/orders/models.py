from django.db import models
from django.conf import settings
from products.models import Product

class Order(models.Model):
    STATUS_CHOICES = [  # 注文状態の選択肢
        ('pending', '支払い待ち'),
        ('paid', '支払い済み'),
        ('preparing', '発送準備中'),
        ('shipped', '発送済み'),
        ('delivered', '配達済み'),
        ('cancelled', 'キャンセル済み'),
    ]
    # ユーザーとの関連付け
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  
        on_delete=models.CASCADE, 
        related_name='orders',    
        verbose_name='ユーザー'  
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='注文状態'
    )
    shipping_address = models.TextField(verbose_name='配送先住所')
    total_price = models.PositiveIntegerField(verbose_name='合計金額')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='注文日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    class Meta:
        verbose_name = '注文'
        verbose_name_plural = '注文'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    def calculate_total(self):
        """注文内の商品の合計金額を計算"""
        return sum(item.get_subtotal() for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='注文'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,  # 商品が削除されても注文履歴は保持
        verbose_name='商品'
    )
    quantity = models.PositiveIntegerField(verbose_name='数量')
    price = models.PositiveIntegerField(verbose_name='購入時の価格')  # 購入時の価格を保存
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')

    class Meta:
        verbose_name = '注文商品'
        verbose_name_plural = '注文商品'

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.id}"

    def get_subtotal(self):
        """小計を計算"""
        return self.price * self.quantity
