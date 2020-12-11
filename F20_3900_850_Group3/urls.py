from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from store import views

urlpatterns = [
    path('', include('store.urls')),

    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),

    path('ckeditor/', include('ckeditor_uploader.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
