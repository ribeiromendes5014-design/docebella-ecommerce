# pedidos/forms.py
from django import forms
from .models import EnderecoEntrega

class EnderecoEntregaForm(forms.ModelForm):
    class Meta:
        model = EnderecoEntrega
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Deixa apenas o campo "número" obrigatório
        campos_opcionais = ['cep', 'rua', 'bairro', 'cidade', 'estado', 'complemento']
        for campo in campos_opcionais:
            if campo in self.fields:
                self.fields[campo].required = False
                # Torna-os somente leitura (não editáveis)
                self.fields[campo].widget.attrs['readonly'] = True

        # Campo essencial
        if 'numero' in self.fields:
            self.fields['numero'].required = True
            self.fields['numero'].widget.attrs.update({
                'placeholder': 'Número da residência ou ponto de retirada',
                'class': 'form-control',
            })

        # Estiliza outros campos visíveis normalmente
        if 'nome' in self.fields:
            self.fields['nome'].widget.attrs.update({'class': 'form-control'})
        if 'email' in self.fields:
            self.fields['email'].widget.attrs.update({'class': 'form-control'})
        if 'telefone' in self.fields:
            self.fields['telefone'].widget.attrs.update({'class': 'form-control'})
