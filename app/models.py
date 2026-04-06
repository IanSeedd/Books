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
    editora = models.CharField(
        max_length=100,
        null = True,
        blank = True,
        )
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
        null = False,
        blank = False,
        default=['artes']
    )

    caracteristicas = MultiSelectField(
        max_length=100,
        choices = STATUS_CHOICES_CARACTERISTICAS,
        null = True,
        blank = True,
        default=None
    )
    capa = models.ImageField(
        default='media/defaults/hmarch.webp',
        upload_to=caminho_livro,
        # Formatos aceitos:
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'webp', 'png', 'jpeg'])]
        )
    video_demonstracao = models.FileField(
        upload_to=caminho_livro,
        max_length=500,
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
                # Pega o caminho base da pasta temporária usando o slug gerado
                pasta_temp_nome = f"temp_{self.slug}"
                # IMPORTANTE: Verifique se no seu caminho_livro você está usando 'livros' ou direto 'media'
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

            # --- NOVA LÓGICA: Renomear arquivos para o padrão capa_id.ext e video_id.ext ---
            def renomear_para_padrao(campo, prefixo):
                arquivo = getattr(self, campo)
                if not arquivo:
                    return
                # Pular renomeação para a imagem padrão (compartilhada)
                if campo == 'capa' and 'defaults' in arquivo.name:
                    return
                if hasattr(arquivo, 'path') and os.path.exists(arquivo.path):
                    dir_name = os.path.dirname(arquivo.path)
                    nome_atual = os.path.basename(arquivo.name)
                    ext = os.path.splitext(nome_atual)[1].lower()
                    nome_desejado = f"{prefixo}_{self.id}{ext}"
                    if nome_atual != nome_desejado:
                        novo_caminho = os.path.join(dir_name, nome_desejado)
                        try:
                            os.rename(arquivo.path, novo_caminho)
                            novo_relativo = os.path.join(os.path.dirname(arquivo.name), nome_desejado)
                            # Atualiza o banco de dados sem chamar save() novamente
                            Livro.objects.filter(pk=self.pk).update(**{campo: novo_relativo})
                            setattr(self, campo, novo_relativo)
                        except Exception:
                            # Falha silenciosa para não quebrar a operação principal
                            pass

            renomear_para_padrao('capa', 'capa')
            renomear_para_padrao('video_demonstracao', 'video')

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