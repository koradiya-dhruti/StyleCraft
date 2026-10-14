from django.shortcuts import render
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from .models import *
from .tokens import create_token, verify_token, create_delivery_token, verify_delivery_token
from django.db import transaction
from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Q
from operator import itemgetter
import re
from decimal import Decimal
import requests
from django.conf import settings
import random
from django.core.mail import send_mail
from django.template.loader import get_template
from xhtml2pdf import pisa

# Create your views here.
def index_page(request):
    return render(request, 'index.html')

def wishlist_page(request):
    return render(request, "wishlist.html")

def about_page(request):
    return render(request, 'about.html')

def contact_page(request):
    return render(request, 'contact.html')

def product_detail_page(request, pid):
    productObj = Product.objects.get(id=pid)
    ProductImages = ProductImage.objects.filter(product_id=pid)
    productVariants = ProductVariant.objects.filter(product_id=pid)

    sizes = []
    colors = []

    for variant in productVariants:
        if variant.size and variant.size not in sizes:
            sizes.append(variant.size)

        if variant.color:
            color_exists = False

            for color in colors:
                if color["name"] == variant.color:
                    color_exists = True
                    break

            if not color_exists:
                colors.append({
                    "name": variant.color,
                    "code": variant.color_code
                })

    reviews = Review.objects.filter(product_id=productObj).order_by("-created_at")

    return render(request, 'product-detail.html', {
        'products': productObj,
        'images': ProductImages,
        'variants': productVariants,
        'sizes': sizes,
        'colors': colors,
        'reviews': reviews
    })

def product_page(request):
    return render(request, 'product.html')

def shoping_cart_page(request):
    return render(request, 'shoping-cart.html')

# def login_page(request):
#     return render(request, 'login.html')

def register_page(request):
    return render(request, 'register.html')

def profile_page(request):
    return render(request, 'profile.html')

def forgot_password_page(request):
    return render(request, 'forgot-password.html')

def checkout_page(request):
    return render(request, 'checkout.html')

def order_success_page(request):
    return render(request, "order-success.html")

def feedback_page(request, orderId, orderItemId):
    return render(request, "feedback.html",{"orderId": orderId, "orderItemId": orderItemId})

# DELIVERY PARTNER 
def delivery_partner_login_page(request):
    return render(request, "delivery-partner-login.html")

def delivery_dashboard_page(request):
    return render(request, "delivery-dashboard.html")

def pending_shipments_page(request):
    return render(request, "pending-shipments.html")

def my_shipments_page(request):
    return render(request, "my-shipments.html")

def out_for_delivery_page(request):
    return render(request, "out-for-delivery.html")

def delivered_shipments_page(request):
    return render(request, "delivered-shipments.html")

def exception_shipments_page(request):
    return render(request, "exception-shipments.html")


# REGISTER API
@csrf_exempt
@api_view(["POST"])
def register(request):
    firstName = request.data.get('firstName')
    lastName = request.data.get('lastName')
    userEmail = request.data.get('userEmail')
    dialCode = request.data.get('dialCode')
    phoneNumber = request.data.get('phoneNumber')
    password = request.data.get('password')
    confirmPassword = request.data.get('confirmPassword')

    # REQUIRED FIELD
    if not firstName or not lastName or not userEmail or not dialCode or not phoneNumber or not password or not confirmPassword:
        return JsonResponse({"message": "First name, last name, user email, dialcode, phone number, password and confirm password all fields are required."}, status=400)

    # EMAIL VALIDATION
    if "@" not in userEmail or "." not in userEmail:
        # r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$" 
        return JsonResponse({"message": "Invalid email format."},status=400)

    # Check duplicate email
    if User.objects.filter(email=userEmail).exists():
        return JsonResponse({"message": "Email already registered."}, status=400)

    # PHONE NUMBER VALIDATION
    phoneNumber = str(phoneNumber)

    if len(phoneNumber) != 10:
        return JsonResponse({"message": "Phone number must have exactly 10 digits."},status=400)

    for digit in phoneNumber:

        if digit < '0' or digit > '9':
            return JsonResponse({"message": "Phone number must contain only digits."},status=400)

    # PASSWORD VALIDATION
    has_upper = False
    has_lower = False
    has_number = False
    has_special = False

    for char in password:
        if char >= 'A' and char <= 'Z':
            has_upper = True
        elif char >= 'a' and char <= 'z':
            has_lower = True
        elif char >= '0' and char <= '9':
            has_number = True
        else:
            has_special = True

    if not has_upper or not has_lower or not has_number or not has_special:
        return JsonResponse({"message": "Password must contain at least one A-Z character, a-z character, number (0-9) and special character."},status=400)
    
    if password != confirmPassword:
        return JsonResponse({"message": "password and confirm password do not match."}, status=400)

    # CREATE JSON 
    try:
        User.objects.create(
            first_name = firstName,
            last_name = lastName,
            email = userEmail,
            dial_code = dialCode,
            phone_number = phoneNumber,
            password = password,
        )
        return JsonResponse({"message": "User Register successfully.", "status":True}, status=200)
    
    except Exception as e:
        return JsonResponse({"error": f"{str(e)}"}, status=500)

# LOGIN API
@csrf_exempt
@api_view(["POST"])
def login(request):
    userEmail = request.data.get('userEmail')
    password = request.data.get('password')

    if not userEmail or not password:
        return JsonResponse({"message": "Email and password are required."}, status=400)

    userObj = User.objects.filter(email=userEmail).first()

    if not userObj:
        return JsonResponse({"error": "User not found."}, status=404)
    
    if userObj.password == password:
        token = create_token(userObj)
        return JsonResponse({"message":"Login Successfull.", "token":token,
                             "user": {
                                "id": userObj.id,
                                "firstName": userObj.first_name,
                                "lastName": userObj.last_name,
                                "email": userObj.email,
                                "dialCode": userObj.dial_code,
                                "phoneNumber": userObj.phone_number,
                                "profileImage": userObj.profile_image.url if userObj.profile_image else None
                        }}, status=200)
    
    else:
        return JsonResponse({"error": "Password is incorrect"}, status=401)

# WISHLIST API
@csrf_exempt
@api_view(["POST"])
def wishlist(request):
    token = request.headers.get('Authorization')
    productId = request.data.get('productId')

    # VERIFY LOGIN USER
    userId = verify_token(token)
    if not userId:
        return JsonResponse({"message": "Please login first."}, status=401)

    userObj = User.objects.get(id=userId)

    if not productId:
        return JsonResponse({"message": "product id is required."}, status=400)

    # ACTIVE PRODUCT
    productObj = Product.objects.filter(id=productId, status=True).first()
    if not productObj:
        return JsonResponse({"message": "Product is inActive."}, status=400)

    # WISHLIST
    wishlist_item = Wishlist.objects.filter(user_id=userObj, product_id=productObj).first()
    if wishlist_item:
        wishlist_item.delete()
        return JsonResponse({"message": "Product removed from wishlist.", "status":False}, status=200)

    Wishlist.objects.create(
        user_id = userObj,
        product_id = productObj
    )
    return JsonResponse({"message": "Product added to wishlist.", "status":True}, status=200)

@api_view(["GET"])
def get_wishlist(request):

    token = request.headers.get("Authorization")

    # VERIFY LOGIN USER
    userId = verify_token(token)
    
    if not userId:
        return JsonResponse({
            "message": "Please login first."
        }, status=401)

    try:
        userObj = User.objects.get(id=userId)

        wishlistItems = Wishlist.objects.filter(
            user_id=userObj,
            product_id__status=True
        )

        wishlist = []

        for item in wishlistItems:

            productObj = item.product_id

            imageObj = ProductImage.objects.filter(
                product_id=productObj
            ).first()

            variantObj = ProductVariant.objects.filter(
                product_id=productObj,
                status=True
            ).first()

            image = None

            if imageObj:
                image = imageObj.image.url

            price = 0

            if variantObj:
                price = variantObj.selling_price

            wishlist.append({
                "wishlistId": item.id,
                "productId": productObj.id,
                "productName": productObj.name,
                "shortDescription": productObj.short_description,
                "image": image,
                "price": price
            })

        return JsonResponse({
            "message": "Wishlist fetched successfully.",
            "wishlist": wishlist,
            "count": len(wishlist)
        }, status=200)

    except User.DoesNotExist:

        return JsonResponse({
            "message": "User not found."
        }, status=404)

