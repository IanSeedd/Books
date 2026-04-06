from django import forms
from .models import Livro
from django.core.exceptions import ValidationError
import os

class LivroForm(forms.ModelForm):
    # Substituindo campos com widgets personalizados
    descricao = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'maxlength': 8900}),
        help_text=f"Máximo de 8900 caracteres. Restam <span id='char_count'>8900</span>"
    )
    categoria = forms.MultipleChoiceField(
        choices=Livro.STATUS_CHOICES_CATEGORIA,
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )
    caracteristicas = forms.MultipleChoiceField(
        choices=Livro.STATUS_CHOICES_CARACTERISTICAS,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Livro
        fields = ['titulo', 'autor', 'editora', 'descricao', 'preco',
                  'categoria', 'caracteristicas', 'capa', 'video_demonstracao', 'vendido']
        widgets = {
            'preco': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'vendido': forms.CheckboxInput(),
        }

    def clean_capa(self):
        capa = self.cleaned_data.get('capa')
        if capa:
            ext = os.path.splitext(capa.name)[1].lower()
            if ext not in ['.jpg', '.webp', '.png', '.jpeg']:
                raise ValidationError('Formato de imagem não suportado. Use JPG, WEBP ou PNG.')
        return capa

    def clean_video_demonstracao(self):
        video = self.cleaned_data.get('video_demonstracao')
        if video:
            ext = os.path.splitext(video.name)[1].lower()
            if ext not in ['.mp4', '.webm', '.mov']:
                raise ValidationError('Formato de vídeo não suportado. Use MP4, WEBM ou MOV.')
        return video