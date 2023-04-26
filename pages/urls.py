from django.urls import path

from .views import HomePageView
from . import views

urlpatterns = [
    path('', views.home_view, name="home_view"),
    path('', HomePageView.as_view(), name='home'),
    path('portfolio/', views.portfolio_view, name='portfolio_view'),
    path('deposit/', views.deposit_view, name='deposit_view'),
    path('trade/', views.trade_view, name='trade_view'),
    path('buy/', views.buy_view, name='buy_view'),
    path('sell/', views.sell_view, name='sell_view'),
    path('transactions/', views.transactions_view, name='transactions_view'),
    path('success_buy/<str:crypto>', views.success_buy_view, name='success_buy_view'),
    path('error_buy/<str:crypto>', views.error_buy_view, name='error_buy_view'),
    path('error_sell/<str:crypto>', views.error_sell_view, name='error_sell_view'),
    path('success_sell/<str:crypto>', views.success_sell_view, name='success_sell_view'),
    path('success_deposit/<int:value>', views.success_deposit_view, name='success_deposit_view'),
]