# ADD TO CART API
@csrf_exempt
@api_view(["POST"])
def add_to_cart(request):
    token = request.headers.get("Authorization")
    variantId = request.data.get("variantId")
    quantity = int(request.data.get("quantity", 1))

    # VERIFY USER LOGIN
    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    try:
        userObj = User.objects.filter(id=userIdOrError).first()
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)

    # VALIDATION
    if not variantId:
        return JsonResponse({"message": "Variant id is required."}, status=400)

    # CHECK PRODUCT VARIANT
    try:
        variantObj = ProductVariant.objects.get(id=variantId, status=True)
    except ProductVariant.DoesNotExist:
        return JsonResponse({"error": "Product variant not found."}, status=404)

    # CHECK SHOPPING CART
    try:
        cartObj = ShoppingCart.objects.get(user_id=userObj)
    except ShoppingCart.DoesNotExist:
        cartObj = ShoppingCart.objects.create(user_id=userObj)

    # CART ITEM
    try:
        cartItem = CartItem.objects.get(
            cart_id = cartObj,
            product_variant_id = variantObj
        )
        newQuantity = cartItem.quantity + quantity

        if newQuantity > variantObj.stock_quantity:
            return JsonResponse(
                {"message": "Insufficient stock."},
                status=400
            )

        cartItem.quantity = newQuantity
        cartItem.price = variantObj.selling_price
        cartItem.total = variantObj.selling_price * newQuantity
        cartItem.save()
        return JsonResponse({"message": "Cart quantity updated successfully."}, status=200)
    
    except CartItem.DoesNotExist:
        price = variantObj.selling_price
        total = price * quantity

        CartItem.objects.create(
            cart_id = cartObj,
            product_variant_id = variantObj,
            quantity = quantity,
            price = price,
            total = total
        )
        return JsonResponse({"message": "Product added to cart successfully.", "status":True}, status=200)

# GET CART API
@csrf_exempt
@api_view(["GET"])
def get_cart(request):
    token = request.headers.get("Authorization")

    # VERIFY USER LOGIN
    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)
    
    try:
        userObj = User.objects.get(id=userIdOrError)
        cartObj = ShoppingCart.objects.get(user_id=userObj)
        cartItemObj = CartItem.objects.filter(cart_id=cartObj)
        cart = []
        for i in cartItemObj:
            variantObj = i.product_variant_id
            productObj = variantObj.product_id
            productImageObj = ProductImage.objects.filter(product_id=productObj).first()
            cart.append({
                'cartItemId':i.id,
                'variantId': variantObj.id,
                "productName": productObj.name,
                "image": productImageObj.image.url if productImageObj and productImageObj.image else None,
                "color": variantObj.color,
                "size": variantObj.size,
                'quantity': i.quantity,
                'price': i.price,
                'total': i.total
        })
        return JsonResponse({"cartId":cartObj.id, "cartItem":cart}, status=200)
   
    except ShoppingCart.DoesNotExist:
        return JsonResponse({"error": "Cart not found."}, status=404)

# GET SINGLE CART ITEM API
@csrf_exempt
@api_view(["GET"])
def get_single_cartitem(request):
    token = request.headers.get("Authorization")
    id = request.GET.get("id")

    # VERIFY USER LOGIN
    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)
    
    try:
        userObj = User.objects.get(id=userIdOrError)
        cartObj = ShoppingCart.objects.get(user_id=userObj)
        cartItemObj = CartItem.objects.get(id=id, cart_id=cartObj)

        cartItem = {
            'cartId': cartItemObj.cart_id.id,
            'productVariantId': cartItemObj.product_variant_id.id,
            'quantity': cartItemObj.quantity,
            'price': cartItemObj.price,
            'total': cartItemObj.total
        }
        return JsonResponse({"cartItem": cartItem}, status=200)
    except ShoppingCart.DoesNotExist:
        return JsonResponse({"error": "Cart not found."}, status=404)
    except CartItem.DoesNotExist:
        return JsonResponse({"error": "Cart item not found."}, status=404)

# UPDATE CART ITEM API
@csrf_exempt
@api_view(["PUT"])
def update_cartitem(request):
    token = request.headers.get("Authorization")
    id = request.GET.get("id")
    quantity = request.data.get("quantity")

    # VERIFY USER LOGIN
    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)
    quantity = int(quantity)
    if quantity <= 0:
        return JsonResponse({"message": "Quantity is greater than 0"}, status=400)
    try:
        userObj = User.objects.get(id=userIdOrError)
        cartObj = ShoppingCart.objects.get(user_id=userObj)
        cartItemObj = CartItem.objects.get(id=id, cart_id=cartObj.id)
        variant = cartItemObj.product_variant_id
        if quantity > variant.stock_quantity:
            return JsonResponse({"message": "Insufficient stock."}, status=400)

        cartItemObj.quantity = quantity
        cartItemObj.total = cartItemObj.price * cartItemObj.quantity
        cartItemObj.save()
        return JsonResponse({"message": "Updated successfully.", "quantity":cartItemObj.quantity, "total":cartItemObj.total}, status=200)
    except CartItem.DoesNotExist:
        return JsonResponse({"error": "Cart Item not found."}, status=404)

# REMOVE CART ITEM API 
@csrf_exempt
@api_view(["DELETE"])
def remove_cartitem(request):
    token = request.headers.get("Authorization")
    id = request.GET.get("id")

    # VERIFY USER LOGIN
    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    try:
        userObj = User.objects.get(id=userIdOrError)
        cartObj = ShoppingCart.objects.get(user_id=userObj)
        cartItemObj = CartItem.objects.get(id=id, cart_id=cartObj)
        cartItemObj.delete()
        return JsonResponse({"message": "Cart item removed successfully."}, status=200)
    
    except CartItem.DoesNotExist:
        return JsonResponse({"error": "Cart item not found."}, status=404)

# REMOVE CART API
@csrf_exempt
@api_view(["DELETE"])
def remove_cart(request):
    token = request.headers.get("Authorization")

    # VERIFY USER LOGIN
    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)
    
    try:
        userObj = User.objects.get(id=userIdOrError)
        cartObj = ShoppingCart.objects.get(user_id=userObj)
        cartObj.delete()
        return JsonResponse({"message": "Cart removed successfully."}, status=200)
    
    except ShoppingCart.DoesNotExist:
        return JsonResponse({"error": "Cart not found."}, status=404)

# GET CATEGORY API
@api_view(["GET"])
def get_category(request):
    try:
        categoryObj = Category.objects.filter(status=True, parent_category_id=None)
        categoryItem = []
        for i in categoryObj:
            categoryItem.append({
                'id': i.id,
                'name': i.name,
                'description': i.description,
                'image': i.image.url if i.image  else 'No image'
            })
        return JsonResponse({"categoryItem": categoryItem}, status=200)
    except Category.DoesNotExist:
        return JsonResponse({"error": "category not found."}, status=404)

