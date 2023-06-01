from django.shortcuts import render, redirect
from django.db import connection
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import *
from django.contrib.auth.models import User
from django.http import HttpResponse
from .forms import UsersLoginForm, searchForm
from django import forms
from django.contrib import messages
from .utils import *
from .gen_context import *

def login_view(request):
    context = {}
    context['login_disp'] = "block"
    context['register_disp'] = "none"
    print(request.POST.keys())
    if 'login-btn' in request.POST.keys():
        context['login_disp'] = "block"
        context['register_disp'] = "none"
        return render(request, "login/form.html", context=context)
    elif 'register-btn' in request.POST.keys():
        context['login_disp'] = "none"
        context['register_disp'] = "block"
        return render(request, "login/form.html", context=context)
    elif 'register-submit' in request.POST.keys():
        err_str = insert_user_db(request)
        context['err_str'] = err_str
        return render(request, "login/form.html", context = context)

    form = UsersLoginForm(request.POST or None)
    if form.is_valid():
        email_id = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user_id = get_user_id(email_id, password)
        if user_id == -1:
            context['err_str'] = "Invalid Login"
            return render(request, "login/form.html", context= context)
        
        user = authenticate(username=email_id, password=password)

        if user is None:
            user = User.objects.create_user(email_id, email_id, password)
            user = authenticate(username=email_id, password=password)

        login(request, user)
        user_details = get_user_details(user_id)
        request.session['user_id'] = user_details['cust_id']
        request.session['username'] = user_details['cust_firstname']

        if user_id == 0:
            return redirect("/admin_home")
        
        return redirect("/home/")
      #  return render(request, "//{}".format(user_id), context={"username": user_details['cust_firstname']})

    return render(request, "login/form.html", context = context)



@login_required
def admin_view(request):
    if request.method == 'POST':
        if 'logout_btn' in request.POST.keys():
            logout(request)
            return redirect("/login")
        for key in request.POST.keys():
            if key.startswith('order_btn_'):
                order_id = key.rsplit('_', 1)[1]
                update_where('orders', "status = 'DELIVERED'", 'order_id = {}'.format(order_id))

    context = gen_admin_home_context()
    return render(request, "admin/home.html", context = context)


@login_required
def customer_view(request):
    search_str = None
    if request.method == 'POST':
        print(request.POST.keys())
        if 'logout_btn' in request.POST.keys():
            logout(request)
            return redirect("/login")
        elif 'search_btn' in request.POST.keys():
            search_str = request.POST.get('search_inp')
        elif 'cart_btn' in request.POST.keys():
            return redirect("/home/cart")
        for key in request.POST.keys():
            if key.startswith('food_btn'):
                toggle_food_item(request, key)
            
    context = gen_customer_home_context(request.session['user_id'], search_str)
    return render(request, "customer/home.html", context = context)

@login_required
def cart_view(request):
    if request.method == 'POST':
        if 'logout_btn' in request.POST.keys():
            logout(request)
            return redirect("/login")
        elif 'checkout_btn' in request.POST.keys():
            checkout_cart(request)
            return redirect("/home/past_orders")
        for key in request.POST.keys():
            if key.startswith('inc_btn') or key.startswith('dec_btn'):
                change_cart_qty(request, key)
    context = gen_cart_contex(request.session['user_id'])
    return render(request, "customer/cart.html", context = context)

@login_required
def cust_order_view(request):
    if request.method == 'POST':
        if 'logout_btn' in request.POST.keys():
            logout(request)
            return redirect("/login")

    context = gen_cust_order_context(request.session['user_id'])
    return render(request, "customer/orders.html", context=context)

@login_required
def admin_tables_view(request):
    print_dict = {
        "restaurant": [
            {"rest_name": "Restaurant Name"},
            {"rest_add": "Restaurant Address"},
            {"review": "Review"},
        ],
        "customer": [
            {"cust_fistname": "Customer Name"},
            {"cust_lastname": "Customer Name"},
            {"cust_add": "Customer Address"},
            {"email_id": "Email ID"},
        ]
    }
    context = {}
    if request.method == 'POST':
        if 'view_btn' in request.POST.keys():
            selected_item = request.POST.get('table-list')
            if selected_item == "customer":
                context["customer"] = select_where("customer", "cust_id != 0")
            elif selected_item == "restaurant":
                context["restaurant"] = select_where("restaurant")
            return render(request, "admin/table.html", context=context)

    return render(request, "admin/table.html", None)

def index(request):
    return redirect("/login")
#    return HttpResponse("Hello World, Normies")
