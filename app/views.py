from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Livro
from .forms import LivroForm
from django.db.models import Q, Case, When, IntegerField, Value

# --- FUNÇÕES AUXILIARES DE COR ---

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb

# --- VIEWS PÚBLICAS ---

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
        livros = livros.order_by('id')

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
        'car_choices': Livro.STATUS_CHOICES_CARACTERISTICAS
    })

# --- VIEWS DE ADMINISTRAÇÃO ---

@login_required
def admin_dashboard(request):
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
        'is_edit': False
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

def p404_customizada(request, exception):
    return render(request, '404.html', status=404)