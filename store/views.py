from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from .forms import CreateUserForm, SearchForm
from .models import *
from .utils import cartData, guestOrder
import json
import datetime


# Create your views here.
def store(request):
    data = cartData(request)
    cart_items = data['cartItems']
    order = data['order']
    items = data['items']

    products = Product.objects.all()
    context = {'products': products, 'cartItems': cart_items}
    return render(request, 'store/store.html', context)


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(request,
                  'shop/product/list.html',
                  {'category': category,
                   'categories': categories,
                   'products': products})


def category_products(request, id, slug):
    catdata = Category.objects.get(pk=id)
    products = Product.objects.filter(category_id=id)
    category = Category.objects.all()
    context = {'products': products, 'category': category,
               'catdata': catdata}
    return render(request, 'store/category_products.html', context)


def product_detail(request, id, slug):
    # query = request.GET.get('q')
    category = Category.objects.all()

    product = Product.objects.get(pk=id)

    images = Images.objects.filter(product_id=id)
    products_picked = Product.objects.all().order_by('?')[:4]  # Random 4 products
    # comments = Comment.objects.filter(product_id=id,status='True')
    context = {'product': product, 'category': category,
               'images': images,  # 'comments': comments,
               'picked': products_picked,}
    # if product.variant != "None":  # Product have variants
    #     if request.method == 'POST':  # if we select color
    #         variant_id = request.POST.get('variantid')
    #         variant = Variants.objects.get(id=variant_id)  # selected product by click color radio
    #         colors = Variants.objects.filter(product_id=id, size_id=variant.size_id)
    #         sizes = Variants.objects.raw('SELECT * FROM  product_variants  WHERE product_id=%s GROUP BY size_id', [id])
    #         query += variant.title + ' Size:' + str(variant.size) + ' Color:' + str(variant.color)
    #     else:
    #         variants = Variants.objects.filter(product_id=id)
    #         colors = Variants.objects.filter(product_id=id, size_id=variants[0].size_id)
    #         sizes = Variants.objects.raw('SELECT * FROM  product_variants  WHERE product_id=%s GROUP BY size_id', [id])
    #         variant = Variants.objects.get(id=variants[0].id)
    #     context.update({'sizes': sizes, 'colors': colors,
    #                     'variant': variant, 'query': query
    #                     })
    return render(request, 'store/product_detail.html', context)


def cart(request):
    data = cartData(request)
    cart_items = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cart_items}
    return render(request, 'store/cart.html', context)


def checkout(request):
    data = cartData(request)
    cart_items = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cart_items}
    return render(request, 'store/checkout.html', context)


def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('Action:', action)
    print('Product:', productId)

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)


def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == order.get_cart_total:
        order.complete = True
    order.save()
    to_addresses = []
    to_addresses.append(request.user.email)
    send_mail('Onyx Women & Kids Clothing', 'Hello ' + data.name + ',' +
              '\n\nThank you for contacting us with your query. We will look into it and get in touch with you as soon as possible..\n\nOnyx Women & Kids Clothing',
              request.user.email, to_addresses)

    if order.shipping:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )

    return JsonResponse('Payment submitted..', safe=False)


def registerPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        form = CreateUserForm()
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                form.save()
                username = form.cleaned_data.get('username')
                raw_password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=raw_password)
                email = form.cleaned_data.get('email')
                Customer.objects.create(user=user, name=username, email=email)
                messages.success(request, 'Account was created for ' + username)

                to_addresses = []
                to_addresses.append(email)
                send_mail('Onyx Women & Kids Clothing', 'Dear ' + username + ',' +
                          '\n\nThank you for creating an Onyx account.To begin enjoying all the great features available to you, simply sign in with your username and password - anytime, anywhere.' +
                          '\n\nUsername: ' + username + '\n\nOnyx Women & Kids Clothing',
                          email, to_addresses)

                return redirect('login')

        context = {'form': form}
        return render(request, 'registration/register.html', context)


def loginPage(request):
    if request.user.is_authenticated:
        return redirect('store')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('store')
            else:
                messages.info(request, 'Username OR password is incorrect')

        context = {}
        return render(request, 'registration/login.html', context)


def logoutUser(request):
    logout(request)
    return redirect('store')


def contactPage(request):
    if request.method == 'POST':  # check post
        form = ContactForm(request.POST)
        if form.is_valid():
            data = ContactMessage()  # create relation with model
            data.name = form.cleaned_data['name']  # get form input data
            data.email = form.cleaned_data['email']
            data.subject = form.cleaned_data['subject']
            data.message = form.cleaned_data['message']
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()  # save data to table
            messages.success(request, "Your message has ben sent. Thank you for your message.")

            to_addresses = []
            to_addresses.append(request.user.email)
            send_mail('Onyx Women & Kids Clothing', 'Hello ' + data.name + ',' +
                      '\n\nThank you for contacting us with your query. We will look into it and get in touch with you as soon as possible..\n\nOnyx Women & Kids Clothing',
                      request.user.email, to_addresses)
            return HttpResponseRedirect('/contact')

    form = ContactForm
    context = {'form': form}
    return render(request, 'registration/contact.html', context)


def aboutPage(request):
    context = {}
    return render(request, 'registration/about.html', context)


def home(request):
    setting = Setting.objects.get(pk=1)
    category = Category.objects.all()
    products_latest = Product.objects.all().order_by('-id')[:4]  # last 4 products
    products_slider = Product.objects.all().order_by('id')[:4]  # first 4 products
    products_picked = Product.objects.all().order_by('?')[:4]  # Random 4 products
    page = "home"
    context = {'setting': setting,
               'page': page,
               'products_slider': products_slider,
               'products_latest': products_latest,
               'products_picked': products_picked,
               'category': category
               }
    return render(request, 'store/home.html', context)


def contactus(request):
    if request.method == 'POST':  # check post
        form = ContactForm(request.POST)
        if form.is_valid():
            data = ContactMessage()  # create relation with model
            data.name = form.cleaned_data['name']  # get form input data
            data.email = form.cleaned_data['email']
            data.subject = form.cleaned_data['subject']
            data.message = form.cleaned_data['message']
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()  # save data to table
            messages.success(request, "Your message has ben sent. Thank you for your message.")
            return HttpResponseRedirect('/contactus')

    category = Category.objects.all()
    setting = Setting.objects.get(pk=1)
    form = ContactForm

    context = {'setting': setting, 'form': form, 'category': category}
    return render(request, 'store/contactus.html', context)


def aboutus(request):
    setting = Setting.objects.get(pk=1)
    category = Category.objects.all()
    context = {'setting': setting, 'category': category}
    return render(request, 'store/aboutus.html', context)


def search(request):
    if request.method == 'POST':  # check post
        form = SearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']  # get form input data
            catid = form.cleaned_data['catid']
            if catid == 0:
                products = Product.objects.filter(
                    title__icontains=query)  # SELECT * FROM product WHERE title LIKE '%query%'
            else:
                products = Product.objects.filter(title__icontains=query, category_id=catid)

            category = Category.objects.all()
            context = {'products': products, 'query': query,
                       'category': category}
            return render(request, 'store/search_products.html', context)

    return HttpResponseRedirect('/')


def search_auto(request):
    if request.is_ajax():
        q = request.GET.get('term', '')
        products = Product.objects.filter(title__icontains=q)

        results = []
        for rs in products:
            product_json = {}
            product_json = rs.title #+ " > " + rs.category.title
            results.append(product_json)
        data = json.dumps(results)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)
