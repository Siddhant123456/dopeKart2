from django.urls import path
from .import views
urlpatterns = [
    path('',views.cart,name = "cart"),
    path('add_cart/<int:product_id>/',views.add_cart,name = "add_cart"),
    path('dec_cart/<int:product_id>/<int:id>',views.dec_cart,name = "dec_cart"),
    path('remove_cart/<int:product_id>/<int:id>',views.remove_cart,name = "remove_cart"),
    path('add_quantity/<int:product_id>/<int:id>',views.add_quantity,name = "add_quantity"),
    path('checkout/',views.checkout,name = "checkout"),
    
]