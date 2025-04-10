from django.db import models
from django.core.validators import MinValueValidator

class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name='商品名')
    description = models.TextField(verbose_name='商品説明')
    price = models.PositiveIntegerField(verbose_name='価格', validators=[MinValueValidator(1)])
    stock = models.PositiveIntegerField(verbose_name='在庫数', default=0)
    image = models.ImageField(upload_to='products/', verbose_name='商品画像', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    class Meta:
        verbose_name = '商品'
        verbose_name_plural = '商品'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def is_in_stock(self):
        return self.stock > 0
