from shared.db import *
from pprint import pprint
from django.contrib import messages

def get_user_id(email_id, password):
    res = select_where("customer", "email_id = '{}' and cust_pass = '{}'".format(email_id, password))
    if len(res) > 1 or len(res) <= 0:
        return -1
    return res[0]['cust_id']

def get_user_details(user_id):
    res = select_where("customer", "cust_id = {}".format(user_id))
    if len(res) > 1 or len(res) <= 0:
        return None
    return res[0]

def get_all_user_details():
    res = select_where("customer", "cust_id != 0")
    if len(res) <= 0:
        return None
    return res

def check_order_tbl_click(request):
    for key in request.POST.keys():
        if key.startswith('order_btn'):
            return True
    return False

def toggle_food_item(request, btn_str):
    user_id = request.session['user_id']
    food_id = btn_str.rsplit('_', 1)[1]
    rest_id = btn_str.rsplit('_', 2)[1]

    active_cart = select_where("orders", "cust_id = {} and status = 'IN PROGRESS'".format(user_id))
    if len(active_cart) > 0:
        cart_order_id = active_cart[0]['order_id']
        cart_rest_id = select_where("orders", "order_id = {}".format(cart_order_id))[0]['rest_id']
        if int(cart_rest_id) != int(rest_id):
            messages.info(request, "Clearing Old Shopping Cart As Items Present From a Different Restaurant")
            del_where("shopping_cart", "order_id = {}".format(cart_order_id))
            insert_row("shopping_cart", [cart_order_id, food_id, 1])
        else:
            cart_dict = select_where("shopping_cart", "order_id = {} and food_id = {}".format(cart_order_id, food_id))
            if len(cart_dict) > 0:
                del_where("shopping_cart", "order_id = {} and food_id = {}".format(cart_order_id, food_id))
                if len(select_where("shopping_cart", "order_id = {}".format(cart_order_id))) == 0:
                    del_where("orders", "order_id = {}".format(cart_order_id))
            else:
                insert_row("shopping_cart", [cart_order_id, food_id, 1])
    else:
        order_id = get_unique_id("orders", "order_id")
        insert_row("orders", [order_id, user_id, 'NULL', rest_id, 'NULL', "IN PROGRESS"])
        insert_row("shopping_cart", [order_id, food_id, 1])

def change_cart_qty(request, btn_str):
    user_id = request.session['user_id']
    mode = btn_str.split('_', 1)[0]
    food_id = btn_str.rsplit('_', 1)[1]
    order_id = btn_str.rsplit('_', 2)[1]

    if mode == "inc":
        update_where("shopping_cart", "count = count + 1", "food_id = {} and order_id = {}".format(food_id, order_id))
        return
    update_where("shopping_cart", "count = count - 1", "food_id = {} and order_id = {}".format(food_id, order_id))
    
    del_where("shopping_cart", "count <= 0")

    cart_dict = select_where("shopping_cart", "order_id = {}".format(order_id))
    order_dict = select_where("orders", "order_id = {}".format(order_id))
    if len(cart_dict) == 0 and len (order_dict) > 0:
        del_where("orders", "order_id = {}".format(order_id))

def checkout_cart(request):
    user_id = request.session['user_id']

    active_cart = select_where("orders", "cust_id = {} and status = 'IN PROGRESS'".format(user_id))
    if len(active_cart) == 0:
        return

    order_id = active_cart[0]['order_id']
    update_where("orders", "status='PENDING'", "order_id={}".format(order_id))
    update_where("orders", "timestamp=CURRENT_TIMESTAMP", "order_id={}".format(order_id))

    maxi = 100
    del_final = None
    del_dict = select_where("delivery")
    for i in del_dict:
        del_p = i['del_id']
        del_dict = select_where("orders", "status='PENDING' and del_id={}".format(del_p))
        if len(del_dict) < maxi:
            maxi = len(del_dict)
            del_final = del_p

    if del_final:
        update_where("orders", "del_id={}".format(del_final), "order_id={}".format(order_id))

def get_all_order_details(cust_id, status="PENDING"):
    context = {}
    context['cust_add'] = select_where("customer", "cust_id = {}".format(cust_id))[0]['cust_add']

    map_dict = select_where("orders", "cust_id = {} and status = '{}'".format(cust_id, status))
   
    pending_order = []
    for order in map_dict:
        order_dict = {}
        order_id = order['order_id']
        rest_id = select_where("orders", "order_id = {}".format(order_id))[0]['rest_id']
        rest_name = select_where("restaurant", "rest_id = {}".format(rest_id))[0]['rest_name']
        del_id = select_where("orders", "order_id = {}".format(order_id))[0]["del_id"]
        if del_id and del_id != "NULL":
            order_dict['del_name'] = select_where("delivery", "del_id = {}".format(del_id))[0]['del_firstname']
            order_dict['del_name'] += " " + select_where("delivery", "del_id = {}".format(del_id))[0]['del_lastname']

        item_list = []
        tot_amount = 0
        cart_dict = select_where("shopping_cart", "order_id = {}".format(order_id))
        for item in cart_dict:
            food_name = select_where("inventory", "food_id = {}".format(item['food_id']))[0]['food_name']
            price = select_where("menu", "food_id = {} and rest_id = {}".format(item['food_id'], rest_id))[0]['cost']
            tot_price = int(item['count']) * int(price)
            img_id = (item['food_id'] % 5) + 1
            item_dict = {"food_name": food_name, "price": price, "tot_price": tot_price, "food_id": item['food_id'], "count": item['count'], "order_id": order_id, "img_id": img_id}
            tot_amount += tot_price
            item_list.append(item_dict)
        
        order_dict['order_id'] = order_id
        order_dict['rest_id'] = rest_id
        order_dict['rest_name'] = rest_name
        order_dict['tot_amount'] = tot_amount
        order_dict['item_list'] = item_list

        pending_order.append(order_dict)
    
    return pending_order

def insert_user_db(request):
    fields = {}

    fields["full_name"] = request.POST.get('full-name')
    fields["email_id"] = request.POST.get('email')
    fields["password"] = request.POST.get('password')
    fields["confirm_password"] = request.POST.get('confirm-password')
    fields["address"] = request.POST.get('address')
    fields["mob_no"] = request.POST.get('mob-no')

    pprint(fields)
    for key in fields.keys():
        value = fields[key]
        if not value or value == "":
            return "Field {} was empty!".format(key.replace('_', ' '))

    name_split = fields['full_name'].split(' ')
    if len(name_split) < 2:
        return "Please provide First Name and Last Name"
    if fields['password'] != fields['confirm_password']:
        return "Password Field Confirm Password and Password Do Not Match"
    
    if len(select_where('customer', "email_id = '{}'".format(fields['email_id']))) > 0:
        return "Email ID - {} has already been registered!".format(fields['email_id'])

    cust_id = get_unique_id("customer", "cust_id")
    insert_row("customer", [cust_id, name_split[0], name_split[1], fields["address"], fields['email_id'], fields["password"]])
    return None
    # print(full_name, email_id, password, confirm_password, address, mob_no)
