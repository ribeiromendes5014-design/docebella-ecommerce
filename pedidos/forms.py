# pedidos/forms.py (Versão Corrigida)
from django import forms
from .models import EnderecoEntrega

class EnderecoEntregaForm(forms.ModelForm):
    class Meta:
        model = EnderecoEntrega
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Lista de campos a serem bloqueados E TORNADOS OPCIONAIS
        campos_bloqueados_opcionais = ['cep', 'rua', 'bairro', 'cidade', 'estado', 'complemento']
        
        for campo in campos_bloqueados_opcionais:
            if campo in self.fields:
                self.fields[campo].required = False
                # Torna-os somente leitura (não editáveis)
                self.fields[campo].widget.attrs['readonly'] = True
                
        # 2. Configuração do Campo ESSENCIAL (e editável)
        if 'numero' in self.fields:
            self.fields['numero'].required = True # Deve ser obrigatório
            # IMPORTANTE: REMOVA QUALQUER 'readonly' AQUI SE EXISTIR
            if 'readonly' in self.fields['numero'].widget.attrs:
                del self.fields['numero'].widget.attrs['readonly']

            self.fields['numero'].widget.attrs.update({
                'placeholder': 'Número da residência ou ponto de retirada',
                'class': 'form-control',
            })

        # 3. Estiliza e garante que os campos de contato (nome, email, telefone) não estejam bloqueados
        # Eles assumem as regras do modelo (ex: 'required = True' se for o caso)
        campos_contato = ['nome', 'email', 'telefone']
        for campo in campos_contato:
             if campo in self.fields:
                self.fields[campo].widget.attrs.update({'class': 'form-control'})
                if 'readonly' in self.fields[campo].widget.attrs:
                    del self.fields[campo].widget.attrs['readonly']
