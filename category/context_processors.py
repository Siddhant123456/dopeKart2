from .models import Category
from cart.models import Cart,CartItem
from cart.views import _cart_id

def menu_links(request):
    links = Category.objects.all()
    return dict(links = links)

def total_count(request):
    quantity = 0;
    
    try:
        if request.user.is_authenticated:
            user = request.user
            cart_prods = CartItem.objects.filter(user = user,is_active = True)
        else:
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart_prods = CartItem.objects.filter(cart = cart,is_active = True)
        for item in cart_prods:
            quantity += item.quantity
    except Exception as e:
        pass
    
    return dict(quantity = quantity)
    
    
        