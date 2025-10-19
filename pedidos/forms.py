# pedidos/forms.py (CRIE ESTE ARQUIVO SE ELE NÃO EXISTIR)

from django import forms
from .models import EnderecoEntrega

class EnderecoEntregaForm(forms.ModelForm):
    class Meta:
        model = EnderecoEntrega
        fields = '__all__'
    
    # Sobrescreve a inicialização para garantir que os campos são opcionais
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Desliga a obrigatoriedade (required=True) para os campos de endereço
        self.fields['cep'].required = False
        self.fields['rua'].required = False
        self.fields['numero'].required = False
        self.fields['bairro'].required = False
        self.fields['cidade'].required = False
        self.fields['estado'].required = False
        
        # Se você quiser que "Sobrenome" também seja opcional
        # self.fields['sobrenome'].required = False
