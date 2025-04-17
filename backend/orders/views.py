from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.conf import settings
import stripe
from django.views.decorators.csrf import csrf_exempt

from .models import Order, Payment
from .serializers import OrderSerializer, CreateOrderSerializer, PaymentSerializer, CreatePaymentSerializer

# Stripe設定
stripe.api_key = settings.STRIPE_SECRET_KEY

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

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def process_payment(self, request, pk=None):
        """注文の支払い処理を行う"""
        order = self.get_object()
        
        # 既に支払い済みの場合
        if hasattr(order, 'payment') and order.payment.status == 'completed':
            return Response(
                {'error': '既に支払い済みです'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # シリアライザでバリデーション
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment_method = serializer.validated_data['payment_method']
        
        try:
            # 支払い情報を作成
            payment = Payment.objects.create(
                order=order,
                amount=order.calculate_total(),
                payment_method=payment_method,
                status='processing'
            )
            
            # 支払い方法に応じた処理
            if payment_method == 'card':
                # Stripeの支払いIntentを作成
                intent = stripe.PaymentIntent.create(
                    amount=payment.amount,
                    currency='jpy',
                    payment_method=request.data.get('payment_method_id'),
                    confirm=True,  # 即時決済
                    metadata={
                        'order_id': order.id,
                        'user_id': request.user.id
                    }
                )
                
                # 支払いIDを保存
                payment.stripe_payment_intent_id = intent.id
                
                if intent.status == 'succeeded':
                    payment.status = 'completed'
                    order.status = 'paid'  # 注文ステータスも更新
                else:
                    payment.status = 'failed'
                
                payment.save()
                order.save()
                
            elif payment_method in ['konbini', 'bank_transfer']:
                # コンビニ・銀行振込の場合はStripeの支払いリンクを作成
                session = stripe.checkout.Session.create(
                    payment_method_types=[payment_method],
                    line_items=[{
                        'price_data': {
                            'currency': 'jpy',
                            'product_data': {
                                'name': f'注文 #{order.id}',
                            },
                            'unit_amount': payment.amount,
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=request.build_absolute_uri(f'/orders/{order.id}/success'),
                    cancel_url=request.build_absolute_uri(f'/orders/{order.id}/cancel'),
                    metadata={
                        'order_id': order.id,
                        'user_id': request.user.id
                    }
                )
                
                return Response({
                    'session_id': session.id,
                    'session_url': session.url
                })
                
            else:
                # その他の支払い方法（PayPayなど）は今後実装
                return Response(
                    {'error': 'この支払い方法は現在対応していません'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # レスポンスを返す
            serializer = PaymentSerializer(payment)
            return Response(serializer.data)
            
        except stripe.error.CardError as e:
            # カードエラーの場合
            payment.status = 'failed'
            payment.save()
            return Response(
                {'error': settings.PAYMENT_SETTINGS['error_messages']['card_error']},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            # その他のエラー
            if 'payment' in locals():
                payment.status = 'failed'
                payment.save()
            return Response(
                {'error': settings.PAYMENT_SETTINGS['error_messages']['system_error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def payment_status(self, request, pk=None):
        """支払い状態を確認する"""
        order = self.get_object()
        
        if not hasattr(order, 'payment'):
            return Response(
                {'error': '支払い情報が存在しません'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = PaymentSerializer(order.payment)
        return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def stripe_webhook(request):
    """Stripeからのwebhookを処理する"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        # イベントの検証
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.SignatureVerificationError as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    # イベントタイプに応じた処理
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object
        
        try:
            # 支払い情報を更新
            payment = Payment.objects.get(
                stripe_payment_intent_id=payment_intent.id
            )
            with transaction.atomic():
                payment.status = 'completed'
                payment.save()
                
                # 注文ステータスも更新
                order = payment.order
                order.status = 'paid'
                order.save()
                
        except Payment.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
    elif event.type == 'checkout.session.completed':
        session = event.data.object
        
        try:
            # 注文IDをメタデータから取得
            order_id = session.metadata.get('order_id')
            order = Order.objects.get(id=order_id)
            
            # 支払い情報を更新
            payment = order.payment
            payment.status = 'completed'
            payment.save()
            
            # 注文ステータスも更新
            order.status = 'paid'
            order.save()
            
        except (Order.DoesNotExist, Payment.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)

    return Response(status=status.HTTP_200_OK)
