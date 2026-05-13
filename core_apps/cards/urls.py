from django.urls import path
from .views import VirtualCardListCreateAPIView, VirtualCardDetailAPIView, VirtualCardTopupAPIView

urlpatterns = [
    path("virtual-cards/", VirtualCardListCreateAPIView.as_view(), name="virtual_card_list_create"),
    path("virtual-cards/<uuid:pk>/", VirtualCardDetailAPIView.as_view(), name="virtual_card_detail"),
    path("virtual-cards/<uuid:pk>/topup/", VirtualCardTopupAPIView.as_view(), name="virtual_card_topup"),
]