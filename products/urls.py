from django.urls import path
from . import views

app_name = "products"  # krävs för att kunna använda namespace

urlpatterns = [
    path('', views.product_list, name='list'),  # /products/
    # path('category/<slug:slug>/', views.product_list, name='category'),  # /products/category/<slug>/
    path("category/<path:slug_path>/", views.product_list, name="category"),
    path('<slug:slug>/', views.product_detail, name='detail'),  # /products/<slug>/
]
