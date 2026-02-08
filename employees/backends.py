from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        from .models import Employe
        
        # 1. Essayer par username ou email (insensible à la casse pour l'email)
        user = None
        try:
            user = UserModel.objects.get(Q(username=username) | Q(email__iexact=username))
        except UserModel.DoesNotExist:
            # 2. Essayer par matricule via le profil Employe
            try:
                employe = Employe.objects.get(matricule=username)
                user = employe.user
            except (Employe.DoesNotExist, AttributeError):
                return None
        except UserModel.MultipleObjectsReturned:
            # Si plusieurs utilisateurs ont le même email, on prend le premier (peu probable avec unique=True)
            user = UserModel.objects.filter(email__iexact=username).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
