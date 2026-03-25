from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.homeview, name='home'),
    path('<slug:slug>/', views.livroview, name='livro'),
    path('dashboard/home', views.admin_dashboard, name='dashboard'),
    path('dashboard/adicionar', views.add_livro, name='add_livro'),
    path('dashboard/editar/<int:id>', views.edit_livro, name='edit_livro'), 
    path('update-book-status/<int:id>/', views.update_book_status, name='update_book_status'), # Botão de vendido
]

# Para renderizar as imagens
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)