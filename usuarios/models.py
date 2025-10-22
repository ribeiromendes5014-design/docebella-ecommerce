from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _

# --- CLASSE DE MANAGER CORRIGIDA E LIMPA ---
class CustomUserManager(BaseUserManager):
    """
    Gerenciador de usuário personalizado onde o email é o identificador
    principal, em vez do username padrão do Django.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Cria e salva um usuário com o email e senha fornecidos.
        """
        if not email:
            raise ValueError(_('O Email deve ser fornecido.'))
        
        email = self.normalize_email(email)
        
        # Como herdamos de AbstractBaseUser, não precisamos lidar com o 'username'
        # e as 'extra_fields' são passadas diretamente.
        user = self.model(email=email, **extra_fields)
        
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Cria e salva um superusuário com o email e senha fornecidos.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superusuário deve ter is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superusuário deve ter is_superuser=True.'))
        
        # Chama o create_user
        return self.create_user(email, password, **extra_fields)
# -----------------------------------------------------


# --- SEU MODELO Cliente (Otimizado e CORRIGIDO) ---
class Cliente(AbstractBaseUser, PermissionsMixin):
    # Ao herdar de AbstractBaseUser + PermissionsMixin, 
    # não precisamos do campo 'username' ou dos campos ManyToMany repetidos.
    
    # Define o campo de email como único e necessário
    email = models.EmailField(_('Endereço de email'), unique=True)
    
    # Campos customizados
    nome_completo = models.CharField(_('Nome completo'), max_length=150)
    telefone = models.CharField(max_length=20, blank=True, null=True)

    # Campos necessários para o sistema de permissões e admin
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Define o campo 'email' como o campo principal de login
    USERNAME_FIELD = 'email'
    
    # Campos obrigatórios ao usar 'createsuperuser' (além de USERNAME_FIELD e password)
    REQUIRED_FIELDS = ['nome_completo']
    
    # Diz ao Django para usar o Manager customizado
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _('Cliente')
        verbose_name_plural = _('Clientes')

    def __str__(self):
        # CORREÇÃO: Usar um campo sem caracteres especiais (@, .) no lugar do email,
        # para evitar o erro Server Error (500) em reversão de URLs (como no Admin).
        return self.nome_completo

    def get_full_name(self):
        """Retorna o nome completo."""
        return self.nome_completo

    def get_short_name(self):
        """Retorna o primeiro nome (opcional, pode ser o nome completo)."""
        return self.nome_completo
