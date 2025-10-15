from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .serializers import UserProfileSerializer
from apps.common.utils import send_notification_email

User = get_user_model()

class RegisterView(APIView):
    """Регистрация нового пользователя"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        data = request.data
        
        # Валидация обязательных полей
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {'error': f'{field} is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Проверка уникальности username и email
        if User.objects.filter(username=data['username']).exists():
            return Response(
                {'error': 'Username already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=data['email']).exists():
            return Response(
                {'error': 'Email already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Валидация пароля
        try:
            validate_password(data['password'])
        except ValidationError as e:
            return Response(
                {'error': list(e.messages)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создание пользователя
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            organization=data.get('organization', ''),
            country=data.get('country', ''),
            role=User.Role.USER
        )
        
        # Отправка приветственного письма
        send_notification_email(
            user=user,
            subject='Welcome to BRICS AI Registry',
            template_name='welcome',
            context={'user': user}
        )
        
        # Генерация JWT токенов
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'User created successfully',
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'user': UserProfileSerializer(user, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)

class ProfileView(APIView):
    """Получение профиля текущего пользователя"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)

class UpdateProfileView(APIView):
    """Обновление профиля пользователя"""
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request):
        serializer = UserProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'user': serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    """Смена пароля"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        data = request.data
        
        # Проверка старого пароля
        if not user.check_password(data.get('current_password')):
            return Response(
                {'error': 'Current password is incorrect'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Валидация нового пароля
        new_password = data.get('new_password')
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response(
                {'error': list(e.messages)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Смена пароля
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password changed successfully'})

class LogoutView(APIView):
    """Выход (добавление токена в blacklist)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Successfully logged out'})
        except Exception as e:
            return Response(
                {'error': 'Invalid token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class EmailVerificationView(APIView):
    """Подтверждение email (заглушка для будущей реализации)"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        # Здесь будет логика подтверждения email
        return Response({'message': 'Email verification not implemented yet'})
