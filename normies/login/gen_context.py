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
from pprint import pprint


def gen_admin_home_context():
    context = {}
    all_cust_details = get_all_user_details()
    context['tot_users'] = len(all_cust_details)
    context['order_count'] = len(select_where("orders", "status='PENDING' or status='DELIVERED'"))
    context['restaurant_count'] = len(select_where('restaurant'))

    pending_orders = select_where("orders", "status = 'PENDING'")
    context['pending_order_count'] = len(pending_orders)

    for order in pending_orders:
        cust_dict = select_where("customer", "cust_id = {}".format(order['cust_id']))[0]
        order['cust_name'] = "{} {}".format(cust_dict['cust_firstname'], cust_dict['cust_lastname']) 
        order['cust_add'] = cust_dict['cust_add']  
        
        del_dict = select_where("delivery", "del_id = {}".format(order['del_id']))[0]
        order['del_name'] = "{} {}".format(del_dict['del_firstname'], del_dict['del_lastname'])

        rest_dict = select_where("restaurant", "rest_id = {}".format(order['rest_id']))[0]
        order['rest_name'] = rest_dict['rest_name']

    context['pending_orders'] = pending_orders
    return context

def gen_customer_home_context(cust_id, search_str=None):
    menu_dict = {}
    context = {}

    food_list = select_where("menu")
    for item in food_list:
        rest_det = select_where("restaurant", "rest_id = {}".format(item['rest_id']))[0]
        food_name = select_where("inventory", "food_id = {}".format(item['food_id']))[0]['food_name']
        rest_name = rest_det['rest_name']
        if search_str and search_str.lower() not in food_name.lower() and search_str.lower() not in rest_name.lower():
            continue

        if rest_name not in menu_dict: menu_dict[rest_name] = {}
        menu_dict[rest_name]['review'] = rest_det['review']
        menu_dict[rest_name]['rest_name'] = rest_name
        menu_dict[rest_name]['rest_id'] = item['rest_id']

        insert_dict = {"food_name": food_name, "cost": item['cost'], "food_id": item['food_id'], "img_id": (item['food_id'] % 5) + 1}
        cart_query = run_query("select * from shopping_cart where food_id = {} and order_id in (select order_id from orders where cust_id = {} and status = 'IN PROGRESS')".format(item['food_id'], cust_id))
        if len(cart_query) > 0:
            insert_dict['in_cart'] = True
        if 'items' not in menu_dict[rest_name]:
            menu_dict[rest_name]['items'] = [insert_dict]
            continue
        menu_dict[rest_name]['items'].append(insert_dict)
        
    
    context['menu'] = menu_dict
    context['restaurant'] = select_where("restaurant")

    context['cust_add'] = select_where("customer", "cust_id = {}".format(cust_id))[0]['cust_add']
    context['cart_tot_items'] = run_query("select sum(count) as tot_items from shopping_cart where order_id in (select order_id from orders where cust_id = {} and status = 'IN PROGRESS');".format(cust_id))[0]['tot_items']
    if not context['cart_tot_items']:
        context['cart_tot_items'] = 0

    return context

def gen_cart_contex(cust_id):
    context = {}
    tot_amount = tot_cnt = 0

    context['cust_add'] = select_where("customer", "cust_id = {}".format(cust_id))[0]['cust_add']

    cart_dict = run_query("select * from shopping_cart where order_id in (select order_id from orders where cust_id = {} and status = 'IN PROGRESS');".format(cust_id))

    if len(cart_dict) > 0:
        order_id = select_where("orders", "status = 'IN PROGRESS'")[0]['order_id']
        rest_id = select_where("orders", "order_id = {}".format(order_id))[0]['rest_id']

        item_list = []
        for item in cart_dict:
            food_name = select_where("inventory", "food_id = {}".format(item['food_id']))[0]['food_name']
            price = select_where("menu", "food_id = {} and rest_id = {}".format(item['food_id'], rest_id))[0]['cost']
            tot_price = int(item['count']) * int(price)
            item_dict = {"food_name": food_name, "price": price, "tot_price": tot_price, "food_id": item['food_id'], "count": item['count'], "order_id": order_id}
            
            item_list.append(item_dict)
            tot_cnt += item['count']
            tot_amount += tot_price
        
        if tot_amount >= 40:
            context['free_coupon'] = True
        else:
            context['final_amnt'] = tot_amount + 5
        
        context['item_list'] = item_list
    
    context['tot_cnt'] = tot_cnt
    context['tot_amount'] = tot_amount

    return context   

def gen_cust_order_context(cust_id):
    context = {}

    tmp = get_all_order_details(cust_id, "PENDING")
    if len(tmp) > 0:
        context['pending'] = tmp
    tmp = get_all_order_details(cust_id, "DELIVERED")
    if len(tmp) > 0:
        context['delivered'] = tmp
    context['cust_add'] = select_where("customer", "cust_id = {}".format(cust_id))[0]['cust_add']
    return context

# def gen_table_data():

    