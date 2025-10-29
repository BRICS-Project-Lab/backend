from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class BurstRateThrottle(UserRateThrottle):
    """Ограничение для пиковых нагрузок"""
    # scope = 'burst'
    pass

class SustainedRateThrottle(UserRateThrottle):
    """Ограничение для продолжительных нагрузок"""
    # scope = 'sustained'
    pass

class LoginRateThrottle(AnonRateThrottle):
    """Ограничение для попыток входа"""
    # scope = 'login'
    pass

# Настройки в settings.py:
# REST_FRAMEWORK = {
#     'DEFAULT_THROTTLE_RATES': {
#         'anon': '100/hour',
#         'user': '1000/hour',
#         'burst': '60/min',
#         'sustained': '1000/day',
#         'login': '5/min'
#     }
# }
