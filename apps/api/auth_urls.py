from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from . import auth_views

urlpatterns = [
    # JWT токены
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Регистрация и профиль
    path('register/', auth_views.RegisterView.as_view(), name='register'),
    path('profile/', auth_views.ProfileView.as_view(), name='profile'),
    path('profile/update/', auth_views.UpdateProfileView.as_view(), name='update_profile'),
    path('change-password/', auth_views.ChangePasswordView.as_view(), name='change_password'),
    
    # Сброс пароля
    path('password-reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    
    # Подтверждение email (если используется)
    path('email-verification/', auth_views.EmailVerificationView.as_view(), name='email_verification'),
    
    # Выход (blacklist токена)
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