# GET SUBCATEGORY API
@api_view(["GET"])
def get_sub_category(request):

    try:
        category = request.GET.get("category")

        if not category:
            categoryObj = Category.objects.filter(status=True, parent_category_id__isnull=False)
        else:
            parentCategory = Category.objects.filter(status=True, parent_category_id__isnull=True, name__iexact=category).first()

            if not parentCategory:
                return JsonResponse({"categoryItem": []}, status=200)

            categoryObj = Category.objects.filter(status=True, parent_category_id=parentCategory)

        categoryItem = []
        for i in categoryObj:
            categoryItem.append({
                "id": i.id,
                "name": i.name,
                "description": i.description,
                "image": i.image.url if i.image else "No image"
                })

        return JsonResponse({"categoryItem": categoryItem}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

# GET SINGLE CATEGORY API
@api_view(["GET"])
def get_single_category(request):
    categoryId = request.GET.get("id")
    if not categoryId:
        return JsonResponse({"message": "Category Id is required."}, status=400)
    try:
        categoryObj = Category.objects.filter(id=categoryId, status=True)
        categoryItem = []
        for i in categoryObj:
            categoryItem.append({
                'name': i.name,
                'description': i.description,
                'image': i.image.url if i.image else None
            })
        return JsonResponse({"categoryItem": categoryItem}, status=200)
    except Category.DoesNotExist:
        return JsonResponse({"error": "Category not found."}, status=404)

# GET BRAND API
@api_view(["GET"])
def get_brand(request):
    try:
        brandObj = Brand.objects.filter(status=True)
        brandItem = []
        for i in brandObj:
            brandItem.append({
                'id': i.id,
                'name': i.name,
                'logo': i.logo.url if i.logo else None,
                'description': i.description,
                'website': i.website
            })
        return JsonResponse({"brandItem": brandItem}, status=200)
    except Brand.DoesNotExist:
        return JsonResponse({"error": "Brand not found."}, status=404)

# GET SINGLE BRAND API
@api_view(["GET"])
def get_single_brand(request):
    brandId = request.GET.get("id")
    if not brandId:
        return JsonResponse({"message": "Brand Id is required."}, status=400)
    try:
        brandObj = Brand.objects.filter(id=id, status=True)
        brandItem = []
        for i in brandObj:
            brandItem.append({
                'name': i.name,
                'logo': i.logo.url if i.logo else None,
                'description': i.description,
                'website': i.website
            })
        return JsonResponse({"brandItem": brandItem}, status=200)
    except Brand.DoesNotExist:
        return JsonResponse({"error": "Brand not found."}, status=404)

# GET ALL PRODUCTS API
# @api_view(["GET"])
# def get_all_products(request):
#     try:
#         productObj = Product.objects.filter(status=True)
#         products = []

#         for product in productObj:
        
#             productImageObj = ProductImage.objects.filter(product_id=product)

#             variantObj = ProductVariant.objects.filter(product_id=product, status=True)

#             productImages = []
#             for productImageItem in productImageObj:
#                 productImages.append({
#                     'id': productImageItem.id,
#                     'image': productImageItem.image.url if productImageItem.image else None,
#                     'altText': productImageItem.alt_text
#                 })

#             variants = []
#             for variantitem in variantObj:
#                 variants.append({
#                     'id': variantitem.id,
#                     'color': variantitem.color,
#                     'colorCode': variantitem.color_code,
#                     'size': variantitem.size,
#                     'mrp': variantitem.mrp,
#                     'sellingPrice': variantitem.selling_price,
#                     'costPrice': variantitem.cost_price,
#                     'stockQuantity': variantitem.stock_quantity,
#                     'minimumStock': variantitem.minimum_stock
#                 })
          
#             products.append({
#                 'id': product.id,
#                 'name': product.name,
#                 'categoryId': product.category_id.id,
#                 'barndId': product.brand_id.id,
#                 'shortDescription': product.short_description,
#                 'description': product.description,
#                 'gender': product.gender,
#                 'variant': variants,
#                 'image': productImages
#             })
#         return JsonResponse({"products": products}, status=200)
#     except Product.DoesNotExist:
#         return JsonResponse({"error": "Product not found."}, status=404)

# GET SINGLE PRODUCT API
@api_view(["GET"])
def get_single_product(request):
    productId = request.GET.get("id")

    if not productId:
        return JsonResponse({"message": "Product Id is required."}, status=400)

    try:
        productObj = Product.objects.get(id=productId, status=True)
        
        productImageObj = ProductImage.objects.filter(product_id=productObj)

        variantObj = ProductVariant.objects.filter(product_id=productObj, status=True)

        productImages = []
        for productImageItem in productImageObj:
            productImages.append({
                'id': productImageItem.id,
                'image': productImageItem.image.url if productImageItem.image else None,
                'altText': productImageItem.alt_text
            })

        variants = []
        for variantitem in variantObj:
            variants.append({
                'id': variantitem.id,
                'color': variantitem.color,
                'colorCode': variantitem.color_code,
                'size': variantitem.size,
                'mrp': variantitem.mrp,
                'sellingPrice': variantitem.selling_price,
                'costPrice': variantitem.cost_price,
                'stockQuantity': variantitem.stock_quantity,
                'minimumStock': variantitem.minimum_stock
            })
        
        product = ({
            'id': productObj.id,
            'name': productObj.name,
            'categoryId': productObj.category_id.id,
            'barndId': productObj.brand_id.id,
            'shortDescription': productObj.short_description,
            'description': productObj.description,
            'gender': productObj.get_gender_display(),
            'variant': variants,
            'image': productImages
        })
        return JsonResponse({"products": product}, status=200)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found."}, status=404)

@api_view(["GET"])
def get_countries(request):

    countries = Country.objects.all()

    countryList = []

    for country in countries:
        countryList.append({
            "countryId": country.country_id,
            "countryName": country.country_name
        })

    return JsonResponse({
        "country": countryList
    }, status=200)

@api_view(["GET"])
def get_states(request):

    countryId = request.GET.get("countryId")

    if not countryId:
        return JsonResponse({
            "message": "Country id is required."
        }, status=400)

    states = State.objects.filter(
        country_id=countryId
    )

    stateList = []

    for state in states:
        stateList.append({
            "stateId": state.state_id,
            "stateName": state.state_name
        })

    return JsonResponse({
        "state": stateList
    }, status=200)

@api_view(["GET"])
def get_cities(request):

    stateId = request.GET.get("stateId")

    if not stateId:
        return JsonResponse({
            "message": "State id is required."
        }, status=400)

    cities = City.objects.filter(
        state_id=stateId
    )

    cityList = []

    for city in cities:
        cityList.append({
            "cityId": city.city_id,
            "cityName": city.city_name
        })

    return JsonResponse({
        "city": cityList
    }, status=200)

@api_view(["GET"])
def get_areas(request):

    cityId = request.GET.get("cityId")

    if not cityId:
        return JsonResponse({
            "message": "City id is required."
        }, status=400)

    areas = Area.objects.filter(
        city_id=cityId
    )

    areaList = []

    for area in areas:
        areaList.append({
            "areaId": area.area_id,
            "areaName": area.area_name
        })

    return JsonResponse({
        "area": areaList
    }, status=200)

# GET ADDRESS API
@csrf_exempt
@api_view(["GET"])
def get_addresses(request):
    token = request.headers.get('Authorization')

    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)
    
    try:
        userObj = User.objects.get(id=userIdOrError)
        addressObj = Address.objects.filter(user_id=userObj)
        addresses = []
        for i in addressObj:
            addresses.append({
                'id': i.id,
                'userId': i.user_id.id,
                'fullName': i.full_name,
                'dialCode': i.dial_code,
                'phoneNumber': i.phone_number,
                'addressLine1': i.address_line1,
                'addressLine2': i.address_line2,
                'countryId': i.country_id.country_id,
                'stateId': i.state_id.state_id,
                'cityId': i.city_id.city_id,
                'areaId': i.area_id.area_id,
                'postalCode': i.postal_code,
                'landmark': i.landmark,
                'addresstype': i.get_address_type_display()
            })
        return JsonResponse({"address": addresses}, status=200)
    except Address.DoesNotExist:
        return JsonResponse({"error": "Address not found."}, status=404)

# GET SINGLE ADDRESS 
@csrf_exempt
@api_view(["GET"])
def get_single_address(request):
    token = request.headers.get("Authorization")
    addressId = request.GET.get("id")

    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    if not addressId:
        return JsonResponse({"message": "Address Id is required."}, status=400)
    
    try:
        userObj = User.objects.get(id=userIdOrError)
        addressObj = Address.objects.get(id=addressId, user_id=userObj)
        address = {
            'id': addressObj.id,
            'userId': addressObj.user_id.id,
            'fullName': addressObj.full_name,
            'dialCode': addressObj.dial_code,
            'phoneNumber': addressObj.phone_number,
            'addressLine1': addressObj.address_line1,
            'addressLine2': addressObj.address_line2,
            'city': addressObj.city,
            'state': addressObj.state,
            'country': addressObj.country,
            'postalCode': addressObj.postal_code,
            'landmark': addressObj.landmark,
            'addresstype': addressObj.get_address_type_display()
        }
        return JsonResponse({"address": address}, status=200)
    except Address.DoesNotExist:
        return render({"error": "Address not found."}, status=404)

