from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Views publicas 
    path('', views.homeview, name='home'),
    path('escolha-por-mim/', views.escolha_por_mim, name='escolha_por_mim'),
    path('<slug:slug>/', views.livroview, name='livro'),
    # Views de ADM:
    path('dashboard/home', views.admin_dashboard, name='dashboard'),
    path('update-book-status/<int:id>/', views.update_book_status, name='update_book_status'), # Botão de vendido
    path('dashboard/adicionar', views.add_livro, name='add_livro'),
    path('dashboard/editar/<int:id>', views.edit_livro, name='edit_livro'), 
    path('dashboard/deletar/<int:id>', views.delete_livro, name='delete_livro'), # Literalmente deletar
]

# Para renderizar as imagens
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)