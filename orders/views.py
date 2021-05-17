from django.shortcuts import render,redirect
from cart.models import CartItem
from store.models import Product
from django.http import JsonResponse
# Create your views here.
from .forms import OrderForm
import datetime
from .models import Order,Payment,OrderProduct
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


import json


def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user = request.user,is_ordered = False,order_number =  body['orderID'])
    #Store Transaction details inside payment models
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['paymentMethod'],
        amount_paid = order.order_total,
        status = body['status']

    )
    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.save()

    #move the cart items to orderProduct Table and reduce the quantity of products in original stock
    #clear cart and send email to customer
    #send order number and transaction id back to senddata method via Json response


    cart_items = CartItem.objects.filter(user = request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order = order
        orderproduct.payment = payment
        orderproduct.user = request.user
        orderproduct.product = item.product
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        cart_item = CartItem.objects.get(id =item.id)
        product_variation = cart_item.variations.all()
        order_product = OrderProduct.objects.get(id = orderproduct.id)
        order_product.variations.set(product_variation)
        order_product.save()


        product = Product.objects.get(id = item.product.id)
        product.stock -= item.quantity
        product.save()
    
    
    
    cart_items.delete()

    mail_subject = "Thank You For Your Order"
    message = render_to_string('orders/order_received_email.html',{
                    'user' : request.user,
                    'order' : order,
                })
    to_email = request.user.email

    send_email = EmailMessage(mail_subject,message,to = [to_email])

    send_email.send()

    data = {
        'order_number' : order.order_number,
        'transID' : payment.payment_id,
    }

    return JsonResponse(data)
    




    
    
    
    
















def place_order(request):
    current_user = request.user

    # If the Cart Count is less than equal to 0 then redirect back to shop
    cart_item = CartItem.objects.filter(user = current_user)
    cart_count = cart_item.count()
    if cart_count == 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    total = 0
    quantity = 0
    for item in cart_item:
        total += (item.product.price*item.quantity)
        quantity += item.quantity
    tax = (8/100)*total
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # store billing info inside order table
            data = Order()
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone_number = form.cleaned_data['phone_number']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.state = form.cleaned_data['state']
            data.pincode = form.cleaned_data['pincode']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            #Generate order Number

            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))

            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)

            data.order_number = order_number
            data.user = current_user
            data.save()
            order = Order.objects.get(user = current_user , is_ordered = False, order_number = order_number)
            context = {
                'order' : order,
                'all_prods' : cart_item,
                'total' : total,
                'tax': tax,
                'grand_total' : grand_total
            }
            return render(request,'orders/payments.html',context)
    else:
        return redirect('checkout')



def order_complete(request):
    order_number = request.GET.get('order_number')
    payment_id = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number = order_number,is_ordered = True)
        products = OrderProduct.objects.filter(order = order)
        payment = Payment.objects.get(payment_id = payment_id)
        data = {
            'order' : order,
            'products' : products,
            'payment' : payment,
        }
        return render(request,'orders/order_complete.html',data)
        
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')

    