# ADD ADDERSS API
@csrf_exempt
@api_view(["POST"])
def add_address(request):
    token = request.headers.get("Authorization")

    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    fullName = request.data.get("fullName")
    dialCode = request.data.get("dialCode")
    phoneNumber = request.data.get("phoneNumber")
    addressLine1 = request.data.get("addressLine1")
    addressLine2 = request.data.get("addressLine2")
    countryId = request.data.get("countryId")
    stateId = request.data.get("stateId")
    cityId = request.data.get("cityId")
    areaId = request.data.get("areaId")
    postalCode = request.data.get("postalCode")
    landmark = request.data.get("landmark")
    addressType = request.data.get("addressType")

    try:
        userObj = User.objects.get(id=userIdOrError)

        countryObj = Country.objects.filter(country_id=countryId).first()
        stateObj = State.objects.filter(state_id=stateId).first()
        cityObj = City.objects.filter(city_id=cityId).first()
        areaObj = Area.objects.filter(area_id=areaId).first()

        addressObj = Address.objects.create(
            user_id = userObj,
            full_name = fullName,
            dial_code = dialCode,
            phone_number = phoneNumber,
            address_line1 = addressLine1,
            address_line2 = addressLine2,
            country_id=countryObj,
            state_id=stateObj,
            city_id=cityObj,
            area_id=areaObj,
            postal_code = postalCode,
            landmark = landmark,
            address_type = addressType
        )
        return JsonResponse({"message": "Address added successfully.", "addressId": addressObj.id}, status=200)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)

# UPDATE ADDRESS API
@csrf_exempt
@api_view(["PUT"])
def update_address(request):
    token = request.headers.get("Authorization")
    addressId = request.GET.get("id")

    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    if not addressId:
        return JsonResponse({"message": "Address Id is required."}, status=400)

    try:
        userObj = User.objects.get(id=userIdOrError)
        addressobj = Address.objects.get(id=addressId, user_id=userObj)

        addressobj.full_name = request.data.get("fullName")
        addressobj.dial_code = request.data.get("dialCode")
        addressobj.phone_number = request.data.get("phoneNumber")
        addressobj.address_line1 = request.data.get("addressLine1")
        addressobj.address_line2 = request.data.get("addressLine2")
        addressobj.city = request.data.get("city")
        addressobj.state = request.data.get("state")
        addressobj.country = request.data.get("country")
        addressobj.postal_code = request.data.get("postalCode")
        addressobj.landmark = request.data.get("landmark")
        addressobj.address_type = request.data.get("addressType")
        addressobj.save()

        return JsonResponse({"message": "Address updated successfully."}, status=200)
    except Address.DoesNotExist:
        return JsonResponse({"error": "Address not found."}, status=404)
    
def calculate_shipping_charge(
    store_state_id,
    store_city_id,
    store_area_id,
    customer_state_id,
    customer_city_id,
    customer_area_id
):
    if store_area_id == customer_area_id:
        return Decimal("0")

    elif store_city_id == customer_city_id:
        return Decimal("50")

    elif store_state_id == customer_state_id:
        return Decimal("100")

    else:
        return Decimal("200")

# PLACE ORDER API
@csrf_exempt
@api_view(["POST"])
def place_order(request): 
    token = request.headers.get("Authorization")
    addressId = request.data.get("addressId")
    paymentMode = int(request.data.get("paymentMode"))

    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    if not addressId or not paymentMode:
        return JsonResponse({"message": "Address Id and Payment mode is required."}, status=400)

    if paymentMode != 1 and paymentMode != 2 and paymentMode != 3:
        return JsonResponse({"message": "Payment mode 1 for COD, 2 for Online and 3 for Card."}, status=400)

    # CARD DETAILS
    cardHolderName = None
    cardNumber = None
    cardExpireDate = None
    cardCvv = None

    if paymentMode == 3:
        cardHolderName = request.data.get("cardHolderName")
        cardNumber = request.data.get("cardNumber")
        cardExpireDate = request.data.get("cardExpireDate")
        cardCvv = request.data.get("cardCvv")

        if not cardHolderName:
            return JsonResponse({"message": "Card holder name is required."}, status=400)

        if not cardNumber:
            return JsonResponse({"message": "Card number is required."}, status=400)

        if len(cardNumber) != 16:
            return JsonResponse({"message": "Card number must be 16 digits."}, status=400)

        if not cardExpireDate:
            return JsonResponse({"message": "Card expiry date is required."}, status=400)

        if not re.match(r"^(0[1-9]|1[0-2])/\d{2}$", cardExpireDate):
            return JsonResponse({"message": "Card expiry date must be in MM/YY format."}, status=400)
        
        if not cardCvv:
            return JsonResponse({"message": "CVV is required."}, status=400)

        if len(cardCvv) != 3:
            return JsonResponse({"message": "CVV must be 3 digits."}, status=400)

    try:
        userObj = User.objects.get(id=userIdOrError)
        # CART
        cartObj = ShoppingCart.objects.get(user_id=userObj)
        cartItemObj = CartItem.objects.filter(cart_id=cartObj)

        if not cartItemObj:
            return JsonResponse({"message": "Cart is empty."}, status=400)

        # ADDRESS
        addressObj = Address.objects.get(id=addressId, user_id=userObj)

        shippingObj = ShippingCharge.objects.first()

        if not shippingObj:
            return JsonResponse({
                "message": "Store shipping location is not configured."
            }, status=404)

        # SUBTOTAL
        subTotal = 0

        for item in cartItemObj:
            variant = item.product_variant_id

            if not variant.status:
                return JsonResponse({"message": "Product variant Id is not available."}, status=400)

            if item.quantity > variant.stock_quantity:
                return JsonResponse({"message": "Insufficient stock."}, status=400)
        
            subTotal += item.total

        # TAX
        tax = subTotal * 18 / 100

        # SHIPPING

        storeStateId = 1
        storeCityId = 1
        storeAreaId = 1

        customerStateId = addressObj.state_id.state_id
        customerCityId = addressObj.city_id.city_id
        customerAreaId = addressObj.area_id.area_id

        shippingCharge = calculate_shipping_charge(
            storeStateId,
            storeCityId,
            storeAreaId,
            customerStateId,
            customerCityId,
            customerAreaId
        )

        # TOTAL

        totalAmount = subTotal + tax + shippingCharge

        # PAYMENT STATUS
        if paymentMode == 1:
            paymentStatus = 1
        else:
            paymentStatus = 2

        # ORDER NUMBER
        lastOrder = Order.objects.last()

        if lastOrder:
            lastNumber = int(lastOrder.order_number.replace("DTL", ""))
            orderNumber = lastNumber + 1
        else:
            orderNumber = 1

        orderNumber = "DTL" + str(orderNumber)

        with transaction.atomic():
            cardObj = None

            if paymentMode == 3:

                # Find card using card number
                cardObj = Card.objects.select_for_update().filter(number=cardNumber, is_active=True).first()

                # CARD NUMBER CHECK
                if not cardObj:
                    return JsonResponse({"message": "Card number is incorrect."}, status=400)

                # HOLDER NAME CHECK
                if cardObj.holder_name.strip().lower() != cardHolderName.strip().lower():
                    return JsonResponse({"message": "Card holder name is incorrect."}, status=400)

                # CVV CHECK
                if str(cardObj.cvv) != str(cardCvv):
                    return JsonResponse({"message": "CVV is incorrect."}, status=400)

                # EXPIRY FORMAT CHECK
                if not re.match(r"^(0[1-9]|1[0-2])/\d{2}$", cardExpireDate):
                    return JsonResponse({"message": "Expiry date must be in MM/YY format."}, status=400)

                # CHECK IF CARD IS ACTUALLY EXPIRED
                month = int(cardExpireDate[0:2])
                year = int("20" + cardExpireDate[3:5])

                currentDate = datetime.now()

                currentMonth = currentDate.month
                currentYear = currentDate.year

                if year < currentYear or (year == currentYear and month < currentMonth):
                    return JsonResponse({"message": "Card has expired."}, status=400)

                # BALANCE CHECK
                if cardObj.balance < totalAmount:
                    return JsonResponse({"message": "Insufficient card balance."}, status=400)

            # CREATE ORDER
            orderObj = Order.objects.create(
                order_number=orderNumber,
                user_id=userObj,
                address_id=addressObj,
                subtotal=subTotal,
                tax=tax,
                shipping_charge=shippingCharge,
                total_amount=subTotal + tax + shippingCharge,
                payment_status=paymentStatus,
                order_status=1,
                notes=""
            )

            # CREATE OREDR ITEMS
            for item in cartItemObj:
                variant = item.product_variant_id
                OrderItem.objects.create(
                    order_id = orderObj,
                    product_id = variant.product_id,
                    product_variant_id = item.product_variant_id,
                    product_name = variant.product_id.name,
                    color = variant.color,
                    size = variant.size,
                    quantity = item.quantity,
                    mrp = variant.mrp,
                    selling_price = variant.selling_price,
                    tax = 0,
                    total = item.total
                )
                variant.stock_quantity = (
                    variant.stock_quantity - item.quantity
                )
                variant.save()

            if paymentMode == 3:
                cardObj.balance = cardObj.balance - totalAmount
                cardObj.save()

            paidAt = timezone.now()

            # CREATE PAYMENT
            Payment.objects.create(
                order_id = orderObj,
                payment_method = paymentMode,
                payment_status = paymentStatus,
                amount = totalAmount,
                paid_at = paidAt
            )

            # REMOVE CART
            cartObj.delete()

            shippingDate = orderObj.placed_at
            estimateDelivery = shippingDate + timedelta(days=5)

            Shipment.objects.create(
                order_id = orderObj,
                shipping_date = shippingDate,
                estimate_delivery = estimateDelivery,
                current_status = 1
            )

            return JsonResponse({"message": "Order Placed Successfully.",
                                "orderId": orderObj.id,
                                "orderNumber": orderNumber,
                                "subtotal": subTotal,
                                "tax": tax,
                                "totalAmount": totalAmount,
                                "shippingDate": shippingDate,
                                "estimateDelivery": estimateDelivery
                                }, status=200)

    except User.DoesNotExist:
        return JsonResponse({"message": "user not found."}, status=404)

    except ShoppingCart.DoesNotExist:
        return JsonResponse({"error": "shopping cart not found."}, status=404)

