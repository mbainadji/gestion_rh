from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # Essayer de trouver par email ou username
            user = UserModel.objects.get(Q(username=username) | Q(email=username))
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            return None
