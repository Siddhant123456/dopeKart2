from django.shortcuts import render,get_object_or_404
from .models import Product,ProductGallery
from category.models import Category
from cart.models import CartItem,Cart
from cart.views import _cart_id
from django.http import HttpResponse
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator 
from django.db.models import Q
from .models import Variation,ReviewRating
from .forms import ReviewForm
from django.contrib import messages
from django.shortcuts import redirect
from orders.models import OrderProduct
from accounts.models import UserProfile

# Create your views here.


def store(request,category_slug = None):
    categories = None
    products = None

    if category_slug is not None:
        categories = get_object_or_404(Category,slug = category_slug)
        products = Product.objects.filter(category = categories,is_available=True)
        paginator = Paginator(products, 1)
        page = request.GET.get('page')
        paged_product = paginator.get_page(page)
    
        length = products.count()
    
    else:
        products = Product.objects.all()
        categories = products.values_list('category',flat=True).distinct()
        length = len(products)
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_product = paginator.get_page(page)
    
    
    data = {
        'products' : paged_product,
        'length' : length,
        'categories' : categories,
    }
    return render(request,'store/store.html',data)

def product_detail(request,category_slug,product_slug):
    flag = False
    quantity = 0;
    userprofile = None
    if request.user.is_authenticated:
        userprofile = UserProfile.objects.get(user = request.user)
    single_product = Product.objects.get(category__slug = category_slug,slug = product_slug)

    try:
        cart_id = Cart.objects.get(cart_id = _cart_id(request))
        in_cart = CartItem.objects.filter(cart = cart_id)
            
        
        if not in_cart:
            pass
        else:
            for item in in_cart:
                if item.product.id == single_product.id:
                    flag = True
                    quantity = item.quantity
                    break
    except Exception as e:
        pass
    is_ordered = False
    try:
        orderProduct = OrderProduct.objects.filter(user = request.user,product = single_product).exists()
        if orderProduct:
            is_ordered = True
    except:
        pass

    try:
        product_gallery = ProductGallery.objects.filter(product = single_product)

    except:
        product_gallery = None


    try:
        reviews = ReviewRating.objects.filter(product = single_product,status = True)
        data = {
        'single_product' : single_product,
        'flag' : flag,
        'quantity_product': quantity,
        'is_ordered' :is_ordered,
        'reviews' : reviews,
        'userprofile':userprofile,
        'product_gallery' : product_gallery,

    }
    except:
        data = {
        'single_product' : single_product,
        'flag' : flag,
        'quantity_product': quantity,
        'is_ordered' :is_ordered,
        'userprofile' : userprofile,
        'product_gallery' :product_gallery,
    }
        

    
    return render(request,'store/product_detail.html',data)



def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains = keyword) |  Q(product_name__icontains = keyword))
            length = len(products)
    data = {
        'products': products,
        'length' : length,

    }
    return render(request,'store/store.html',data)


def submit_review(request,product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == "POST":
        try:
            reviews = ReviewRating.objects.get(user__id = request.user.id,product__id = product_id)
            form = ReviewForm(request.POST,instance = reviews)
            form.save()
            messages.success(request,"ThankYou! Your Review has been updated")
            return redirect(url)
        
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                
                data.rating = form.cleaned_data['rating']
                
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request,"ThankYou! Your Review has been Submitted")

                return redirect(url)            