# GET PENDING ORDERS API
@csrf_exempt
@api_view(["GET"])
def get_pending_orders(request):
    token = request.headers.get("Authorization")

    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)
    try:
        userObj = User.objects.get(id=userIdOrError)

        orderObj = Order.objects.filter(user_id=userObj, order_status=1)
        order = []

        for i in orderObj:
            shipmentObj = Shipment.objects.filter(order_id=i).first()
            order.append({
                "orderId": i.id,
                "orderNumber": i.order_number,
                "totalAmount": i.total_amount,
                "orderStatus": i.order_status,
                "shipmentStatus": shipmentObj.current_status if shipmentObj else 'none',
                "placedAt": i.placed_at
            })
        return JsonResponse({"order": order}, status=200)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)

# GET IN ORDERS API
@csrf_exempt
@api_view(["GET"])
def get_in_orders(request):
    token = request.headers.get("Authorization")
    
    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    try:
        userObj = User.objects.get(id=userIdOrError)
        
        orderObj = Order.objects.filter(user_id=userObj, order_status=2)
        order = []

        for i in orderObj:
            shipmentObj = Shipment.objects.filter(order_id=i).first()
            order.append({
                "orderId": i.id,
                "orderNumber": i.order_number,
                "totalAmount": i.total_amount,
                "orderStatus": i.order_status,
                "shipmentStatus": shipmentObj.current_status,
                "placedAt": i.placed_at
            })
        return JsonResponse({"order": order}, status=200)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)

# GET COMPLETE ORDERS API
@csrf_exempt
@api_view(["GET"])
def get_complete_orders(request):
    token = request.headers.get("Authorization")
    
    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    try:
        userObj = User.objects.get(id=userIdOrError)
        
        orderObj = Order.objects.filter(user_id=userObj, order_status=3)
        order = []

        for i in orderObj:
            shipmentObj = Shipment.objects.filter(order_id=i).first()
            order.append({
                "orderId": i.id,
                "orderNumber": i.order_number,
                "totalAmount": i.total_amount,
                "orderStatus": i.order_status,
                "shipmentStatus": shipmentObj.current_status,
                "placedAt": i.placed_at
            })
        return JsonResponse({"order": order}, status=200)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)

# CANCEL ORDER API
@csrf_exempt
@api_view(["PUT"])
def cancel_order(request):
    token = request.headers.get("Authorization")
    orderId = request.GET.get("orderId")

    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    if not orderId:
        return JsonResponse({"message": "Order id is required."}, status=400)

    try:
        userObj = User.objects.get(id=userIdOrError)
        orderObj = Order.objects.get(id=orderId,user_id=userObj)

        if orderObj.order_status != 1 and orderObj.order_status != 2:
            return JsonResponse({"message": "Order cannot be cancelled."}, status=400)
        orderObj.order_status = 4
        orderObj.save()
        return JsonResponse({"message": "Order cancelled successfully.","orderId": orderObj.id,"orderNumber": orderObj.order_number}, status=200)

    except User.DoesNotExist:
        return JsonResponse({"message": "User not found."}, status=404)

    except Order.DoesNotExist:
        return JsonResponse({"message": "Order not found."}, status=404)

# CHANGE TO IN ORDER API
@csrf_exempt
@api_view(["PUT"])
def change_to_in_order(request):
    token = request.headers.get("Authorization")
    orderId = request.GET.get("orderId")
   
    userIdOrError = verify_token(token)

    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    if not orderId:
        return JsonResponse({"message": "Order id is required."}, status=400)
    
    try:
        userObj = User.objects.get(id=userIdOrError)
        orderObj = Order.objects.get(id=orderId, user_id=userObj)
       
        if orderObj.order_status != 1:
            return JsonResponse({"message": "Order is not pending."}, status=400)

        shipmentObj = Shipment.objects.get(order_id=orderObj)
        
        orderObj.order_status = 2
        orderObj.save()

        shipmentObj.current_status = 2
        shipmentObj.save()

        return JsonResponse({"message": "Order moved to processing.",
                             "orderId": orderObj.id,
                             "orderStatus": orderObj.get_order_status_display(),
                             "shipmentStatus": shipmentObj.get_current_status_display()
                            }, status=200)

    except User.DoesNotExist:
        return JsonResponse({"message": "User not found."}, status=404)

    except Order.DoesNotExist:
        return JsonResponse({"message": "Order not found."}, status=404)

    except Shipment.DoesNotExist:
        return JsonResponse({"message": "Shipment not found."}, status=404)

# CHANGE TO COMPLETE ORDER API
@csrf_exempt
@api_view(["PUT"])
def change_to_complete_order(request):
    token = request.headers.get("Authorization")
    orderId = request.GET.get("orderId")

    userIdOrError = verify_token(token)

    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    if not orderId:
        return JsonResponse({"message": "Order id is required."}, status=400)

    try:
        userObj = User.objects.get(id=userIdOrError)
        orderObj = Order.objects.get(id=orderId,user_id=userObj)

        if orderObj.order_status != 2:
            return JsonResponse({"message": "Order is not processing."}, status=400)

        shipmentObj = Shipment.objects.get(order_id=orderObj)

        orderObj.order_status = 3
        orderObj.save()

        shipmentObj.current_status = 5
        shipmentObj.delivered_date = timezone.now().date()
        shipmentObj.save()

        return JsonResponse({
            "message": "Order completed successfully.",
            "orderId": orderObj.id,
            "orderNumber": orderObj.order_number,
            "orderStatus": orderObj.get_order_status_display(),
            "shipmentStatus": shipmentObj.get_current_status_display(),
            "deliveredDate": shipmentObj.delivered_date
        }, status=200)

    except User.DoesNotExist:
        return JsonResponse({"message": "User not found."}, status=404)

    except Order.DoesNotExist:
        return JsonResponse({"message": "Order not found."}, status=404)

    except Shipment.DoesNotExist:
        return JsonResponse({"message": "Shipment not found."}, status=404)

