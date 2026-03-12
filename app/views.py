from django.shortcuts import render
from .models import Livro
import functools

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb

def homeview(request):
    # Agora pegamos uma lista de categorias
    categorias_selecionadas = request.GET.getlist('cat')
    livros = Livro.objects.all()
    
    cores_categorias = {
        'artes': '#FF5733', 'nerd': '#00D4FF', 'estudos': '#A3E635',
        'brumed': '#9333EA', 'erotica': '#FB7185',
    }

    nomes_bonitos = []
    rgb_list = []

    if categorias_selecionadas:
        # Filtra livros que pertencem a QUALQUER uma das categorias selecionadas
        livros = livros.filter(categoria__in=categorias_selecionadas)
        
        choices = dict(Livro.STATUS_CHOICES_CATEGORIA)
        for cat in categorias_selecionadas:
            nomes_bonitos.append(choices.get(cat))
            if cat in cores_categorias:
                rgb_list.append(hex_to_rgb(cores_categorias[cat]))

        # Cálculo da Cor Média (Mistura)
        if rgb_list:
            avg_rgb = tuple(
                int(sum(x) / len(x)) for x in zip(*rgb_list)
            )
            cor_tema = rgb_to_hex(avg_rgb)
        else:
            cor_tema = "#F2F2EB"
    else:
        cor_tema = "#F2F2EB"

    # No final da sua homeview em views.py
    return render(request, 'home.html', {
        'livros': livros,
        'categorias_ativas': categorias_selecionadas,
        'categoria_nome_bonito': " + ".join(nomes_bonitos) if nomes_bonitos else None,
        'cor_tema': cor_tema,
        'status_choices': Livro.STATUS_CHOICES_CATEGORIA # Adicione isso aqui!
    })