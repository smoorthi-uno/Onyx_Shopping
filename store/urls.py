from django.urls import path
from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # leave empty string for base url
    path('', views.home, name="home"),
    path('old', views.store, name="store"),
    path('cart/', views.cart, name="cart"),
    path('checkout/', views.checkout, name="checkout"),

    path('update_item/', views.updateItem, name="update_item"),
    path('process_order/', views.processOrder, name="process_order"),

    # url(r'^category/(?P<hierarchy>.+)/$', views.show_category, name='category'),
    # path('accounts/login/password_reset', auth_views.PasswordResetView.as_view(), name='password_reset'),
    # path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),

    path('category/<int:id>/<slug:slug>', views.category_products, name='category_products'),
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),

    path('register/', views.registerPage, name='register'),
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name='logout'),

    path('aboutus/', views.aboutus, name="aboutus"),
    path('contactus/', views.contactus, name="contactus"),

    path('contact/', views.contactPage, name='contact'),
    path('about/', views.aboutPage, name='about')
]
