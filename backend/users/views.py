"""主な機能:ユーザー登録の処理、ログイン認証、セッション管理、エラーハンドリング、レスポンスの生成
Next.jsとの連携:Next.jsからのリクエストを受け取る処理結果をJSON形式で返す、セッション情報を管理
つまり、views.pyはフロントエンド(Next.js)とバックエンド(Django)の橋渡し役として、ユーザー認証の中心的な処理を担当しています。"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth import login as django_login, logout as django_logout
from .serializers import UserSerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):    # ユーザー登録
        serializer = UserSerializer(data=request.data) # リクエストデータをシリアライズ
        if serializer.is_valid(): # バリデーションチェック　必須項目が入力されているか
            user = serializer.save() # ユーザーを保存
            django_login(request, user) # ログイン　requestにはフロントから送られたデータが入っている
            return Response(serializer.data, status=status.HTTP_201_CREATED) # レスポンスを返す
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) # エラーハンドリング 

    @action(detail=False, methods=['post'])
    def login_api(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                django_login(request, user)
                return Response(UserSerializer(user).data)
            return Response({'error': 'Invalid password'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        django_logout(request)
        return Response({'message': 'Logged out successfully'}) 