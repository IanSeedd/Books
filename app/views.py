from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Livro
from .forms import LivroForm
from django.views.decorators.csrf import csrf_exempt
import json
import random
from django.http import JsonResponse
from django.db.models import Q, Case, When, IntegerField, Value

# --- FUNÇÕES AUXILIARES DE COR ---

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb

# --- VIEWS PÚBLICAS ---

def escolha_por_mim(request):
    # Pega um livro aleatório do banco de dados
    livro_random = Livro.objects.filter(vendido=False).order_by('?').first()
    
    if livro_random:
        return redirect('livro', slug=livro_random.slug)
    # Se não houver nenhum livro no banco, volta para a home (só para garantir que não vai quebrar nada)
    return redirect('home')

def homeview(request):
    query = request.GET.get('q', '') 
    categorias_selecionadas = request.GET.getlist('cat')
    caracteristicas_selecionadas = request.GET.getlist('car')
    
    livros = Livro.objects.all()

    cores_categorias = {
        'artes': '#FF5733', 'nerd': '#00D4FF', 'estudos': '#A3E635',
        'brumed': '#9333EA', 'erotica': '#FB7185',
    }

    nomes_bonitos = []
    rgb_list = []
    
    # 1. FILTRO DE CATEGORIAS (Lógica OR com Priorização)
    if categorias_selecionadas:
        # Filtra livros que tenham PELO MENOS UMA das categorias (OR)
        filtro_cat = Q()
        for cat in categorias_selecionadas:
            filtro_cat |= Q(categoria__contains=cat)
        livros = livros.filter(filtro_cat)

        # Pontuação para ordenação (Relevância)
        relevancia = Value(0)
        for cat in categorias_selecionadas:
            relevancia += Case(
                When(categoria__contains=cat, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        livros = livros.annotate(pontos_cat=relevancia)

        # Lógica de nomes e cores para o tema da página
        choices = dict(Livro.STATUS_CHOICES_CATEGORIA)
        for cat in categorias_selecionadas:
            nomes_bonitos.append(choices.get(cat))
            if cat in cores_categorias:
                rgb_list.append(hex_to_rgb(cores_categorias[cat]))

    # 2. FILTRO DE CARACTERÍSTICAS
    if caracteristicas_selecionadas:
        filtro_car = Q()
        for car in caracteristicas_selecionadas:
            filtro_car |= Q(caracteristicas__contains=car)
        livros = livros.filter(filtro_car)

    # 3. BUSCA POR TEXTO
    if query:
        livros = livros.filter(titulo__icontains=query)

    # 4. ORDENAÇÃO (Prioriza pontos de categoria, depois ID)
    if categorias_selecionadas:
        livros = livros.order_by('-pontos_cat', 'id')
    else:
        livros = livros.order_by('-id')

    # Cálculo da Cor Média para o Tema
    if rgb_list:
        avg_rgb = tuple(int(sum(x) / len(x)) for x in zip(*rgb_list))
        cor_tema = rgb_to_hex(avg_rgb)
    else:
        cor_tema = "#F2F2EB"

    return render(request, 'home.html', {
        'livros': livros,
        'categorias_ativas': categorias_selecionadas,
        'caracteristicas_ativas': caracteristicas_selecionadas,
        'categoria_nome_bonito': " + ".join(nomes_bonitos) if nomes_bonitos else None,
        'cor_tema': cor_tema,
        'cat_choices': Livro.STATUS_CHOICES_CATEGORIA,
        'car_choices': Livro.STATUS_CHOICES_CARACTERISTICAS
    })

def livroview(request, slug):
    import os
    livro = get_object_or_404(Livro, slug=slug)

    cores_categorias = {
        'artes': '#FF5733', 'nerd': '#00D4FF', 'estudos': '#A3E635',
        'brumed': '#9333EA', 'erotica': '#FB7185',
    }
    
    rgb_list = []
    # livro.categoria retorna a lista de slugs do MultiSelectField
    for cat in livro.categoria:
        if cat in cores_categorias:
            rgb_list.append(hex_to_rgb(cores_categorias[cat]))

    if rgb_list:
        avg_rgb = tuple(int(sum(x) / len(x)) for x in zip(*rgb_list))
        cor_tema = rgb_to_hex(avg_rgb)
    else:
        cor_tema = "#F2F2EB"

    return render(request, 'livro.html', {
        'livro': livro,
        'cor_tema': cor_tema,
        'car_choices': Livro.STATUS_CHOICES_CARACTERISTICAS,
        'contato': os.getenv('NUMERO') # numero de contato para consultar sobre o livro
    })


# --- VIEWS DE ADMINISTRAÇÃO ---

@login_required
def admin_dashboard(request):
    if not request.session.get('2fa_verificado'):
        return redirect('view_2fa') # Manda ele pro 2FA se não verificou
    livros = Livro.objects.all().order_by('-id')
    return render(request, 'dashboard/admin_dashboard.html', {'livros': livros})

@login_required
def add_livro(request):
    if request.method == 'POST':
        form = LivroForm(request.POST, request.FILES)
        if form.is_valid():
            livro = form.save(commit=False)
            # O slug é gerado automaticamente no save() do seu model ou no form
            livro.save()
            form.save_m2m() # Importante para salvar campos de múltipla escolha
            return redirect('dashboard')
    else:
        form = LivroForm()
    
    return render(request, 'dashboard/adicionar_editar.html', {
        'form': form,
        'is_edit': False,
    })

@login_required
def edit_livro(request, id): # Usando 'id' para bater com o <int:id> da URL
    livro = get_object_or_404(Livro, id=id)
    
    if request.method == 'POST':
        form = LivroForm(request.POST, request.FILES, instance=livro)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = LivroForm(instance=livro)
        
    return render(request, 'dashboard/adicionar_editar.html', {
        'form': form,
        'livro': livro,
        'is_edit': True
    })
# Views para o botão do dashboard
@login_required
@csrf_exempt 
def update_book_status(request, id):
    if request.method == 'POST':
        livro = get_object_or_404(Livro, id=id)
        data = json.loads(request.body)
        
        # Aqui usamos o formulário para validar a alteração
        # Passamos apenas o dado do 'vendido' e o 'instance' do livro atual
        livro.vendido = data.get('vendido', False)
        livro.save()
        
        return JsonResponse({'status': 'success', 'vendido': livro.vendido})
    return JsonResponse({'status': 'error'}, status=400)

def p404_customizada(request, exception):
    return render(request, '404.html', status=404)
# Views de deletar
@login_required
def delete_livro(request, id):
    # Busca o livro ou retorna 404 se não existir
    livro = get_object_or_404(Livro, id=id)
    
    if request.method == 'POST':
        livro.delete()
        return redirect('dashboard')
    # Se tentarem acessar via GET por erro, apenas volta para o dashboard
    return redirect('dashboard')

# --- VIEWS DE 2FA ---
from django.core.mail import send_mail
from django.contrib.auth import logout
from django.http import Http404

def view_2fa(request):
    # 1. SEGURANÇA: Caso não haja login forja um 404
    if not request.user.is_authenticated:
        raise Http404

    # 2. SEGURANÇA: Se ele já verificou o 2FA nessa sessão, manda pro dashboard
    if request.session.get('2fa_verificado'):
        return redirect('dashboard')

    if request.method == 'POST':
        codigo_digitado = request.POST.get('codigo')
        codigo_real = request.session.get('codigo_2fa')

        if codigo_digitado and codigo_digitado == codigo_real:
            request.session['2fa_verificado'] = True
            # Limpa o código da sessão por segurança após usar
            del request.session['codigo_2fa'] 
            return redirect('dashboard')
        else:
            return render(request, '2fa.html', {'error': 'Código inválido!'})

    # --- LÓGICA DE ENVIO (ANTI-SPAM) ---
    # Só gera e envia um codigo, se não existir um ativo na sessão (evita o spam do F5)
    if not request.session.get('codigo_2fa'):
        codigo_2fa = str(random.randint(100000, 999999))
        request.session['codigo_2fa'] = codigo_2fa
        
        try:
            send_mail(
                'Código de Segurança',
                f'Seu código é: {codigo_2fa}',
                settings.EMAIL_HOST_USER,
                [request.user.email],
                fail_silently=False,
            )
        except Exception:
            return render(request, 'dashboard/2fa.html', {'error': 'Erro ao enviar e-mail. Tente novamente.'})

    return render(request, 'dashboard/2fa.html')
@login_required
def reenviar_2fa(request):
    if not request.user.is_authenticated:
        raise Http404
        
    # Remove o código atual da sessão para forçar a criação de um novo
    if 'codigo_2fa' in request.session:
        del request.session['codigo_2fa']
    
    # Redireciona de volta para a tela de verificação
    return redirect('view_2fa')