# GET ALL PRODUCTS
@api_view(["GET"])
def get_all_products(request):
    category = request.GET.get("category")
    subcategoryId = request.GET.get("subcategoryId")
    startRange = request.GET.get("startRange")
    endRange = request.GET.get("endRange")
    page = int(request.GET.get("page", 1))
    search = request.GET.get("search")
    sort = request.GET.get("sort", "")

    try:
        limit = 16
        products = []

        productObj = Product.objects.all()

        for product in productObj:

            # SEARCH
            if search and search.lower() not in product.name.lower():
                continue

            # SUBCATEGORY 
            if subcategoryId:
                if product.category_id.id != int(subcategoryId):
                    continue

            # CATEGORY
            elif category:
                parentCategory = Category.objects.filter(status=True, parent_category_id=None, name__iexact=category).first()

                if not parentCategory:
                    continue

                productCategory = product.category_id
                if not productCategory.parent_category_id:
                    continue

                if productCategory.parent_category_id.id != parentCategory.id:
                    continue   

            # VARIANTS
            variantObj = ProductVariant.objects.filter(product_id=product, status=True)

            # PRICE
            price = None

            for variant in variantObj:
                if price is None or variant.selling_price < price:
                    price = variant.selling_price

            if price is None:
                continue

            # PRICE FILTER
            if startRange and price < float(startRange):
                continue

            if endRange and price > float(endRange):
                continue

            # IMAGE
            imageObj = ProductImage.objects.filter(product_id=product).first()

            image = imageObj.image.url if imageObj else None

            products.append({
                "id": product.id,
                "name": product.name,
                "image": image,
                "categoryId": product.category_id.id,
                "categoryName": product.category_id.name,
                "shortDescription": product.short_description,
                "price": price,
                "createdAt": product.created_at
            })

        # SORT
        sort = request.GET.get("sort", "asset")
        if sort == "asset":
            products.sort(key=itemgetter("price"))
        elif sort == "desset":
            products.sort(key=itemgetter("price"), reverse=True)
        elif sort == "newest":
            products.sort(key=lambda x: x["createdAt"], reverse=True)

        # COUNT
        totalProductCount = len(products)

        previousPage = page - 1 if page > 1 else None

        nextPage = page + 1 if page * limit < totalProductCount else None

        # PAGINATION
        start = (page - 1) * limit
        end = start + limit

        products = products[start:end]

        return JsonResponse({
            "previousPage": previousPage,
            "currentPage": page,
            "nextPage": nextPage,
            "totalProducts": totalProductCount,
            "products": products
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

# GET PROFILE API
@csrf_exempt
@api_view(["GET"])
def get_profile(request):
    token = request.headers.get("Authorization")

    if not token:
        return JsonResponse({"message": "Token is required."}, status=401)

    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    try:
        userObj = User.objects.get(id=userIdOrError)
        profileData = {
            "firstName": userObj.first_name,
            "lastName": userObj.last_name,
            "email": userObj.email,
            "dialCode": userObj.dial_code,
            "phoneNumber": userObj.phone_number,
            "gender": userObj.gender,
            "dateOfBirth": userObj.date_of_birth
        }
        return JsonResponse({"profileData":profileData}, status=200)
    except User.DoesNotExist:
        return JsonResponse({"error": "User does not exist."}, status=404)

# UPDATE PROFILE API
@csrf_exempt
@api_view(["PUT"])
def update_profile(request):

    token = request.headers.get("Authorization")
    
    if not token:
        return JsonResponse({
            "message": "Token is required."
        }, status=401)

    userIdOrError = verify_token(token)

    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    userObj = User.objects.filter(id=userIdOrError).first()

    if not userObj:
        return JsonResponse({
            "message": "User not found."
        }, status=404)

    firstName = request.data.get("firstName")
    lastName = request.data.get("lastName")
    email = request.data.get("email")
    dialCode = request.data.get("dialCode")
    phoneNumber = request.data.get("phoneNumber")

    if not firstName or not lastName or not email or not phoneNumber:
        return JsonResponse({
            "message": "All fields are required."
        }, status=400)

    userObj.first_name = firstName
    userObj.last_name = lastName
    userObj.email = email
    userObj.dial_code = dialCode
    userObj.phone_number = phoneNumber

    userObj.save()

    return JsonResponse({"message": "Profile updated successfully.", "status": True}, status=200)

# DELETE PROFILE API
@csrf_exempt
@api_view(["DELETE"])
def delete_profile(request):
    pass

# GET CURRENT ORDER API
@csrf_exempt
@api_view(["GET"])
def get_current_orders(request):
    token = request.headers.get("Authorization")

    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    try:
        userObj = User.objects.get(id=userIdOrError)

        ordersObj = Order.objects.filter(
            user_id=userObj,
            order_status__in=[1, 2, 3, 4]
        ).order_by("-placed_at")

        orders = []

        for order in ordersObj:

            orderItemsObj = OrderItem.objects.filter(order_id=order)

            items = []

            for item in orderItemsObj:

                items.append({
                    "id": item.id,
                    "productId": item.product_id.id,
                    "productName": item.product_name,
                    "color": item.color,
                    "size": item.size,
                    "quantity": item.quantity,
                    "mrp": float(item.mrp),
                    "sellingPrice": float(item.selling_price),
                    "total": float(item.total)
                })

            orders.append({
                "orderId": order.id,
                "orderNumber": order.order_number,
                "subtotal": float(order.subtotal),
                "tax": float(order.tax),
                "shippingCharge": float(order.shipping_charge),
                "totalAmount": float(order.total_amount),
                "orderStatus": order.order_status,
                "orderStatusName": order.get_order_status_display(),
                "paymentStatus": order.payment_status,
                "placedAt": order.placed_at.strftime("%d-%m-%Y %I:%M %p"),
                "items": items
            })

        return JsonResponse({
            "orders": orders
        }, status=200)

    except User.DoesNotExist:

        return JsonResponse({
            "error": "User not found."
        }, status=404)

# GET ALL ORDERS API
@csrf_exempt
@api_view(["GET"])
def get_my_orders(request):
    token = request.headers.get("Authorization")

    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    try:
        userObj = User.objects.get(id=userIdOrError)

        orderObj = Order.objects.filter(user_id=userObj, order_status=3).order_by("placed_at")
        orders = []

        for order in orderObj:
            orderItemsObj = OrderItem.objects.filter(order_id=order)
            items = []

            for item in orderItemsObj:
                items.append({
                    "id": item.id,
                    "productId": item.product_id.id,
                    "productName": item.product_name,
                    "color": item.color,
                    "size": item.size,
                    "quantity": item.quantity,
                    "sellingPrice": float(item.selling_price),
                    "total": float(item.total)
                })

            orders.append({
                "id": order.id,
                "orderNumber": order.order_number,
                "totalAmount": float(order.total_amount),
                "orderStatus": order.order_status,
                "orderStatusName": order.get_order_status_display(),
                "placedAt": order.placed_at,
                "items": items
            })
        return JsonResponse({"orders": orders}, status=200)

    except User.DoesNotExist:
        return JsonResponse({"message": "User not found."}, status=404)

# GET ORDER ITEM API
@csrf_exempt
@api_view(["GET"])
def get_order_item(request):
    token = request.headers.get("Authorization")
    orderItemId = request.GET.get("orderItemId")

    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    if not orderItemId:
        return JsonResponse({"message": "Order item id is required."}, status=400)

    try:
        userObj = User.objects.get(id=userIdOrError)
        orderItemObj = OrderItem.objects.get(id=orderItemId, order_id__user_id=userObj)

        return JsonResponse({
            "orderItem": {
                "id": orderItemObj.id,
                "productId": orderItemObj.product_id.id,
                "productName": orderItemObj.product_name,
                "color": orderItemObj.color,
                "size": orderItemObj.size,
                "quantity": orderItemObj.quantity,
                "sellingPrice": float(orderItemObj.selling_price),
                "total": float(orderItemObj.total)
            }}, status=200)

    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)

    except OrderItem.DoesNotExist:
        return JsonResponse({"error": "Order item not found."}, status=404)

# ADD REVIEW API
@csrf_exempt
@api_view(["POST"])
def add_review(request):
    token = request.headers.get("Authorization")

    orderId = request.data.get("orderId")
    orderItemId = request.data.get("orderItemId")
    rating = request.data.get("rating")
    title = request.data.get("title")
    review = request.data.get("review")
    image = request.FILES.get("images")

    userIdOrError = verify_token(token)
    if isinstance(userIdOrError, dict):
        return JsonResponse(userIdOrError, status=401)

    if not orderId or not orderItemId:
        return JsonResponse({"message": "Order and order item are required."}, status=400)

    if not rating or not title or not review:
        return JsonResponse({"message": "Rating, title and review are required."}, status=400)

    try:
        rating = int(rating)

        if rating < 1 or rating > 5:
            return JsonResponse({"message": "Rating must be between 1 and 5."}, status=400)

        userObj = User.objects.get(id=userIdOrError)
        orderObj = Order.objects.get(id=orderId, user_id=userObj)

        # Check completed order
        if orderObj.order_status != 3:
            return JsonResponse({"message": "You can review only completed orders."}, status=400)

        # Check that item belongs to this order
        orderItemObj = OrderItem.objects.get(id=orderItemId, order_id=orderObj)
        productObj = orderItemObj.product_id

        # Check whether user already reviewed product
        existingReview = Review.objects.filter(product_id=productObj, user_id=userObj).first()

        if existingReview:
            return JsonResponse({"message": "You have already reviewed this product."}, status=400)

        Review.objects.create(
            product_id=productObj,
            user_id=userObj,
            rating=rating,
            title=title,
            review=review,
            images=image,
            verified_purchase=True
        )
        return JsonResponse({"message": "Review submitted successfully."}, status=200)

    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)

    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found."}, status=404)

    except OrderItem.DoesNotExist:
        return JsonResponse({"error": "Order item does not belong to this order."}, status=404)

