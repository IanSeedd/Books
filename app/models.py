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

class Livro(models.Model):
    titulo = models.CharField(max_length=200)
    # Valor slug para o link do livro personalizado
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    autor = models.CharField(max_length=100)
    editora = models.CharField(max_length=100)
    descricao = models.TextField(max_length=8900)
    preco = models.DecimalField(
        max_digits=6,
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
        )
    STATUS_CHOICES_CARACTERISTICAS = [
        ('capa-dura', 'Capa Dura'),
        ('impressão-especial', 'Impressão Especial'), 
        ('contra-capa', 'Contra Capa')
    ]
    STATUS_CHOICES_CATEGORIA = [
        ('artes', 'Design + Arte + Tattoo'),
        ('nerd', 'Quadrinhos + Nerdices'),
        ('estudos', 'História + Sociologia + Filosofia + Linguística'),
        ('brumed', 'Bruxaria + Meditação'),
        ('erotica', 'Erótica'),
    ]
    categoria = MultiSelectField(
        max_length=200,
        choices = STATUS_CHOICES_CATEGORIA,
        null = True,
        blank = True,
        default=None
    )

    caracteristicas = MultiSelectField(
        max_length=100,
        choices = STATUS_CHOICES_CARACTERISTICAS,
        null = True,
        blank = True,
        default=None
    )
    capa = models.ImageField(
        upload_to=caminho_livro,
        # Formatos aceitos:
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'webp', 'png'])]
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
            self.slug = slugify(self.titulo)
            
            if self.pk:
                antigo = Livro.objects.get(pk=self.pk)
                if antigo.capa and self.capa and antigo.capa != self.capa:
                    if os.path.isfile(antigo.capa.path): os.remove(antigo.capa.path)
                if antigo.video_demonstracao and self.video_demonstracao and antigo.video_demonstracao != self.video_demonstracao:
                    if os.path.isfile(antigo.video_demonstracao.path): os.remove(antigo.video_demonstracao.path)

            is_new = self.pk is None
            super().save(*args, **kwargs)

            if is_new:
                # Pegamos o caminho base da pasta temporária usando o slug gerado
                pasta_temp_nome = f"temp_{self.slug}"
                # IMPORTANTE: Verifique se no seu caminho_livro você está usando 'livros' ou direto 'media'
                # Ajustei para bater com a sua estrutura de pastas da imagem:
                old_path = os.path.join(settings.MEDIA_ROOT, 'media', pasta_temp_nome)
                new_path = os.path.join(settings.MEDIA_ROOT, 'media', str(self.id))
                
                if os.path.exists(old_path):
                    if os.path.exists(new_path):
                        # Se a pasta ID já existe (por erro anterior), movemos os arquivos de dentro
                        for file in os.listdir(old_path):
                            shutil.move(os.path.join(old_path, file), os.path.join(new_path, file))
                        os.rmdir(old_path)
                    else:
                        # Caso normal: renomeia a pasta inteira
                        os.rename(old_path, new_path)
                    
                    # Atualiza os nomes no banco de dados para refletir o novo caminho
                    if self.capa:
                        self.capa.name = self.capa.name.replace(pasta_temp_nome, str(self.id))
                    if self.video_demonstracao:
                        self.video_demonstracao.name = self.video_demonstracao.name.replace(pasta_temp_nome, str(self.id))
                    
                    # Salva apenas os caminhos atualizados
                    super().save(update_fields=['capa', 'video_demonstracao'])

    def __str__(self):
        return self.titulo
    

from django.db.models.signals import post_delete
from django.dispatch import receiver

@receiver(post_delete, sender=Livro)
def deletar_pasta_livro(sender, instance, **kwargs):
    # O MEDIA_ROOT aponta para a pasta 'media' do seu projeto
    # instance.id ainda está acessível no objeto mesmo após deletado do banco
    caminho_pasta = os.path.join(settings.MEDIA_ROOT, 'media', str(instance.id))
    
    if os.path.exists(caminho_pasta):
        shutil.rmtree(caminho_pasta)
        print(f"Faxina concluída: Pasta {instance.id} removida com sucesso.")