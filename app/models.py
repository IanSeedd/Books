from django.db import models
from django.conf import settings
import shutil
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.utils.text import slugify
from decimal import Decimal
from multiselectfield import MultiSelectField
import os

# OBS: Futuramente os serviços externos farão isso automáticamente
# Função para definir o caminho do upload pelo ID
def caminho_livro(instance, filename):
    # Primeiro upload: usa o slug temporariamente porque o ID ainda não existe
    # Se já existir ID (edição), usa o ID
    pasta = instance.id if instance.id else f"temp_{slugify(instance.titulo)}"
    return os.path.join('media', str(pasta), filename)

class Livros(models.Model):
    titulo = models.CharField(max_length=200)
    # Valor slug para o link do livro personalizado
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    autor = models.CharField(max_length=100)
    editora = models.CharField(max_length=100)
    data_de_publicacao = models.DateField()
    descricao = models.TextField(max_length=500)
    preco = models.DecimalField(
        max_digits=6,
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
        )
    STATUS_CHOICES = [
        ('capa-dura', 'Capa Dura'),
        ('impressão-especial', 'Impressão Especial'), 
        ('contra-capa', 'Contra Capa')
    ]
    especial = MultiSelectField(
        max_length=25,
        choices = STATUS_CHOICES,
        null = True,
        blank = True,
        default=None
    )
    capa = models.ImageField(
        upload_to=caminho_livro,
        # Formatos aceitos:
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'webm', 'png'])]
        )
    video_demonstracao = models.FileField(
        upload_to=caminho_livro,
        null=True, 
        blank=True,
        # Formatos aceitos:
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'webm', 'mov'])]
    )
    # Campo para saber se o livro foi vendido
    vendido = models.BooleanField(default=False)
    

    def save(self, *args, **kwargs):
            # 1. Garante o slug
            self.slug = slugify(self.titulo)
            
            # 2. Lógica para limpeza de arquivos antigos (substituição)
            if self.pk:
                antigo = Livros.objects.get(pk=self.pk)
                if antigo.capa and self.capa and antigo.capa != self.capa:
                    if os.path.isfile(antigo.capa.path): os.remove(antigo.capa.path)
                if antigo.video_demonstracao and self.video_demonstracao and antigo.video_demonstracao != self.video_demonstracao:
                    if os.path.isfile(antigo.video_demonstracao.path): os.remove(antigo.video_demonstracao.path)

            # 3. Salva os dados (Aqui o ID é gerado se for novo)
            is_new = self.pk is None
            super().save(*args, **kwargs)

            # 4. A MÁGICA: Se for novo, move da pasta temp para a pasta ID
            if is_new:
                old_path = os.path.join(settings.MEDIA_ROOT, 'livros', f"temp_{self.slug}")
                new_path = os.path.join(settings.MEDIA_ROOT, 'livros', str(self.id))
                
                if os.path.exists(old_path):
                    # Se a pasta de destino já existir por erro, removemos
                    if os.path.exists(new_path): shutil.rmtree(new_path)
                    
                    os.rename(old_path, new_path)
                    
                    # Atualiza os caminhos no objeto para apontar para a pasta com ID
                    if self.capa:
                        self.capa.name = self.capa.name.replace(f"temp_{self.slug}", str(self.id))
                    if self.video_demonstracao:
                        self.video_demonstracao.name = self.video_demonstracao.name.replace(f"temp_{self.slug}", str(self.id))
                    
                    # Salva novamente apenas os campos de arquivo para atualizar o banco
                    super().save(update_fields=['capa', 'video_demonstracao'])

    def __str__(self):
        return self.titulo