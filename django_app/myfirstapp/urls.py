from django.urls import path
from . import views


app_name = 'myfirstapp'

urlpatterns = [
    path('prodreports/', views.prodreports, name='prodreports'),
    path('production_detail/<int:prod_id>/', views.production_detail, name='production_detail')
]
