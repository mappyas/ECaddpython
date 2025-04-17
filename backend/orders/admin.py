from django.contrib import admin
from .models import Order, OrderItem, Payment

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['payment_method', 'amount', 'status', 'stripe_payment_intent_id', 'created_at']
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'created_at', 'get_total', 'get_payment_status']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'user__email']
    readonly_fields = ['user', 'created_at', 'updated_at']
    inlines = [OrderItemInline, PaymentInline]
    
    def get_total(self, obj):
        return f'¥{obj.calculate_total():,}'
    get_total.short_description = '合計金額'
    
    def get_payment_status(self, obj):
        if hasattr(obj, 'payment'):
            return obj.payment.get_status_display()
        return '-'
    get_payment_status.short_description = '支払い状態'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'amount', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order__id', 'stripe_payment_intent_id']
    readonly_fields = ['order', 'amount', 'payment_method', 'stripe_payment_intent_id', 'created_at', 'updated_at']
    
    def has_add_permission(self, request):
        return False  # 手動での追加を禁止
