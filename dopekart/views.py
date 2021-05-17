from django.shortcuts import render
from store.models import Product
from store.models import ReviewRating

def home(request):
    products = Product.objects.all().filter(is_available = True).order_by('created_date')

    for single_product in products:
        reviews = ReviewRating.objects.filter(product = single_product,status = True)
        
    data = {
        'products' : products,
        'reviews' :reviews
    }

    return render(request,'home.html',data)


