"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
import os
from dotenv import load_dotenv
load_dotenv()

urlpatterns = [
    path('admin/', admin.site.urls),
    path(f'login/{os.getenv('SECRET_LOGIN_KEY')}/', auth_views.LoginView.as_view(template_name='dashboard/login.html'), name='login'),
    path('', include('app.urls')),
]
handler404 = 'app.views.p404_customizada' # 404 desconfigurado