# QUICK VIEW
def quick_view(request, pid):
    try:
        productObj = Product.objects.get(id=pid, status=True)
        images = ProductImage.objects.filter(product_id=productObj)
        variants = ProductVariant.objects.filter(product_id=productObj, status=True)

        imageList = []

        for image in images:
            imageList.append({
                "image": image.image.url,
                "altText": image.alt_text
            })

        variantList = []

        sizes = []
        colors = []

        for variant in variants:
            variantList.append({
                "id": variant.id,
                "size": variant.size,
                "color": variant.color,
                "colorCode": variant.color_code,
                "sellingPrice": variant.selling_price,
                "stockQuantity": variant.stock_quantity
            })

            if variant.size not in sizes:
                sizes.append(variant.size)

            if variant.color not in colors:
                colors.append({
                    "name": variant.color,
                    "code": variant.color_code
                })

        return JsonResponse({
            "id": productObj.id,
            "name": productObj.name,
            "shortDescription": productObj.short_description,
            "price": variants.first().selling_price if variants.exists() else 0,
            "images": imageList,
            "sizes": sizes,
            "colors": colors,
            "variants": variantList
        }, status=200)

    except Product.DoesNotExist:
        return JsonResponse({"message": "Product not found."}, status=404)

    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)

# GET PENDING SHIPMENT API
@api_view(["GET"])
def get_shipments(request):
    status = request.GET.get("status")

    if status:
        status = int(status)

        if status not in [1,2,3,4,5]:
            return JsonResponse({"message": "Invalid shipment status."}, status=400)
        
        shipmentObj = Shipment.objects.filter(current_status=status).order_by("-id")

    else:
        shipmentObj = Shipment.objects.all().order_by("-id")

    shipments = []

    for shipment in shipmentObj:
        shipments.append({
            "shipmentId": shipment.id,
            "orderId": shipment.order_id.id,
            "orderNumber": shipment.order_id.order_number,
            "shippingDate": shipment.shipping_date,
            "estimateDelivery": shipment.estimate_delivery,
            "deliveredDate": shipment.delivered_date,
            "currentStatus": shipment.current_status,
            "currentStatusName": shipment.get_current_status_display()
        })
    return JsonResponse({"shipments": shipments}, status=200)

# CHANGE SHIPMENT STATUS API
@api_view(["PUT"])
def change_status(request):
    shipmentId = request.data.get("shipmentId")
    status = request.data.get("status")

    if not shipmentId or not status:
        return JsonResponse({"message": "Shipment id and status are required."}, status=400)

    status = int(status)
    if status not in[1,2,3,4,5]:
        return JsonResponse({"message": "Invalid shipment status."}, status=400)

    shipmentObj = Shipment.objects.filter(id=shipmentId).first()

    if not shipmentObj:
        return JsonResponse({"message": "Shipment not found."}, status=404)

    orderObj = shipmentObj.order_id

    if orderObj.order_status == 4:
        return JsonResponse({"message": "order is alredy delivered. Status  cannot be changed."}, status=400)

    if shipmentObj.current_status == 4:
        return JsonResponse({"message": "Shipment is already delivered. Status cannot be changed."}, status=400)

    if shipmentObj.current_status == 1 and status != 2:
        return JsonResponse({"message": "Pending shipment can only be changed Picked Up."}, status=400)

    if shipmentObj.current_status == 2 and status != 3:
        return JsonResponse({"message": "Picked up shipment can only be changed Out for Delivery."}, status=400)

    if shipmentObj.current_status == 3 and status not in [4, 5]:
        return JsonResponse({"message": "Out for Delivery shipment can only be changed Delivered or Exception/Delayed."}, status=400)

    shipmentObj.current_status = status
    if status == 4:
        shipmentObj.delivered_date = timezone.now().date()
    shipmentObj.save()

    if status == 1:
        orderObj.order_status = 1

    elif status == 2:
        orderObj.order_status = 2

    elif status == 3:
        orderObj.order_status = 2
    
    elif status == 4:
        orderObj.order_status = 3 

    elif status == 5:
        orderObj.order_status = 2 

    orderObj.save()

    return JsonResponse({
        "message": "Shipment and order status updated successfully.",
        "shipmentId": shipmentObj.id,
        "shipmentStatus": shipmentObj.current_status,
        "shipmentStatusName": shipmentObj.get_current_status_display(),
        "orderId": orderObj.id,
        "orderStatus": orderObj.order_status,
        "orderStatusName": orderObj.get_order_status_display(),
    }, status=200)


# @api_view(["GET"])
# def get_shipments(request):

#     token = request.headers.get("Authorization")

#     if not token:
#         return JsonResponse({
#             "message": "Delivery token is required."
#         }, status=401)
    
#     deliveryPartnerId = verify_delivery_token(token)

#     if not deliveryPartnerId:
#         return JsonResponse({
#             "message": "Invalid delivery token."
#         }, status=401)

#     status = request.GET.get("status")

#     shipmentObj = Shipment.objects.filter(
#         delivery_partner_id=deliveryPartnerId
#     ).order_by("-id")

#     if status:
#         status = int(status)

#         if status not in [1, 2, 3, 4, 5]:
#             return JsonResponse({
#                 "message": "Invalid shipment status."
#             }, status=400)

#         shipmentObj = shipmentObj.filter(
#             current_status=status
#         )

#     shipments = []

#     for shipment in shipmentObj:

#         shipments.append({
#             "shipmentId": shipment.id,
#             "orderId": shipment.order_id.id,
#             "orderNumber": shipment.order_id.order_number,
#             "shippingDate": shipment.shipping_date,
#             "estimateDelivery": shipment.estimate_delivery,
#             "deliveredDate": shipment.delivered_date,
#             "currentStatus": shipment.current_status,
#             "currentStatusName": shipment.get_current_status_display()
#         })

#     return JsonResponse({
#         "shipments": shipments
#     }, status=200)

