from django.urls import path
from .views import dashboard,layer1_view, layer2_view, layer3_view, layer4_view, layer5_view

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('layer1/', layer1_view, name='layer1'),
    path('layer2/', layer2_view, name='layer2'),
    path('layer3/', layer3_view, name='layer3'),
    path('layer4/', layer4_view, name='layer4'),
    path('layer5/', layer5_view, name='layer5'),
]
