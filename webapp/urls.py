from django.urls import path, re_path
from django.contrib import admin
import webapp.views as views

urlpatterns = \
    [
        path('', views.index),
        path('admin/', admin.site.urls),
        re_path(r'^(?P<path>.*)/$', views.index, name='index'),
    ]
