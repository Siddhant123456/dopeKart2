from django.shortcuts import render,redirect
from store.models import Product
from .models import Cart,CartItem
from store.models import Variation
from django.http import HttpResponse
from django.contrib import messages
from accounts.models import Account
from django.contrib.auth.decorators import login_required
# Create your views here.

def cart(request):
    cart_id = _cart_id(request)
    total = 0
    tax = 0
    cart_prods = []
    try:
        if request.user.is_authenticated:
            user = Account.objects.get(pk = request.user.id)
    
            cart_prods = CartItem.objects.filter(user = user,is_active = True)

        else:
            cart = Cart.objects.get(cart_id = cart_id)
            
            cart_prods = CartItem.objects.filter(cart = cart,is_active = True)
            
        
        for item in cart_prods:
            total += (item.product.price) * (item.quantity)
            
        tax = (8/100)*total;
        
    except Cart.DoesNotExist:
        pass
    
    total_price = total + tax;
    data = {
        'all_prods' : cart_prods,
        'total' : total,
        'tax' : tax,
        'total_price' : total_price,
        
    }
    return render(request,'store/cart.html',data)


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request,product_id):
    # curren_user = request.user
    product = Product.objects.get(id = product_id)
    product_variation = []
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]
            
            try:
                variation = Variation.objects.get(product = product,variation_category__iexact = key,variation_value__iexact = value)
                product_variation.append(variation)
            except:
                pass
    
    try:
        if request.user.is_authenticated:
            user = request.user
        cart = Cart.objects.get(cart_id = _cart_id(request))   #get the cart using the cart id present in the session
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id = _cart_id(request)
        )
    cart.save()
    if request.user.is_authenticated:
        is_cart_item_exists = CartItem.objects.filter(product = product,user=user).exists()
    else:
        is_cart_item_exists = CartItem.objects.filter(product = product,cart=cart).exists()


    if is_cart_item_exists:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.filter(product = product,user =user)
        else:    
            cart_item = CartItem.objects.filter(product = product,cart =cart)
        # existing variations ->database
        # current variations ->product variation list
        # item id -> database

        # if current variation is inside the existing variations then we will increase the quantity
        existing_variations_list = []
        id = []
        for item in cart_item:
            existing_variation = item.variations.all()
            existing_variations_list.append(list(existing_variation))
            id.append(item.id)

        if product_variation in existing_variations_list:
            index = existing_variations_list.index(product_variation)
            item_id = id[index]
            item = CartItem.objects.get(product = product,id = item_id)
            item.quantity += 1
            item.save()

        else:
            if request.user.is_authenticated:
                cart_item = CartItem.objects.create(
                product = product,
                quantity = 1,
                user = user
            )
            else: 
                cart_item = CartItem.objects.create(
                product = product,
                quantity = 1,
                cart = cart
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                for item in product_variation:
                    cart_item.variations.add(item)
            cart_item.save()


    else:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.create(
            product = product,
            quantity = 1,
            user = user
        )
        else:    
            cart_item = CartItem.objects.create(
                product = product,
                quantity = 1,
                cart = cart
            )
        if len(product_variation) > 0:
            cart_item.variations.clear()
            for item in product_variation:
                cart_item.variations.add(item)
        cart_item.save()

    return redirect('cart')


def dec_cart(request,product_id,id):
    product = Product.objects.get(id = product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(user = request.user,id = id)
    else:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_item = CartItem.objects.get(cart = cart ,id = id)
    
    
    cart_item.quantity -= 1 #incrementing the cart item quantity
    if(cart_item.quantity == 0):
        cart_item.delete()
    else:
        cart_item.save()
    return redirect('cart')

def remove_cart(request,product_id,id):
    product = Product.objects.get(id = product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(user = request.user,id = id)
    else:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_item = CartItem.objects.get(cart = cart ,id = id)
    cart_item.delete()
    return redirect('cart')

def add_quantity(request,product_id,id):
    product = Product.objects.get(id = product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(user = request.user,id = id)
    else:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_item = CartItem.objects.get(cart = cart ,id = id)
    
    
    
    if(cart_item.quantity == product.stock):
        messages.info(request,"Only {:d} items available in stock".format(cart_item.quantity))
        cart_item.quantity -= 1
    cart_item.quantity += 1 #incrementing the cart item quantity
    
    cart_item.save()
    return redirect('cart')

@login_required(login_url = 'login')
def checkout(request):
    cart_id = _cart_id(request)
    total = 0
    tax = 0
    cart_prods = []
    
    try:
        if request.user.is_authenticated:
            user = Account.objects.get(pk = request.user.id)
    
            cart_prods = CartItem.objects.filter(user = user,is_active = True)

        else:
            cart = Cart.objects.get(cart_id = cart_id)
            
            cart_prods = CartItem.objects.filter(cart = cart,is_active = True)
            
        
        for item in cart_prods:
            total += (item.product.price) * (item.quantity)
            
        tax = (8/100)*total;
    except Cart.DoesNotExist:
        pass
    
    total_price = total + tax;
    data = {
        'all_prods' : cart_prods,
        'total' : total,
        'tax' : tax,
        'total_price' : total_price,
        
    }
    return render(request,'store/checkout.html',data)