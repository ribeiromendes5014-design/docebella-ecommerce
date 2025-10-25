# G:\projeto\usuarios\forms.py

from django import forms
# Importa o AuthenticationForm padrão para criar o nosso form de login customizado
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm 

# Importe o seu modelo de usuário customizado
from .models import Cliente 

# =========================================================================
# 1. FORMULÁRIO DE CADASTRO (CadastroClienteForm)
# =========================================================================

class CadastroClienteForm(UserCreationForm):
    # Campos extras que não estão no UserCreationForm padrão:
    nome_completo = forms.CharField(max_length=150, required=True, 
                                    label='Nome completo',
                                    widget=forms.TextInput(attrs={'placeholder': 'ex.: Maria Perez', 'class': 'custom-input'}))
    
    # 🚨 CORREÇÃO: Aumentar max_length para acomodar 27 caracteres ou mais
    # (20 caracteres é muito pouco para telefone com máscara ou código de país)
    telefone = forms.CharField(max_length=30, required=False, 
                               label='Telefone (opcional)',
                               widget=forms.TextInput(attrs={'placeholder': 'ex.: 11971923030', 'class': 'custom-input'}))

    class Meta(UserCreationForm.Meta):
        # Use o seu modelo de usuário
        model = Cliente 
        
        # Inclua todos os campos que você deseja no formulário.
        # As senhas (password1 e password2) são herdadas automaticamente do UserCreationForm.
        # Se você definiu USERNAME_FIELD = 'email', não inclua 'username' na lista de fields.
        fields = ('nome_completo', 'email', 'telefone') 
        
    def save(self, commit=True):
        # Chama o save() da classe pai (UserCreationForm) que lida com o hashing de senha.
        user = super().save(commit=False)
        
        # 🚨 ADIÇÃO: Se o seu modelo de usuário Cliente ainda requer o campo 'username'
        # e você está usando 'email' para logar, você deve preencher 'username'
        # com o valor do 'email' antes de salvar.
        # Isso é necessário apenas se o seu modelo Cliente ainda tiver um campo 'username'
        # e o USERNAME_FIELD no settings.py estiver definido como 'email'.
        user.username = self.cleaned_data["email"] 
        
        if commit:
            user.save()
        return user

# =========================================================================
# 2. FORMULÁRIO DE LOGIN (LoginForm) - NECESSÁRIO PARA AUTENTICAR POR E-MAIL
# =========================================================================

class LoginForm(AuthenticationForm):
    # O AuthenticationForm padrão usa o campo 'username'.
    # Aqui, nós o redefinimos para se comportar como um campo de 'E-mail'.
    username = forms.EmailField(
        label="E-mail",
        max_length=254,
        widget=forms.EmailInput(attrs={'autofocus': True, 'class': 'custom-input', 'placeholder': 'seu-email@email.com.br'})
    )
    
    # Redefinimos a senha para aplicar classes CSS customizadas, se necessário.
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'custom-input', 'placeholder': 'sua senha'})
    )

    # Nota: Não é necessário um método 'clean' ou 'save' aqui, pois 
    # a autenticação é feita na view com 'authenticate()'.

# =========================================================================
# 3. FORMULÁRIO DE EDIÇÃO (ClienteChangeForm)
# =========================================================================

class ClienteChangeForm(UserChangeForm):
    class Meta:
        # Use o seu modelo de usuário
        model = Cliente 
        fields = ('nome_completo', 'email', 'telefone', 'is_active', 'is_staff')