# DELIVERY PERSON LOGIN API
@csrf_exempt
@api_view(["POST"])
def delivery_partner_login(request):
    email = request.data.get("email")
    password = request.data.get("password")
    print(email, password)
    if not email or not password:
        return JsonResponse({"message": "Email and password are required."}, status=400)
    
    deliveryPartnerObj = DeliveryPartner.objects.filter(email=email).first()
    
    if not deliveryPartnerObj:
        return JsonResponse({"error": "Delivery partner not found."}, status=404)

    if deliveryPartnerObj.password == password:
        token = create_delivery_token(deliveryPartnerObj)
       
        return JsonResponse({"message":"Login Successfull.", "token":token,
                                "deliveryPartner": {
                                "id": deliveryPartnerObj.id,
                                "firstName": deliveryPartnerObj.first_name,
                                "lastName": deliveryPartnerObj.last_name,
                                "email": deliveryPartnerObj.email,
                        }}, status=200)
    else:
        return JsonResponse({"error": "Password is incorrect"}, status=401)

# CALCULATE SHIPPING API
@api_view(["POST"])
def calculate_shipping(request):
    token = request.headers.get("Authorization")

    if not token:
        return JsonResponse({
            "message": "Token is required."
        }, status=401)

    userId = verify_token(token)

    if isinstance(userId, dict):
        return JsonResponse(userId, status=401)

    addressId = request.data.get("addressId")

    if not addressId:
        return JsonResponse({
            "message": "Address id is required."
        }, status=400)

    addressObj = Address.objects.filter(
        id=addressId,
        user_id=userId
    ).first()

    if not addressObj:
        return JsonResponse({
            "message": "Address not found."
        }, status=404)

    return JsonResponse({
        "stateId": addressObj.state_id.state_id,
        "cityId": addressObj.city_id.city_id,
        "areaId": addressObj.area_id.area_id
    }, status=200)

# FORGOT PASSWORD API
@api_view(["POST"])
def forgot_password(request):
    action = request.data.get("action")
    email = request.data.get("email")

    if not email:
        return JsonResponse({"message": "Email is required."}, status=400)

    userObj = User.objects.filter(email=email, is_deleted=False).first()
    if not userObj:
        return JsonResponse({"message": "User not found."}, status=404)

    # GET OTP
    if action == "getOtp":
        otp = random.randint(100000, 999999)

        userObj.otp = otp
        userObj.otp_verified = False
        userObj.otp_created_at = timezone.now()
        userObj.save()

        subject = "StyleCreaft Password Reset OTP"

        message = f"""
Hello {userObj.first_name},

Your OTP for resetting your StyleCraft password is:

{otp}

This OTP is valid for 10 minutes.

If you did not request a password reset, please ignore this email.

Thank you,
StyleCraft Team
"""
        send_mail(subject, message, None, [userObj.email])

        return JsonResponse({"message": "OTP sent successfully to your email."}, status=200)

    elif action == "verifyOtp":
        otp = request.data.get("otp")

        if not otp:
            return JsonResponse({"message": "OTP is required."}, status=400)

        try:
            otp = int(otp)
        except:
            return JsonResponse({"message": "OTP must be a number."}, status=400)
        print(otp)
        if not userObj.otp:
            return JsonResponse({"message": "Please Generate OTP first."}, status=400)

        if userObj.otp != otp:
            return JsonResponse({"message": "Invalid OTP."}, status=400)

        if not userObj.otp_created_at:
            return JsonResponse({"message": "OTP is inavlid."}, status=400)

        currentTime = timezone.now()
        timeDiffrence = currentTime - userObj.otp_created_at

        if timeDiffrence.total_seconds() > 600:
            return JsonResponse({"message": "OTP has expired. Please generate a new OTP."}, status=400)

        userObj.otp_verified = True
        userObj.save()

        return JsonResponse({"message": "OTP verified successfully."}, status=200)

    elif action == "resetPassword":
        newPassword = request.data.get("newPassword")
        confirmPassword = request.data.get("confirmPassword")

        if not newPassword or not confirmPassword:
            return JsonResponse({"message": "New password and confirm passeord are required."}, status=400)

        if not userObj.otp_verified:
            return JsonResponse({"message": "Please verify OTP first."}, status=400)

        if newPassword != confirmPassword:
            return JsonResponse({"message": "Password and confirm password do not match."}, status=400)

        if len(newPassword) < 8 or len(newPassword) > 16:
            return JsonResponse({"message": "Passwor must be between 8 and 16 characters."}, status=400)

        hasUpper = False
        hasLower = False
        hasDigit = False
        hasSpecial = False

        for character in newPassword:
            if character.isupper():
                hasUpper = True
            elif character.islower():
                hasLower = True
            elif character.isdigit():
                hasDigit = True
            else:
                hasSpecial = True

        if not hasUpper or not hasLower or not hasDigit or not hasSpecial:
            return JsonResponse({"message": "Password must conatin an uppercase letter, a lowercase letter, a number and a special character."}, status=400)

        userObj.password = newPassword

        userObj.otp = None
        userObj.otp_verified = False
        userObj.otp_created_at = None
        userObj.save()

        token = create_token(userObj)

        return JsonResponse({"message": "Password reset successfully.", "token": token,
                             "user": {
                                 "id": userObj.id,
                                 "firstName": userObj.first_name,
                                 "lastName": userObj.last_name,
                                 "email": userObj.email,
                                 "dialCode": userObj.dial_code,
                                 "phoneNumber": userObj.phone_number,
                                 "profileImage": userObj.profile_image.url if userObj.profile_image else None
                             }}, status=200)

    else:
        return JsonResponse({"message": "Invalid action."}, status=400)

# GENERATE INVOICE 
def generate_invoice(request, order_id):

    orderObj = Order.objects.filter(id=order_id).first()
    if not orderObj:
        return HttpResponse("Order not found", status=404)

    order_items = OrderItem.objects.filter(order_id=orderObj)
    items = []

    subtotal = 0

    for item in order_items:
        item_total = item.quantity * item.selling_price
        subtotal = subtotal + item_total

        items.append({
            "product": item.product_variant_id.product_id.name,
            "size": item.product_variant_id.size,
            "color": item.product_variant_id.color,
            "quantity": item.quantity,
            "price": item.selling_price,
            "total": item.total,
        })

    tax = subtotal * 18 / 100
    shipping = orderObj.shipping_charge
    total = subtotal + tax + shipping

    context = {
        "order": orderObj,
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "shipping_charge": shipping,
        "total": total,
        "payment_mode": orderObj.get_payment_status_display(),
    }

    template = render(request, "invoice.html", context)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        'attachment; filename="Invoice_'
        + str(orderObj.order_number)
        + '.pdf"'
    )

    pisa_status = pisa.CreatePDF(template.content,dest=response)

    if pisa_status.err:
        return HttpResponse("Error while generating PDF", status=500)

    return response

# ORDER REPORT API
@api_view(["GET"])
def order_report(request):
    today = timezone.now()

    start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    orderStatus = request.GET.get("orderStatus")
    paymentStatus = request.GET.get("paymentStatus")
    startDate = request.GET.get("startDate")
    endDate = request.GET.get("endDate")
    search = request.GET.get("search")

    orders = Order.objects.filter(placed_at__gte=start_date, placed_at__lte=today)

    if orderStatus:
        orders = orders.filter(order_status=orderStatus)

    if paymentStatus:
        orders = orders.filter(payment_status=paymentStatus)

    if startDate:
        orders = orders.filter(placed_at__date__gte=startDate)

    if endDate:
        orders = orders.filter(placed_at__date__lte=endDate)

    if search:
        orders = orders.filter(order_number__icontains=search)

    print(orderStatus, paymentStatus) 

    orderList = []

    for order in orders:
        orderList.append({
            "orderId": order.id,
            "orderNumber": order.order_number,
            "customerName": order.user_id.first_name + " " + order.user_id.last_name,
            "email": order.user_id.email,
            "subTotal": order.subtotal,
            "tax": order.tax,
            "shippingCharge": order.shipping_charge,
            "totalAmount": order.total_amount,
            "paymentStatus": order.get_payment_status_display(),
            "orderStatus": order.get_order_status_display(),
            "placedAt": order.placed_at.strftime("%d-%m-%y %H:%M")
        })

    return JsonResponse({"message": "Order report generated successfully.", "totalOrders":len(orderList), "orders": orderList}, status=200)
