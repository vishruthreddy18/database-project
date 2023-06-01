from django.urls import path, re_path
from .views import (
    login_view,
    admin_view,
    admin_tables_view,
    customer_view,
    cust_order_view,
    cart_view,
    index,
)
app_name = 'login'
urlpatterns = [
#    re_path("login", login_view, name = "login"),
#    path('', index, name='index'),
    path("admin_home/", admin_view, name = "admin_home"),
    path("admin_home/tables", admin_tables_view, name = "admin_tables"),
    path("home/cart", cart_view, name = "cart"),
    path("home/past_orders", cust_order_view, name = "past_orders"),
    re_path("home/", customer_view, name = "home"),
    path("login/", login_view, name = "login"),
    path("", index, name = "index"),
]