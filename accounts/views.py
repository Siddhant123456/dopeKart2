from django.contrib.auth.models import User
from django.shortcuts import render,redirect
from .forms import RegistrationForm,UserForm,UserProfileForm
from .models import Account,UserProfile
from django.contrib import messages,auth
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from cart.models import CartItem,Cart
from cart.views import _cart_id
from store.models import Variation
from orders.models import Order,OrderProduct
import requests
from django.shortcuts import get_object_or_404
#verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
# Create your views here.


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]
            
            user = Account.objects.create_user(first_name = first_name,last_name = last_name,email = email,username = username,password = password)
            user.phone_number = phone_number
            user.save()
            user_profile = UserProfile()
            user_profile.user = user
            user_profile.image = 'default/default.png'
            user_profile.save()

            current_site = get_current_site(request)

            mail_subject = "Please Verify your Account"
            message = render_to_string('accounts/account_verification_email.html',{
                'user' : user,
                'domain': current_site,
                'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                'token' : default_token_generator.make_token(user)
            })
            to_email = email

            send_email = EmailMessage(mail_subject,message,to = [to_email])

            send_email.send()

            #messages.success(request,"Thank YOu For Registring with us. We have Sent a Verfication email to your email address")
            
            return redirect('/accounts/login/?command=verification&email='+email)
    
    else:
        form = RegistrationForm()
    data = {
        'form' : form
    }
    return render(request,'accounts/register.html',data)


def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        user = authenticate(email = email,password = password)
        
        
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id = _cart_id(request))
                is_cart_items_exist = CartItem.objects.filter(cart = cart).exists()
                if is_cart_items_exist:
                    cart_item = CartItem.objects.filter(cart = cart)
                    
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []

                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)
                    
                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id = item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()

            except:
                print("except block")
            auth.login(request,user)
            messages.success(request,"You are Now Logged in")
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                # next=/cart/checkout
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    next_page = params['next']
                    return redirect(next_page)
            except:
                return redirect('dashboard')
                
        else:
            messages.error(request,"Invalid login Credentials")
            return redirect('login')
    return render(request,'accounts/login.html')

@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    messages.success(request,"You are Logged out")
    return redirect('login')


def activate(request,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk = uid)

    except(TypeError , ValueError , OverflowError , Account.DoesNotExist()):
        user = None

    if user is not None and default_token_generator.check_token(user,token):
        user.is_active = True
        user.save()
        messages.success(request,'Congratulations! Your Account is Activated')
        return redirect('login')

    else:
        messages.error(request,'Invalid Activation Link')
        return redirect('register')

@login_required(login_url='login')
def dashboard(request):
    order = Order.objects.order_by('-created_at').filter(user = request.user,is_ordered = True)
    count = order.count()
    profile = UserProfile.objects.get(user = request.user)
    data = {
        'orders': order,
        'count' : count,
        'profile': profile
    }
    return render(request, 'accounts/dashboard.html',data)


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email = email).exists():
            user = Account.objects.get(email__iexact = email)
            current_site = get_current_site(request)

            mail_subject = "Reset Your Password"
            message = render_to_string('accounts/reset_password_email.html',{
                'user' : user,
                'domain': current_site,
                'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                'token' : default_token_generator.make_token(user)
            })
            to_email = email
            send_email = EmailMessage(mail_subject,message,to = [to_email])
            send_email.send()
            messages.success(request,"Password Reset Email Has Been Sent to Your Email")
            return redirect('login')
        else:
            messages.error(request,"Account Does Not exist")
            return redirect('forgotPassword')

    return render(request,'accounts/forgotPassword.html')


def resetPasswordValidate(request,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk = uid)

    except(TypeError , ValueError , OverflowError , Account.DoesNotExist()):
        user = None

    if user is not None and default_token_generator.check_token(user,token):
        request.session['uid'] = uid
        messages.success(request,"Please Reset Your Password")

        return redirect('resetPassword')

    else:
        messages.error(request,"This Link Has Been Expired")
        return redirect('login')


def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk = uid)
            user.set_password(password)
            user.save()
            messages.success(request,"Password Reset Successful")
            return redirect('login')
        else:
            messages.error(request,"Password does not Match")
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')

@login_required(login_url='login')
def my_orders(request):
    order = Order.objects.order_by('-created_at').filter(user = request.user,is_ordered = True)
    data = {
        'orders' : order
    }
    return render(request,'accounts/my_orders.html',data)

@login_required(login_url='login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile , user = request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST,instance=request.user)
        profile_form = UserProfileForm(request.POST,request.FILES,instance=userprofile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request,"Your Profile has been Updated")
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    data = {
        'user_form':user_form,
        'profile_form' : profile_form,
        'userprofile' : userprofile
    }
    return render(request,'accounts/edit_profile.html',data)


@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_pass = request.POST['current_password']
        new_pass = request.POST['new_password']
        confirm_pass = request.POST['confirm_new_password']

        user = Account.objects.get(username__exact = request.user.username)

        if new_pass == confirm_pass:
            success = user.check_password(current_pass)
            if success:
                user.set_password(new_pass)
                user.save()
                messages.success(request,"Password Updated Succesfully! please Login")
                return redirect('change_password')
            else:
                messages.error(request,"Please Enter Correct Current Password")
                return redirect('change_password')
        else:
            messages.error(request,"New Password and Confirm New Password Do not Match")
            return redirect('change_password')
        
    return render(request,'accounts/change_password.html')

@login_required(login_url='login')
def order_detail(request,order_id):
    order = None
    product = None
    try:
        order = Order.objects.get(order_number = order_id,is_ordered = True)
        products = OrderProduct.objects.filter(order = order)
    except:
        pass
        
    data = {
        'order' : order,
        'products' : products,
    }
    return render(request,'accounts/order_detail.html',data)
