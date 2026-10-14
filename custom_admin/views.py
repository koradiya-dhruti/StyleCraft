from django.shortcuts import render
from clothing.models import *
from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.utils import timezone as django_timezone
# from django.utils import timezone
from django.db.models import Sum
from .tokens import *
from django.contrib.auth.hashers import make_password, check_password
import random
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta, datetime
from django.urls import reverse


# Create your views here.

def index(request):
    return render(request, "admin/admin-index.html")

def profile(request):
    return render(request, "admin/admin-profile.html")

def admin_login(request):
    return render(request, "admin/admin-login.html")

def admin_forgot_password(request):
    return render(request, "admin/admin-forgot-password.html")

# def products(request):
#     return render(request, "admin/products.html")

def add_new_product(request):
    return render(request, "admin/add-new-product.html")

def view_products(request):
    return render(request, "admin/view-products.html")

def add_new_product_variant(request):
    return render(request, "admin/add-new-product-variant.html")

def edit_product_page(request, product_id):
    return render(request, "admin/edit-product.html", {"productId": product_id})

# def categories(request):
#     return render(request, "admin/categories.html")

def add_new_category(request):
    return render(request, "admin/add-new-category.html")

def view_category(request):
    return render(request, "admin/view-category.html")

def edit_category_page(request, category_id):
    return render(request, "admin/edit-category.html", {"categoryId": category_id})

# def stock_management(request):
#     return render(request, "admin/stock-management.html")

def add_new_stock(request):
    return render(request, "admin/add-new-stock.html")

def view_current_stock(request):
    return render(request, "admin/view-current-stock.html")

def edit_stock_page(request, variant_id):
    return render(request, "admin/edit-stock.html", {"variantId": variant_id})

# def orders(request):
#     return render(request, "admin/orders.html")

def current_orders(request):
    return render(request, "admin/current-orders.html")

def in_delivery_orders(request):
    return render(request, "admin/in-delivery-orders.html")

def order_history(request):
    return render(request, "admin/order-history.html")

def order_details_page(request, orderId):
    return render(request, "admin/order-details.html", {"orderId": orderId})

# def payments(request):
#     return render(request, "admin/payments.html")

def total_payments(request):
    return render(request, "admin/total-payments.html")

# GET ALL CATEGORIES API
@csrf_exempt
@api_view(["GET"])
def get_all_categories(request):

    search = request.GET.get("search", "").strip()
    categoryType = request.GET.get("categoryType", "").strip()
    sort = request.GET.get("sort", "newest")
    status = request.GET.get("status", "").strip()

    try:
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))

        if page < 1:
            page = 1

        if limit < 1:
            limit = 10

        categoryObj = Category.objects.all()

        categoryList = []

        for category in categoryObj:

            parentCategory = None
            parentCategoryId = None

            if category.parent_category_id:
                parentCategoryId = category.parent_category_id.id
                parentCategory = category.parent_category_id.name

            # SEARCH
            if search:
                searchText = search.lower()

                if (
                    searchText not in str(category.id).lower()
                    and searchText not in category.name.lower()
                    and searchText not in (parentCategory or "").lower()
                ):
                    continue

            # CATEGORY FILTER
            if categoryType == "main":
                if parentCategoryId is not None:
                    continue

            elif categoryType == "sub":
                if parentCategoryId is None:
                    continue

            if status == "active" and not category.status:
                continue

            if status == "inactive" and category.status:
                continue

            categoryList.append({
                "categoryId": category.id,
                "image": category.image.url if category.image else None,
                "category": category.name,
                "description": category.description,
                "parentId": parentCategoryId,
                "parentCategory": parentCategory,
                "status": category.status
            })

        # SORT
        if sort == "newest":

            for i in range(len(categoryList)):
                for j in range(i + 1, len(categoryList)):

                    if categoryList[i]["categoryId"] < categoryList[j]["categoryId"]:

                        temp = categoryList[i]
                        categoryList[i] = categoryList[j]
                        categoryList[j] = temp

        elif sort == "oldest":

            for i in range(len(categoryList)):
                for j in range(i + 1, len(categoryList)):

                    if categoryList[i]["categoryId"] > categoryList[j]["categoryId"]:

                        temp = categoryList[i]
                        categoryList[i] = categoryList[j]
                        categoryList[j] = temp
    

        # TOTAL COUNT
        totalCategories = len(categoryList)

        # PAGINATION
        totalPages = (totalCategories + limit - 1) // limit

        if totalPages > 0 and page > totalPages:
            page = totalPages

        previousPage = page - 1 if page > 1 else None
        nextPage = page + 1 if page < totalPages else None

        start = (page - 1) * limit
        end = start + limit

        categoryList = categoryList[start:end]

        return JsonResponse({
            "category": categoryList,
            "total": totalCategories,
            "currentPage": page,
            "totalPages": totalPages,
            "limit": limit,
            "previousPage": previousPage,
            "nextPage": nextPage,
            "hasPrevious": previousPage is not None,
            "hasNext": nextPage is not None
        }, status=200)

    except (ValueError, TypeError):
        return JsonResponse({
            "error": "Page and limit must be valid numbers."
        }, status=400)

    except Exception as e:
        return JsonResponse({
            "error": str(e)
        }, status=400)

# GET SINGLE CATEGORY API
@api_view(["GET"]) 
def get_single_category(request, category_id):

    categoryObj = Category.objects.filter(
        id=category_id
    ).first()

    if not categoryObj:
        return JsonResponse(
            {
                "message": "Category not found.",
                "categoryId": category_id
            },
            status=404
        )

    category = {
        "categoryId": categoryObj.id,
        "category": categoryObj.name,
        "description": categoryObj.description,
        "parentId": categoryObj.parent_category_id.id if categoryObj.parent_category_id else None,
        "status": categoryObj.status
    }

    return JsonResponse(
        {
            "category": category
        },
        status=200
    )

# ADD CATEGORY API
@csrf_exempt
@api_view(["POST"])
def add_category(request):

    name = request.data.get("name")
    description = request.data.get("description")
    parentCategoryId = request.data.get("parentCategoryId")
    image = request.FILES.get("image")
    status = request.data.get("status")

    # Check category name
    if not name:
        return JsonResponse(
            {"message": "Category name is required."},
            status=400
        )

    # Convert status to Boolean
    if isinstance(status, str):
        status = status.lower() == "true"

    # Parent category
    parentCategory = None

    if parentCategoryId:
        parentCategory = Category.objects.filter(
            id=parentCategoryId
        ).first()

        if not parentCategory:
            return JsonResponse(
                {"message": "Parent category not found."},
                status=404
            )

    # Create category
    categoryObj = Category.objects.create(
        name=name,
        description=description,
        parent_category_id=parentCategory,
        image=image,
        status=status
    )

    return JsonResponse(
        {
            "message": "Category added successfully.",
            "categoryId": categoryObj.id
        },
        status=201
    )

# EDIT CATEGORY API
@csrf_exempt
@api_view(["POST"])
def edit_category(request, category_id):

    categoryObj = Category.objects.filter(id=category_id).first()

    if not categoryObj:
        return JsonResponse(
            {
                "message": "Category not found."
            },
            status=404
        )

    name = request.data.get("name")
    description = request.data.get("description")
    parentCategoryId = request.data.get("parentCategoryId")
    status = request.data.get("status")
    image = request.FILES.get("image")

    if not name:
        return JsonResponse(
            {
                "message": "Category name is required."
            },
            status=400
        )

    if isinstance(status, str):
        status = status.lower() == "true"

    parentCategory = None

    if parentCategoryId:

        parentCategory = Category.objects.filter(
            id=parentCategoryId
        ).first()

        if not parentCategory:
            return JsonResponse(
                {
                    "message": "Parent category not found."
                },
                status=404
            )

        if parentCategory.id == categoryObj.id:
            return JsonResponse({"message": "Category cannot be its own parent."}, status=400)

    categoryObj.name = name
    categoryObj.description = description
    categoryObj.parent_category_id = parentCategory
    categoryObj.status = status

    if image:
        categoryObj.image = image

    categoryObj.save()

    return JsonResponse({"message": "Category updated successfully.", "categoryId": categoryObj.id}, status=200)

# DELETE CATEGORY API
@csrf_exempt
@api_view(["DELETE"])
def delete_category(request):

    categoryId = request.GET.get("categoryId")

    print("Category ID:", categoryId)

    if not categoryId:
        return JsonResponse(
            {
                "message": "Category ID is required."
            },
            status=400
        )

    categoryObj = Category.objects.filter(
        id=categoryId
    ).first()

    if not categoryObj:
        return JsonResponse(
            {
                "message": "Category not found."
            },
            status=404
        )

    categoryObj.delete()

    return JsonResponse(
        {
            "message": "Category deleted successfully."
        },
        status=200
    )

# GET ALL BRANDS API
@api_view(["GET"])
def get_all_brands(request):
    brandObj = Brand.objects.all().order_by("-id")

    brandList = []
    for brand in brandObj:
        brandList.append({
            "brandId": brand.id,
            "brand": brand.name
        })
    return JsonResponse({"brand": brandList}, status=200)

# GET SINGLE PRODUCT API
@api_view(["GET"])
def get_single_product(request, product_id):
    productObj = Product.objects.filter(id=product_id).first()

    if not productObj:
        return JsonResponse({"message": "Product not found.", "productId": product_id}, status=404)

    product = {
        "id": productObj.id,
        "categoryId": productObj.category_id.id,
        "category": productObj.category_id.name,
        "brandId": productObj.brand_id.id,
        "brand": productObj.brand_id.name,
        "name": productObj.name,
        "shortDescription": productObj.short_description,
        "description": productObj.description,
        "gender": productObj.gender,
        "status": productObj.status
    }

    return JsonResponse({"product": product}, status=200)

# GET ALL PRODUCTS API
@api_view(["GET"])
def get_all_products(request):
    try:
        search = request.GET.get("search", "").strip().lower()
        categoryId = request.GET.get("categoryId", "").strip()
        brandId = request.GET.get("brandId", "").strip()
        gender = request.GET.get("gender", "").strip().lower()
        status = request.GET.get("status", "").strip()
        sort = request.GET.get("sort", "newest")

        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))

        if page < 1:
            page = 1

        if limit < 1:
            limit = 10

        productObj = Product.objects.all()

        productList = []

        for product in productObj:
            categoryName = product.category_id.name if product.category_id else ""
            categoryIdValue = product.category_id.id if product.category_id else None
            brandName = product.brand_id.name if product.brand_id else ""
            brandIdValue = product.brand_id.id if product.brand_id else None
            genderName = product.get_gender_display()

            # SEARCH
            if search:
                if (
                    search not in str(product.id).lower()
                    and search not in product.name.lower()
                    and search not in categoryName.lower()
                    and search not in brandName.lower()
                ):
                    continue

            # CATEGORY FILTER
            if categoryId:
                if str(categoryIdValue) != categoryId:
                    continue

            # BRAND FILTER
            if brandId:
                if str(brandIdValue) != brandId:
                    continue

            brandIdValue = product.brand_id.id if product.brand_id else None

            # GENDER FILTER
            if gender:
                if genderName.lower() != gender:
                    continue

            # STATUS FILTER
            if status == "active":
                if not product.status:
                    continue
            elif status == "inactive":
                if product.status:
                    continue

            productList.append({
                "productId": product.id,
                "categoryId": categoryIdValue,
                "category": categoryName,
                "brandId": brandIdValue,
                "brand": brandName,
                "name": product.name,
                "shortDescription": product.short_description,
                "description": product.description,
                "gender": genderName,
                "status": product.status,
            })

        # SORT
        if sort == "newest":
            for i in range(len(productList)):
                for j in range(i + 1, len(productList)):
                    if productList[i]["productId"] < productList[j]["productId"]:
                        temp = productList[i]
                        productList[i] = productList[j]
                        productList[j] = temp

        elif sort == "oldest":
            for i in range(len(productList)):
                for j in range(i + 1, len(productList)):
                    if productList[i]["productId"] > productList[j]["productId"]:
                        temp = productList[i]
                        productList[i] = productList[j]
                        productList[j] = temp

        # TOTAL AND PAGINATION
        totalProducts = len(productList)
        totalPages = (totalProducts + limit - 1) // limit

        if totalPages > 0 and page > totalPages:
            page = totalPages

        previousPage = page - 1 if page > 1 else None
        nextPage = page + 1 if page < totalPages else None

        start = (page - 1) * limit
        end = start + limit

        productList = productList[start:end]

        return JsonResponse({
            "product": productList,
            "total": totalProducts,
            "currentPage": page,
            "totalPages": totalPages,
            "limit": limit,
            "previousPage": previousPage,
            "nextPage": nextPage,
            "hasPrevious": previousPage is not None,
            "hasNext": nextPage is not None
        }, status=200)

    except (ValueError, TypeError):
        return JsonResponse({
            "message": "Page and limit must be valid numbers."
        }, status=400)

    except Exception as e:
        return JsonResponse({
            "message": str(e)
        }, status=400)

# ADD PRODUCT API
@csrf_exempt
@api_view(["POST"])
def add_product(request):

    categoryId = request.data.get("categoryId")
    brandId = request.data.get("brandId")
    name  = request.data.get("name")
    shortDescription = request.data.get("shortDescription")
    description = request.data.get("description")
    gender = request.data.get("gender")

    if not categoryId or not brandId or not name or not shortDescription or not description or not gender:
        return JsonResponse({"message": "Category Id, Brand Id, Product name, Short Description, Description, Gender and Status these all fields are required."}, status=400)
    
    categoryObj = Category.objects.filter(id=categoryId).first()
    brandObj = Brand.objects.filter(id=brandId).first()

    productObj = Product.objects.create(
        category_id = categoryObj,
        brand_id = brandObj,
        name = name, 
        short_description = shortDescription,
        description = description,
        gender = gender
    )
    return JsonResponse({"message": "Product added successfully.", "productId": productObj.id}, status=200)

# EDIT PRODUCT API
@csrf_exempt
@api_view(["POST"])
def edit_product(request, product_id):

    productObj = Product.objects.filter(id=product_id).first()

    if not productObj:
        return JsonResponse({"message": "Product not found."}, status=404)

    categoryId = request.data.get("categoryId")
    brandId = request.data.get("brandId")
    name = request.data.get("name")
    shortDescription = request.data.get("shortDescription")
    description = request.data.get("description")
    gender = request.data.get("gender")
    status = request.data.get("status")

    if isinstance(status, str):
        status = status.lower() == "true"

    if not categoryId:
        return JsonResponse({"message": "Category is required."}, status=400)

    if not brandId:
        return JsonResponse({"message": "Brand is required."}, status=400)

    if not name:
        return JsonResponse({"message": "Product name is required."}, status=400)

    if not shortDescription:
        return JsonResponse({"message": "Short description is required."}, status=400)

    if not description:
        return JsonResponse({"message": "Description is required."}, status=400)

    if not gender:
        return JsonResponse({"message": "Gender is required."}, status=400)

    categoryObj = Category.objects.filter(id=categoryId).first()

    if not categoryObj:
        return JsonResponse({"message": "Category not found."}, status=404)

    brandObj = Brand.objects.filter(id=brandId).first()

    if not brandObj:
        return JsonResponse({"message": "Brand not found."}, status=404)

    productObj.category_id = categoryObj
    productObj.brand_id = brandObj
    productObj.name = name
    productObj.short_description = shortDescription
    productObj.description = description
    productObj.gender = gender
    productObj.status = status

    productObj.save()

    return JsonResponse({"message": "Product updated successfully."}, status=200)

# DELETE PRODUCT API
@csrf_exempt
@api_view(["DELETE"])
def delete_product(request):
    productId = request.GET.get("productId")
    
    productObj = Product.objects.filter(id=productId).first()

    productObj.delete()

    return JsonResponse({"message": "Product deleted successfully."}, status=200)

# # GET CURRENT ORDERS API
# @api_view(["GET"])
# def get_current_orders(request):

#     orderObj = Order.objects.filter(
#         order_status__in=[1, 2]
#     ).select_related(
#         "user_id",
#         "address_id"
#     ).order_by("-id")

#     orderList = []

#     for order in orderObj:

#         if order.payment_status == 1:
#             paymentStatus = "Pending"
#         elif order.payment_status == 2:
#             paymentStatus = "Paid"
#         elif order.payment_status == 3:
#             paymentStatus = "Failed"
#         elif order.payment_status == 4:
#             paymentStatus = "Refunded"
#         else:
#             paymentStatus = "Unknown"

#         if order.order_status == 1:
#             orderStatus = "Pending"
#         elif order.order_status == 2:
#             orderStatus = "Processing"
#         else:
#             orderStatus = "Unknown"

#         customerName = (
#             order.user_id.first_name
#             + " "
#             + order.user_id.last_name
#         )

#         orderList.append(
#             {
#                 "orderId": order.id,
#                 "orderNumber": order.order_number,

#                 "customerId": order.user_id.id,
#                 "customerName": customerName,
#                 "customerEmail": order.user_id.email,
#                 "customerPhone": order.user_id.phone_number,

#                 "addressId": order.address_id.id,
#                 "address": order.address_id.address_line1,
#                 "city": (
#                     order.address_id.city_id.city_name
#                     if order.address_id.city_id
#                     else ""
#                 ),
#                 "state": (
#                     order.address_id.state_id.state_name
#                     if order.address_id.state_id
#                     else ""
#                 ),

#                 "subtotal": str(order.subtotal),
#                 "tax": str(order.tax),
#                 "shippingCharge": str(order.shipping_charge),
#                 "totalAmount": str(order.total_amount),

#                 "paymentStatus": order.payment_status,
#                 "paymentStatusName": paymentStatus,

#                 "orderStatus": order.order_status,
#                 "orderStatusName": orderStatus,

#                 "notes": order.notes,
#                 "placedAt": order.placed_at.strftime(
#                     "%d-%m-%Y %H:%M"
#                 )
#             }
#         )

#     return JsonResponse({"orders": orderList}, status=200)


@api_view(["GET"])
def get_current_orders(request):

    search = request.GET.get("search", "").strip().lower()
    orderStatusFilter = request.GET.get("orderStatus", "").strip()
    paymentStatusFilter = request.GET.get("paymentStatus", "").strip()
    sort = request.GET.get("sort", "newest")

    try:
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))

        if page < 1:
            page = 1

        if limit not in [10, 20, 50]:
            limit = 10

        orderObj = Order.objects.filter(
            order_status__in=[1, 2]
        ).select_related(
            "user_id",
            "address_id",
            "address_id__city_id",
            "address_id__state_id"
        ).order_by("-id")

        orderList = []

        for order in orderObj:

            if order.payment_status == 1:
                paymentStatus = "Pending"
            elif order.payment_status == 2:
                paymentStatus = "Paid"
            elif order.payment_status == 3:
                paymentStatus = "Failed"
            elif order.payment_status == 4:
                paymentStatus = "Refunded"
            else:
                paymentStatus = "Unknown"

            if order.order_status == 1:
                orderStatus = "Pending"
            elif order.order_status == 2:
                orderStatus = "Processing"
            else:
                orderStatus = "Unknown"

            customerName = (
                order.user_id.first_name + " "
                + order.user_id.last_name
            )

            address = order.address_id.address_line1

            city = (
                order.address_id.city_id.city_name
                if order.address_id.city_id
                else ""
            )

            state = (
                order.address_id.state_id.state_name
                if order.address_id.state_id
                else ""
            )

            # SEARCH
            if search:
                searchableText = (
                    str(order.id) + " "
                    + str(order.order_number) + " "
                    + customerName + " "
                    + order.user_id.email + " "
                    + str(order.user_id.phone_number) + " "
                    + address + " "
                    + city + " "
                    + state
                ).lower()

                if search not in searchableText:
                    continue

            # ORDER STATUS FILTER
            if orderStatusFilter:
                if str(order.order_status) != orderStatusFilter:
                    continue

            # PAYMENT STATUS FILTER
            if paymentStatusFilter:
                if str(order.payment_status) != paymentStatusFilter:
                    continue

            orderList.append({
                "orderId": order.id,
                "orderNumber": order.order_number,

                "customerId": order.user_id.id,
                "customerName": customerName,
                "customerEmail": order.user_id.email,
                "customerPhone": order.user_id.phone_number,

                "addressId": order.address_id.id,
                "address": address,
                "city": city,
                "state": state,

                "subtotal": str(order.subtotal),
                "tax": str(order.tax),
                "shippingCharge": str(order.shipping_charge),
                "totalAmount": str(order.total_amount),

                "paymentStatus": order.payment_status,
                "paymentStatusName": paymentStatus,

                "orderStatus": order.order_status,
                "orderStatusName": orderStatus,

                "notes": order.notes,
                "placedAt": (
                    order.placed_at.strftime("%d-%m-%Y %H:%M")
                    if order.placed_at
                    else ""
                )
            })

        # SORTING
        for i in range(len(orderList)):
            for j in range(i + 1, len(orderList)):

                swap = False

                if sort == "newest":
                    if orderList[i]["orderId"] < orderList[j]["orderId"]:
                        swap = True

                elif sort == "oldest":
                    if orderList[i]["orderId"] > orderList[j]["orderId"]:
                        swap = True

                elif sort == "amountHigh":
                    if float(orderList[i]["totalAmount"]) < float(orderList[j]["totalAmount"]):
                        swap = True

                elif sort == "amountLow":
                    if float(orderList[i]["totalAmount"]) > float(orderList[j]["totalAmount"]):
                        swap = True

                if swap:
                    temp = orderList[i]
                    orderList[i] = orderList[j]
                    orderList[j] = temp

        # TOTAL RECORDS AND PAGES
        totalOrders = len(orderList)
        totalPages = (totalOrders + limit - 1) // limit

        if totalPages > 0 and page > totalPages:
            page = totalPages

        if totalPages == 0:
            page = 1

        start = (page - 1) * limit
        end = start + limit

        paginatedOrders = orderList[start:end]

        previousPage = page - 1 if page > 1 else None
        nextPage = page + 1 if page < totalPages else None

        # COUNTS FOR ALL MATCHING CURRENT ORDERS
        pendingCount = 0
        processingCount = 0

        for order in orderList:
            if order["orderStatus"] == 1:
                pendingCount += 1
            elif order["orderStatus"] == 2:
                processingCount += 1

        return JsonResponse({
            "status": True,
            "orders": paginatedOrders,
            "totalOrders": totalOrders,
            "currentPage": page,
            "totalPages": totalPages,
            "limit": limit,
            "previousPage": previousPage,
            "nextPage": nextPage,
            "hasPrevious": previousPage is not None,
            "hasNext": nextPage is not None,
            "pendingCount": pendingCount,
            "processingCount": processingCount
        }, status=200)

    except (ValueError, TypeError):
        return JsonResponse({
            "status": False,
            "message": "Invalid page or limit value."
        }, status=400)

# # GET DELIVERY ORDERS API
# @api_view(["GET"])
# def get_delivery_orders(request):

#     shipmentObj = Shipment.objects.filter(
#         current_status__in=[1, 2, 3, 5]
#     ).select_related(
#         "order_id",
#         "order_id__user_id",
#         "order_id__address_id",
#         "delivery_partner_id"
#     ).order_by("-id")

#     shipmentList = []

#     for shipment in shipmentObj:

#         # SHIPMENT STATUS
#         if shipment.current_status == 1:
#             shipmentStatus = "Pending"

#         elif shipment.current_status == 2:
#             shipmentStatus = "Picked Up"

#         elif shipment.current_status == 3:
#             shipmentStatus = "Out for Delivery"

#         elif shipment.current_status == 5:
#             shipmentStatus = "Exception/Delayed"

#         else:
#             shipmentStatus = "Unknown"

#         # ORDER STATUS
#         order = shipment.order_id

#         if order.order_status == 1:
#             orderStatus = "Pending"

#         elif order.order_status == 2:
#             orderStatus = "Processing"

#         elif order.order_status == 3:
#             orderStatus = "Delivered"

#         elif order.order_status == 4:
#             orderStatus = "Cancelled"

#         else:
#             orderStatus = "Unknown"

#         # CUSTOMER
#         customerName = (
#             order.user_id.first_name
#             + " "
#             + order.user_id.last_name
#         )

#         # DELIVERY PARTNER
#         deliveryPartnerName = None
#         deliveryPartnerEmail = None
#         deliveryPartnerMobile = None
#         deliveryPartnerId = None

#         if shipment.delivery_partner_id:

#             deliveryPartnerId = shipment.delivery_partner_id.id

#             deliveryPartnerName = (
#                 shipment.delivery_partner_id.first_name
#                 + " "
#                 + shipment.delivery_partner_id.last_name
#             )

#             deliveryPartnerEmail = (
#                 shipment.delivery_partner_id.email
#             )

#             deliveryPartnerMobile = (
#                 shipment.delivery_partner_id.mobile_number
#             )

#         # ADDRESS
#         address = order.address_id.address_line1

#         city = ""

#         if order.address_id.city_id:
#             city = order.address_id.city_id.city_name

#         state = ""

#         if order.address_id.state_id:
#             state = order.address_id.state_id.state_name

#         # ADD DATA
#         shipmentList.append(
#             {
#                 "shipmentId": shipment.id,

#                 "orderId": order.id,
#                 "orderNumber": order.order_number,

#                 "customerId": order.user_id.id,
#                 "customerName": customerName,
#                 "customerEmail": order.user_id.email,
#                 "customerPhone": order.user_id.phone_number,

#                 "address": address,
#                 "city": city,
#                 "state": state,

#                 "deliveryPartnerId": deliveryPartnerId,
#                 "deliveryPartnerName": deliveryPartnerName,
#                 "deliveryPartnerEmail": deliveryPartnerEmail,
#                 "deliveryPartnerMobile": deliveryPartnerMobile,

#                 "shippingDate": shipment.shipping_date.strftime(
#                     "%d-%m-%Y %H:%M"
#                 ),

#                 "estimateDelivery": shipment.estimate_delivery.strftime(
#                     "%d-%m-%Y %H:%M"
#                 ),

#                 "deliveredDate": (
#                     shipment.delivered_date.strftime("%d-%m-%Y")
#                     if shipment.delivered_date
#                     else None
#                 ),

#                 "shipmentStatus": shipment.current_status,
#                 "shipmentStatusName": shipmentStatus,

#                 "orderStatus": order.order_status,
#                 "orderStatusName": orderStatus,

#                 "totalAmount": str(order.total_amount)
#             }
#         )

#     return JsonResponse({"shipments": shipmentList}, status=200)

@api_view(["GET"])
def get_delivery_orders(request):

    search = request.GET.get("search", "").strip().lower()
    shipmentStatusFilter = request.GET.get("shipmentStatus", "").strip()
    partnerFilter = request.GET.get("partner", "").strip()
    sort = request.GET.get("sort", "newest")

    try:
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))

        if page < 1:
            page = 1

        if limit not in [10, 20, 50]:
            limit = 10

        shipmentObj = Shipment.objects.filter(
            current_status__in=[1, 2, 3, 5]
        ).select_related(
            "order_id",
            "order_id__user_id",
            "order_id__address_id",
            "order_id__address_id__city_id",
            "order_id__address_id__state_id",
            "delivery_partner_id"
        ).order_by("-id")

        shipmentList = []

        for shipment in shipmentObj:

            order = shipment.order_id

            # SHIPMENT STATUS
            if shipment.current_status == 1:
                shipmentStatus = "Pending"
            elif shipment.current_status == 2:
                shipmentStatus = "Picked Up"
            elif shipment.current_status == 3:
                shipmentStatus = "Out for Delivery"
            elif shipment.current_status == 5:
                shipmentStatus = "Exception/Delayed"
            else:
                shipmentStatus = "Unknown"

            # ORDER STATUS
            if order.order_status == 1:
                orderStatus = "Pending"
            elif order.order_status == 2:
                orderStatus = "Processing"
            elif order.order_status == 3:
                orderStatus = "Delivered"
            elif order.order_status == 4:
                orderStatus = "Cancelled"
            else:
                orderStatus = "Unknown"

            # CUSTOMER
            customerName = (
                f"{order.user_id.first_name} "
                f"{order.user_id.last_name}"
            )

            # DELIVERY PARTNER
            deliveryPartnerName = None
            deliveryPartnerEmail = None
            deliveryPartnerMobile = None
            deliveryPartnerId = None

            if shipment.delivery_partner_id:

                deliveryPartnerId = shipment.delivery_partner_id.id

                deliveryPartnerName = (
                    f"{shipment.delivery_partner_id.first_name} "
                    f"{shipment.delivery_partner_id.last_name}"
                )

                deliveryPartnerEmail = (
                    shipment.delivery_partner_id.email
                )

                deliveryPartnerMobile = (
                    shipment.delivery_partner_id.mobile_number
                )

            # ADDRESS
            address = order.address_id.address_line1

            city = ""
            if order.address_id.city_id:
                city = order.address_id.city_id.city_name

            state = ""
            if order.address_id.state_id:
                state = order.address_id.state_id.state_name

            # SHIPMENT STATUS FILTER
            if shipmentStatusFilter:
                if str(shipment.current_status) != shipmentStatusFilter:
                    continue

            # DELIVERY PARTNER FILTER
            if partnerFilter == "assigned":
                if not shipment.delivery_partner_id:
                    continue

            elif partnerFilter == "unassigned":
                if shipment.delivery_partner_id:
                    continue

            # SEARCH
            searchableText = " ".join([
                str(shipment.id),
                str(order.id),
                str(order.order_number),
                customerName,
                str(order.user_id.email or ""),
                str(order.user_id.phone_number or ""),
                str(deliveryPartnerName or ""),
                str(deliveryPartnerEmail or ""),
                str(deliveryPartnerMobile or ""),
                str(address or ""),
                str(city or ""),
                str(state or ""),
                shipmentStatus,
                orderStatus
            ]).lower()

            if search:
                if search not in searchableText:
                    continue

            shipmentList.append({
                "shipmentId": shipment.id,

                "orderId": order.id,
                "orderNumber": order.order_number,

                "customerId": order.user_id.id,
                "customerName": customerName,
                "customerEmail": order.user_id.email,
                "customerPhone": order.user_id.phone_number,

                "address": address,
                "city": city,
                "state": state,

                "deliveryPartnerId": deliveryPartnerId,
                "deliveryPartnerName": deliveryPartnerName,
                "deliveryPartnerEmail": deliveryPartnerEmail,
                "deliveryPartnerMobile": deliveryPartnerMobile,

                "shippingDate": (
                    shipment.shipping_date.strftime("%d-%m-%Y %H:%M")
                    if shipment.shipping_date else ""
                ),

                "estimateDelivery": (
                    shipment.estimate_delivery.strftime("%d-%m-%Y %H:%M")
                    if shipment.estimate_delivery else ""
                ),

                "deliveredDate": (
                    shipment.delivered_date.strftime("%d-%m-%Y")
                    if shipment.delivered_date else None
                ),

                "shipmentStatus": shipment.current_status,
                "shipmentStatusName": shipmentStatus,

                "orderStatus": order.order_status,
                "orderStatusName": orderStatus,

                "totalAmount": str(order.total_amount),

                # Used internally for estimated delivery sorting
                "_estimateDeliverySort": (
                    shipment.estimate_delivery.isoformat()
                    if shipment.estimate_delivery else ""
                )
            })

        # SORTING
        for i in range(len(shipmentList)):
            for j in range(i + 1, len(shipmentList)):

                swap = False

                if sort == "newest":
                    if shipmentList[i]["shipmentId"] < shipmentList[j]["shipmentId"]:
                        swap = True

                elif sort == "oldest":
                    if shipmentList[i]["shipmentId"] > shipmentList[j]["shipmentId"]:
                        swap = True

                elif sort == "deliverySoonest":
                    dateOne = shipmentList[i]["_estimateDeliverySort"]
                    dateTwo = shipmentList[j]["_estimateDeliverySort"]

                    if dateTwo and (not dateOne or dateOne > dateTwo):
                        swap = True

                elif sort == "deliveryLatest":
                    dateOne = shipmentList[i]["_estimateDeliverySort"]
                    dateTwo = shipmentList[j]["_estimateDeliverySort"]

                    if dateOne and (not dateTwo or dateOne < dateTwo):
                        swap = True

                if swap:
                    temp = shipmentList[i]
                    shipmentList[i] = shipmentList[j]
                    shipmentList[j] = temp

        # STATUS COUNTS FOR ALL MATCHING SHIPMENTS
        pendingCount = 0
        pickedUpCount = 0
        outForDeliveryCount = 0
        exceptionCount = 0

        for shipment in shipmentList:

            if shipment["shipmentStatus"] == 1:
                pendingCount += 1
            elif shipment["shipmentStatus"] == 2:
                pickedUpCount += 1
            elif shipment["shipmentStatus"] == 3:
                outForDeliveryCount += 1
            elif shipment["shipmentStatus"] == 5:
                exceptionCount += 1

        # PAGINATION
        totalShipments = len(shipmentList)
        totalPages = (totalShipments + limit - 1) // limit

        if totalPages > 0 and page > totalPages:
            page = totalPages

        if totalPages == 0:
            page = 1

        start = (page - 1) * limit
        end = start + limit

        paginatedShipments = shipmentList[start:end]

        # Remove internal sorting field
        for shipment in paginatedShipments:
            del shipment["_estimateDeliverySort"]

        previousPage = page - 1 if page > 1 else None
        nextPage = page + 1 if page < totalPages else None

        return JsonResponse({
            "status": True,
            "shipments": paginatedShipments,

            "totalShipments": totalShipments,
            "currentPage": page,
            "totalPages": totalPages,
            "limit": limit,

            "previousPage": previousPage,
            "nextPage": nextPage,
            "hasPrevious": previousPage is not None,
            "hasNext": nextPage is not None,

            "pendingCount": pendingCount,
            "pickedUpCount": pickedUpCount,
            "outForDeliveryCount": outForDeliveryCount,
            "exceptionCount": exceptionCount
        }, status=200)

    except (ValueError, TypeError):
        return JsonResponse({
            "status": False,
            "message": "Invalid page or limit value."
        }, status=400)

# GET ORDERS HISTORY API
@api_view(["GET"])
def get_orders_history(request):

    orderObj = Order.objects.filter(
        order_status__in=[3, 4]
    ).order_by("-id")

    orderList = []

    for order in orderObj:

        if order.order_status == 3:
            orderStatus = "Delivered"
        else:
            orderStatus = "Cancelled"

        if order.payment_status == 1:
            paymentStatus = "Pending"
        elif order.payment_status == 2:
            paymentStatus = "Paid"
        elif order.payment_status == 3:
            paymentStatus = "Failed"
        else:
            paymentStatus = "Refunded"

        orderList.append(
            {
                "orderId": order.id,
                "orderNumber": order.order_number,

                "customerName":
                    order.user_id.first_name
                    + " "
                    + order.user_id.last_name,

                "customerEmail": order.user_id.email,

                "subtotal": str(order.subtotal),
                "tax": str(order.tax),
                "shippingCharge": str(order.shipping_charge),
                "totalAmount": str(order.total_amount),

                "paymentStatus": paymentStatus,
                "orderStatus": orderStatus,

                "placedAt": order.placed_at.strftime(
                    "%d-%m-%Y %H:%M"
                )
            }
        )

    return JsonResponse({"orders": orderList}, status=200)

# CHANGE ORDER STATUS API
@csrf_exempt
@api_view(["POST"])
def change_order_status(request):

    orderId = request.data.get("orderId")

    status = request.data.get("status")


    if not orderId:

        return JsonResponse({
            "success": False,
            "message": "Order ID is required."
        }, status=400)


    if not status:

        return JsonResponse({
            "success": False,
            "message": "Status is required."
        }, status=400)


    try:

        orderObj = Order.objects.get(id=orderId)

    except Order.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "Order not found."
        }, status=404)


    try:

        status = int(status)

    except ValueError:

        return JsonResponse({
            "success": False,
            "message": "Invalid status."
        }, status=400)


    if status not in [1, 2, 3, 4]:

        return JsonResponse({
            "success": False,
            "message": "Invalid order status."
        }, status=400)


    if orderObj.order_status == 3:

        return JsonResponse({
            "success": False,
            "message": "Delivered order status cannot be changed."
        }, status=400)


    if orderObj.order_status == 4:

        return JsonResponse({
            "success": False,
            "message": "Cancelled order status cannot be changed."
        }, status=400)


    orderObj.order_status = status

    orderObj.save()


    return JsonResponse({
        "success": True,
        "message": "Order status updated successfully.",
        "orderId": orderObj.id,
        "orderStatus": orderObj.order_status
    })

# GET PRODUCTS API
@api_view(["GET"])
def get_stock_products(request):

    products = Product.objects.all().order_by("name")

    product_list = []

    for product in products:
        product_list.append({
            "id": product.id,
            "name": product.name
        })

    return JsonResponse({
        "status": True,
        "products": product_list
    })

# GET VARIANTS OF PRODUCT API
@api_view(["GET"])
def get_product_stock_variants(request):

    product_id = request.GET.get("productId")

    if not product_id:
        return JsonResponse({
            "status": False,
            "message": "Product ID is required."
        }, status=400)

    variants = ProductVariant.objects.filter(
        product_id_id=product_id
    ).order_by("color", "size")

    variant_list = []

    for variant in variants:

        variant_list.append({
            "id": variant.id,
            "color": variant.color,
            "colorCode": variant.color_code,
            "size": variant.size,
            "mrp": str(variant.mrp),
            "sellingPrice": str(variant.selling_price),
            "costPrice": str(variant.cost_price),
            "stockQuantity": variant.stock_quantity,
            "minimumStock": variant.minimum_stock,
            "status": variant.status
        })

    return JsonResponse({
        "status": True,
        "variants": variant_list
    })

# ADD STOCK API
@csrf_exempt
@api_view(["POST"])
def add_stock(request):

    product_id = request.data.get("productId")
    variant_id = request.data.get("variantId")
    quantity = request.data.get("quantity")
    remarks = request.data.get("remarks", "")

    if not product_id:
        return JsonResponse({
            "status": False,
            "message": "Product is required."
        }, status=400)

    if not variant_id:
        return JsonResponse({
            "status": False,
            "message": "Variant is required."
        }, status=400)

    if not quantity:
        return JsonResponse({
            "status": False,
            "message": "Quantity is required."
        }, status=400)

    try:
        quantity = int(quantity)
    except:
        return JsonResponse({
            "status": False,
            "message": "Quantity must be a number."
        }, status=400)

    if quantity <= 0:
        return JsonResponse({
            "status": False,
            "message": "Quantity must be greater than 0."
        }, status=400)

    try:
        variant = ProductVariant.objects.get(
            id=variant_id,
            product_id_id=product_id
        )
    except ProductVariant.DoesNotExist:
        return JsonResponse({
            "status": False,
            "message": "Product variant not found."
        }, status=404)

    # Add quantity to current stock
    variant.stock_quantity += quantity
    variant.status = True
    variant.save()

    # Create inventory history
    ProductInventory.objects.create(
        variant_id=variant,
        quantity_change=quantity,
        operation=1,
        remarks=remarks
    )

    return JsonResponse({
        "status": True,
        "message": "Stock added successfully.",
        "stockQuantity": variant.stock_quantity
    })

# GET CURRENT STOCK API
@api_view(["GET"])
def get_current_stock(request):

    search = request.GET.get("search", "").strip()
    stockStatus = request.GET.get("stockStatus", "").strip()
    sort = request.GET.get("sort", "newest")

    try:
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))

        if page < 1:
            page = 1

        if limit < 1:
            limit = 10

        variants = ProductVariant.objects.filter(status=True).order_by("-id")

        stock_list = []

        for variant in variants:

            # STOCK STATUS
            if variant.stock_quantity <= 0:
                currentStatus = "Out of Stock"
            elif variant.stock_quantity <= variant.minimum_stock:
                currentStatus = "Low Stock"
            else:
                currentStatus = "In Stock"

            # SEARCH
            productName = variant.product_id.name
            color = variant.color
            size = variant.size

            if search:
                if (
                    search.lower() not in productName.lower()
                    and search.lower() not in color.lower()
                    and search.lower() not in size.lower()
                    and search.lower() not in str(variant.id)
                ):
                    continue

            # STATUS FILTER
            if stockStatus:
                if currentStatus != stockStatus:
                    continue

            stock_list.append({
                "id": variant.id,
                "productId": variant.product_id.id,
                "productName": productName,
                "color": color,
                "colorCode": variant.color_code,
                "size": size,
                "mrp": str(variant.mrp),
                "sellingPrice": str(variant.selling_price),
                "costPrice": str(variant.cost_price),
                "stockQuantity": variant.stock_quantity,
                "minimumStock": variant.minimum_stock,
                "stockStatus": currentStatus
            })

        # SORT
        for i in range(len(stock_list)):
            for j in range(i + 1, len(stock_list)):

                swap = False

                if sort == "newest":
                    if stock_list[i]["id"] < stock_list[j]["id"]:
                        swap = True

                elif sort == "oldest":
                    if stock_list[i]["id"] > stock_list[j]["id"]:
                        swap = True

                elif sort == "stockLow":
                    if stock_list[i]["stockQuantity"] > stock_list[j]["stockQuantity"]:
                        swap = True

                elif sort == "stockHigh":
                    if stock_list[i]["stockQuantity"] < stock_list[j]["stockQuantity"]:
                        swap = True

                if swap:
                    temp = stock_list[i]
                    stock_list[i] = stock_list[j]
                    stock_list[j] = temp

        # COUNT
        totalStock = len(stock_list)

        # PAGINATION
        totalPages = (totalStock + limit - 1) // limit

        if totalPages > 0 and page > totalPages:
            page = totalPages

        previousPage = page - 1 if page > 1 else None
        nextPage = page + 1 if page < totalPages else None

        start = (page - 1) * limit
        end = start + limit

        stock_list = stock_list[start:end]

        return JsonResponse({
            "status": True,
            "stock": stock_list,
            "totalStock": totalStock,
            "currentPage": page,
            "totalPages": totalPages,
            "limit": limit,
            "previousPage": previousPage,
            "nextPage": nextPage,
            "hasPrevious": previousPage is not None,
            "hasNext": nextPage is not None
        }, status=200)

    except Exception as e:
        return JsonResponse({
            "status": False,
            "message": str(e)
        }, status=400)

# @api_view(["GET"])
# def get_current_stock(request):

#     search = request.GET.get("search", "").strip().lower()
#     stockStatus = request.GET.get("stockStatus", "").strip()
#     colorFilter = request.GET.get("color", "").strip().lower()
#     sizeFilter = request.GET.get("size", "").strip().lower()
#     sort = request.GET.get("sort", "newest").strip()

#     try:
#         page = int(request.GET.get("page", 1))
#         limit = int(request.GET.get("limit", 10))

#         if page < 1:
#             page = 1

#         if limit not in [5, 10, 20, 50]:
#             limit = 10

#         # Read numeric filter values
#         minMRP = request.GET.get("minMRP", "").strip()
#         maxMRP = request.GET.get("maxMRP", "").strip()
#         minSellingPrice = request.GET.get("minSellingPrice", "").strip()
#         maxSellingPrice = request.GET.get("maxSellingPrice", "").strip()
#         minStock = request.GET.get("minStock", "").strip()
#         maxStock = request.GET.get("maxStock", "").strip()

#         def get_decimal(value):
#             if value == "":
#                 return None

#             number = Decimal(value)

#             if not number.is_finite() or number < 0:
#                 raise ValueError("Price and stock filters must be non-negative numbers.")

#             return number

#         minMRP = get_decimal(minMRP)
#         maxMRP = get_decimal(maxMRP)
#         minSellingPrice = get_decimal(minSellingPrice)
#         maxSellingPrice = get_decimal(maxSellingPrice)
#         minStock = get_decimal(minStock)
#         maxStock = get_decimal(maxStock)

#         if minMRP is not None and maxMRP is not None and minMRP > maxMRP:
#             raise ValueError("Minimum MRP cannot be greater than maximum MRP.")

#         if minSellingPrice is not None and maxSellingPrice is not None and minSellingPrice > maxSellingPrice:
#             raise ValueError("Minimum selling price cannot be greater than maximum selling price.")

#         if minStock is not None and maxStock is not None and minStock > maxStock:
#             raise ValueError("Minimum stock cannot be greater than maximum stock.")

#         variants = ProductVariant.objects.filter(status=True).select_related(
#             "product_id"
#         )

#         stock_list = []

#         for variant in variants:

#             product = variant.product_id
#             productName = product.name or ""
#             color = variant.color or ""
#             size = variant.size or ""

#             quantity = variant.stock_quantity
#             minimumStock = variant.minimum_stock

#             mrp = Decimal(str(variant.mrp))
#             sellingPrice = Decimal(str(variant.selling_price))

#             # Determine stock status
#             if quantity <= 0:
#                 currentStatus = "Out of Stock"
#             elif quantity <= minimumStock:
#                 currentStatus = "Low Stock"
#             else:
#                 currentStatus = "In Stock"

#             # Search: ID, product ID, product name, color, color code and size
#             if search:
#                 searchValues = [
#                     str(variant.id),
#                     str(product.id),
#                     productName.lower(),
#                     color.lower(),
#                     str(variant.color_code or "").lower(),
#                     size.lower()
#                 ]

#                 found = False

#                 for value in searchValues:
#                     if search in value:
#                         found = True
#                         break

#                 if not found:
#                     continue

#             # Color filter
#             if colorFilter and colorFilter not in color.lower():
#                 continue

#             # Size filter
#             if sizeFilter and sizeFilter != size.lower():
#                 continue

#             # Stock status filter
#             if stockStatus and currentStatus != stockStatus:
#                 continue

#             # MRP range
#             if minMRP is not None and mrp < minMRP:
#                 continue

#             if maxMRP is not None and mrp > maxMRP:
#                 continue

#             # Selling price range
#             if minSellingPrice is not None and sellingPrice < minSellingPrice:
#                 continue

#             if maxSellingPrice is not None and sellingPrice > maxSellingPrice:
#                 continue

#             # Quantity range
#             if minStock is not None and quantity < minStock:
#                 continue

#             if maxStock is not None and quantity > maxStock:
#                 continue

#             stock_list.append({
#                 "id": variant.id,
#                 "productId": product.id,
#                 "productName": productName,
#                 "color": color,
#                 "colorCode": variant.color_code or "",
#                 "size": size,
#                 "mrp": str(variant.mrp),
#                 "sellingPrice": str(variant.selling_price),
#                 "costPrice": str(variant.cost_price),
#                 "stockQuantity": quantity,
#                 "minimumStock": minimumStock,
#                 "stockStatus": currentStatus
#             })

#         # Sorting
#         if sort == "newest":
#             stock_list.sort(key=lambda item: item["id"], reverse=True)

#         elif sort == "oldest":
#             stock_list.sort(key=lambda item: item["id"])

#         elif sort == "name_asc":
#             stock_list.sort(key=lambda item: item["productName"].lower())

#         elif sort == "name_desc":
#             stock_list.sort(key=lambda item: item["productName"].lower(), reverse=True)

#         elif sort == "stockLow":
#             stock_list.sort(key=lambda item: item["stockQuantity"])

#         elif sort == "stockHigh":
#             stock_list.sort(key=lambda item: item["stockQuantity"], reverse=True)

#         elif sort == "priceLow":
#             stock_list.sort(key=lambda item: Decimal(item["sellingPrice"]))

#         elif sort == "priceHigh":
#             stock_list.sort(key=lambda item: Decimal(item["sellingPrice"]), reverse=True)

#         elif sort == "mrpLow":
#             stock_list.sort(key=lambda item: Decimal(item["mrp"]))

#         else:
#             stock_list.sort(key=lambda item: item["id"], reverse=True)

#         # Count before pagination
#         totalStock = len(stock_list)
#         totalPages = (totalStock + limit - 1) // limit

#         if totalPages > 0 and page > totalPages:
#             page = totalPages

#         if totalPages == 0:
#             page = 1

#         previousPage = page - 1 if page > 1 else None
#         nextPage = page + 1 if page < totalPages else None

#         start = (page - 1) * limit
#         end = start + limit

#         paginatedStock = stock_list[start:end]

#         return JsonResponse({
#             "status": True,
#             "stock": paginatedStock,
#             "totalStock": totalStock,
#             "currentPage": page,
#             "totalPages": totalPages,
#             "limit": limit,
#             "previousPage": previousPage,
#             "nextPage": nextPage,
#             "hasPrevious": previousPage is not None,
#             "hasNext": nextPage is not None
#         }, status=200)

#     except (ValueError, InvalidOperation) as e:
#         return JsonResponse({
#             "status": False,
#             "message": str(e) or "Please enter valid filter values."
#         }, status=400)

#     except Exception as e:
#         return JsonResponse({
#             "status": False,
#             "message": "Unable to load stock."
#         }, status=400)

# GET SINGLE STOCK FOR EDIT API
@api_view(["GET"])
def get_stock_detail(request):

    variant_id = request.GET.get("variantId")

    if not variant_id:
        return JsonResponse({
            "status": False,
            "message": "Variant ID is required."
        }, status=400)

    try:
        variant = ProductVariant.objects.select_related(
            "product_id"
        ).get(id=variant_id)
    except ProductVariant.DoesNotExist:
        return JsonResponse({
            "status": False,
            "message": "Stock not found."
        }, status=404)

    return JsonResponse({
        "status": True,
        "stock": {
            "id": variant.id,
            "productId": variant.product_id.id,
            "productName": variant.product_id.name,
            "color": variant.color,
            "colorCode": variant.color_code,
            "size": variant.size,
            "mrp": str(variant.mrp),
            "sellingPrice": str(variant.selling_price),
            "costPrice": str(variant.cost_price),
            "stockQuantity": variant.stock_quantity,
            "minimumStock": variant.minimum_stock
        }
    })

# UPDATE STOCK API
@csrf_exempt
@api_view(["PUT"])
def update_stock(request):

    variant_id = request.data.get("variantId")
    quantity = request.data.get("quantity")
    remarks = request.data.get("remarks", "")

    if not variant_id:
        return JsonResponse({
            "status": False,
            "message": "Variant ID is required."
        }, status=400)

    if quantity is None:
        return JsonResponse({
            "status": False,
            "message": "Quantity is required."
        }, status=400)

    try:
        quantity = int(quantity)
    except:
        return JsonResponse({
            "status": False,
            "message": "Quantity must be a number."
        }, status=400)

    if quantity < 0:
        return JsonResponse({
            "status": False,
            "message": "Quantity cannot be negative."
        }, status=400)

    try:
        variant = ProductVariant.objects.get(id=variant_id)
    except ProductVariant.DoesNotExist:
        return JsonResponse({
            "status": False,
            "message": "Stock not found."
        }, status=404)

    old_quantity = variant.stock_quantity

    variant.stock_quantity = quantity
    variant.status = True
    variant.save()

    quantity_change = quantity - old_quantity

    ProductInventory.objects.create(
        variant_id=variant,
        quantity_change=quantity_change,
        operation=2,
        remarks=remarks
    )

    return JsonResponse({
        "status": True,
        "message": "Stock updated successfully.",
        "stockQuantity": variant.stock_quantity
    })

# DELETE STOCK API
@csrf_exempt
@api_view(["DELETE"])
def delete_stock(request):
    print("DELETE API CALLED")
    variant_id = request.GET.get("variantId")

    if not variant_id:
        return JsonResponse({
            "status": False,
            "message": "Variant ID is required."
        }, status=400)

    try:
        variant = ProductVariant.objects.get(id=variant_id)
    except ProductVariant.DoesNotExist:
        return JsonResponse({
            "status": False,
            "message": "Stock not found."
        }, status=404)

    # Save inventory history before deleting
    ProductInventory.objects.create(
        variant_id=variant,
        quantity_change=variant.stock_quantity,
        operation=3,
        remarks="Stock deleted"
    )

    variant.delete()

    return JsonResponse({
        "status": True,
        "message": "Stock deleted successfully."
    })

# ADD PRODUCT VARIANT API
@csrf_exempt
@api_view(["POST"])
def add_product_variant(request):

    productId = request.data.get("productId")
    color = request.data.get("color")
    colorCode = request.data.get("colorCode")
    size = request.data.get("size")
    mrp = request.data.get("mrp")
    sellingPrice = request.data.get("sellingPrice")
    costPrice = request.data.get("costPrice")
    stockQuantity = request.data.get("stockQuantity")
    minimumStock = request.data.get("minimumStock")

    if not productId:
        return JsonResponse({
            "message": "Product Id is required."
        }, status=400)

    if not color:
        return JsonResponse({
            "message": "Color is required."
        }, status=400)

    if not colorCode:
        return JsonResponse({
            "message": "Color code is required."
        }, status=400)

    if not size:
        return JsonResponse({
            "message": "Size is required."
        }, status=400)

    if not mrp:
        return JsonResponse({
            "message": "MRP is required."
        }, status=400)

    if not sellingPrice:
        return JsonResponse({
            "message": "Selling price is required."
        }, status=400)

    if not costPrice:
        return JsonResponse({
            "message": "Cost price is required."
        }, status=400)

    if not stockQuantity:
        return JsonResponse({
            "message": "Stock quantity is required."
        }, status=400)

    if not minimumStock:
        return JsonResponse({
            "message": "Minimum stock is required."
        }, status=400)

    productObj = Product.objects.filter(
        id=productId,
        status=True
    ).first()

    if not productObj:
        return JsonResponse({
            "message": "Product not found."
        }, status=404)

    variantObj = ProductVariant.objects.filter(
        product_id=productObj,
        color=color,
        size=size,
        status=True
    ).first()

    if variantObj:
        return JsonResponse({
            "message": "This product variant already exists."
        }, status=400)

    variantObj = ProductVariant.objects.create(
        product_id=productObj,
        color=color,
        color_code=colorCode,
        size=size,
        mrp=mrp,
        selling_price=sellingPrice,
        cost_price=costPrice,
        stock_quantity=stockQuantity,
        minimum_stock=minimumStock,
        status=True
    )

    ProductInventory.objects.create(
        variant_id=variantObj,
        quantity_change=stockQuantity,
        operation=1,
        remarks="New variant created"
    )

    return JsonResponse({
        "message": "Product variant added successfully.",
        "variantId": variantObj.id
    }, status=201)

# GET TOTAL PAYMENTS API
@csrf_exempt
@api_view(["GET"])
def get_total_payments(request):

    search = request.GET.get("search", "").strip()
    paymentStatus = request.GET.get("paymentStatus", "").strip()
    paymentMethod = request.GET.get("paymentMethod", "").strip()
    sort = request.GET.get("sort", "newest")

    try:
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))

        if page < 1:
            page = 1

        if limit < 1:
            limit = 10

        paymentObj = Payment.objects.all()

        paymentList = []

        for payment in paymentObj:

            # SEARCH
            orderNumber = str(payment.order_id.order_number)
            transactionId = payment.transaction_id or ""

            if search:
                if (
                    search.lower() not in orderNumber.lower()
                    and search.lower() not in transactionId.lower()
                ):
                    continue

            # PAYMENT STATUS FILTER
            if paymentStatus:
                statusName = payment.get_payment_status_display()

                if statusName.lower() != paymentStatus.lower():
                    continue

            # PAYMENT METHOD FILTER
            if paymentMethod:
                if str(payment.payment_method) != paymentMethod:
                    continue

            paymentList.append(payment)

        # SORT
        if sort == "newest":
            paymentList.sort(key=lambda payment: payment.id, reverse=True)

        elif sort == "oldest":
            paymentList.sort(key=lambda payment: payment.id)

        elif sort == "amountLow":
            paymentList.sort(key=lambda payment: payment.amount)

        elif sort == "amountHigh":
            paymentList.sort(key=lambda payment: payment.amount, reverse=True)

        # COUNT
        totalPayments = len(paymentList)

        # PAGINATION
        totalPages = (totalPayments + limit - 1) // limit

        previousPage = page - 1 if page > 1 else None
        nextPage = page + 1 if page < totalPages else None

        start = (page - 1) * limit
        end = start + limit
        
        paymentList = paymentList[start:end]

        # PAYMENT DATA
        paymentData = []

        for payment in paymentList:

            paymentData.append({
                "paymentId": payment.id,
                "orderId": payment.order_id.id,
                "orderNumber": payment.order_id.order_number,
                "paymentMethod": payment.get_payment_method_display(),
                "transactionId": payment.transaction_id if payment.transaction_id else "-",
                "paymentStatus": payment.get_payment_status_display(),
                "amount": str(payment.amount),
                "paidAt": payment.paid_at if payment.paid_at else "-"
            })
        
        return JsonResponse({
            "payment": paymentData,
            "total": totalPayments,
            "currentPage": page,
            "totalPages": totalPages,
            "limit": limit,
            "previousPage": previousPage,
            "nextPage": nextPage,
            "hasPrevious": previousPage is not None,
            "hasNext": nextPage is not None
        }, status=200)

    except Exception as e:
        return JsonResponse({
            "error": str(e)
        }, status=400)

@api_view(["GET"])
def get_order_detail(request, orderId):

    print("Received Order ID:", orderId)


    try:
        order = Order.objects.select_related(
            "user_id",
            "address_id",
            "address_id__city_id",
            "address_id__state_id"
        ).get(id=orderId)

        customer = order.user_id
        address = order.address_id

        customerName = (
            f"{customer.first_name} {customer.last_name}"
        ).strip()

        addressLine = ""
        city = ""
        state = ""
        postalCode = ""

        if address:
            addressLine = address.address_line1 or ""

            if address.city_id:
                city = address.city_id.city_name

            if address.state_id:
                state = address.state_id.state_name

            postalCode = getattr(address, "postal_code", "") or ""

        if order.order_status == 1:
            orderStatusName = "Pending"
        elif order.order_status == 2:
            orderStatusName = "Processing"
        elif order.order_status == 3:
            orderStatusName = "Delivered"
        elif order.order_status == 4:
            orderStatusName = "Cancelled"
        else:
            orderStatusName = "Unknown"

        orderItems = OrderItem.objects.filter(
            order_id=order
        ).select_related(
            "product_variant_id",
            "product_variant_id__product_id"
        )

        productList = []
        subtotal = 0

        for item in orderItems:
            variant = item.product_variant_id
            product = variant.product_id

            quantity = item.quantity

            # Use the saved order-item price if your model has one.
            # Otherwise, this example uses the variant selling price.
            itemPrice = getattr(
                item,
                "price",
                variant.selling_price
            )

            lineTotal = itemPrice * quantity
            subtotal = subtotal + lineTotal

            productList.append({
                "productId": product.id,
                "productName": product.name,
                "variantId": variant.id,
                "color": variant.color,
                "size": variant.size,
                "quantity": quantity,
                "unitPrice": str(itemPrice),
                "lineTotal": str(lineTotal)
            })

        return JsonResponse({
            "status": True,
            "order": {
                "orderId": order.id,
                "orderNumber": order.order_number,
                "orderStatus": order.order_status,
                "orderStatusName": orderStatusName,
                "placedAt": order.placed_at,
                "totalAmount": str(order.total_amount),
                "customer": {
                    "customerId": customer.id,
                    "customerName": customerName,
                    "email": customer.email,
                    "phone": getattr(customer, "phone_number", "")
                },
                "address": {
                    "addressLine": addressLine,
                    "city": city,
                    "state": state,
                    "postalCode": postalCode
                },
                "products": productList,
                "subtotal": str(subtotal)
            }
        }, status=200)

    except Order.DoesNotExist:
        return JsonResponse({
            "status": False,
            "message": "Order not found."
        }, status=404)

    except (ValueError, TypeError, AttributeError) as error:
        return JsonResponse({
            "status": False,
            "message": "Unable to load order details.",
            "error": str(error)
        }, status=400)


@api_view(["GET"]) 
def get_admin_dashboard_data(request):
    try:
        # Total records
        totalOrders = Order.objects.count()
        totalProducts = Product.objects.count()
        totalCustomers = User.objects.count()

        # Sales excluding cancelled orders
        completedSalesOrders = Order.objects.exclude(
            order_status=4
        )

        totalSales = completedSalesOrders.aggregate(
            total=Sum("total_amount")
        )["total"] or 0

        # Order status counts
        pendingOrders = Order.objects.filter(
            order_status=1
        ).count()

        processingOrders = Order.objects.filter(
            order_status=2
        ).count()

        deliveredOrders = Order.objects.filter(
            order_status=3
        ).count()

        cancelledOrders = Order.objects.filter(
            order_status=4
        ).count()

        # Low stock count
        lowStockCount = ProductVariant.objects.filter(
            status=True,
            stock_quantity__lte=0
        ).count()

        # Count all active variants at or below minimum stock
        lowStockCount = 0

        for variant in ProductVariant.objects.filter(status=True):
            if variant.stock_quantity <= variant.minimum_stock:
                lowStockCount += 1

        # Monthly sales for the last 6 months
        today = django_timezone.now().date()
        monthlySales = []

        for monthOffset in range(5, -1, -1):
            monthNumber = today.month - monthOffset
            yearNumber = today.year

            while monthNumber <= 0:
                monthNumber += 12
                yearNumber -= 1

            monthOrders = Order.objects.filter(
                placed_at__year=yearNumber,
                placed_at__month=monthNumber
            ).exclude(order_status=4)

            monthTotal = monthOrders.aggregate(
                total=Sum("total_amount")
            )["total"] or 0

            monthlySales.append({
                "month": datetime(
                    yearNumber, monthNumber, 1
                ).strftime("%b %Y"),
                "sales": float(monthTotal)
            })

        # Recent orders
        recentOrders = Order.objects.select_related(
            "user_id"
        ).order_by("-placed_at")[:5]

        orderList = []

        for order in recentOrders:
            customerName = (
                f"{order.user_id.first_name or ''} "
                f"{order.user_id.last_name or ''}"
            ).strip()

            statusNames = {
                1: "Pending",
                2: "Processing",
                3: "Delivered",
                4: "Cancelled"
            }

            orderList.append({
                "orderId": order.id,
                "orderNumber": order.order_number,
                "customerName": customerName or "-",
                "totalAmount": str(order.total_amount),
                "paymentStatus": str(order.payment_status),
                "orderStatus": statusNames.get(
                    order.order_status, "Unknown"
                ),
                "placedAt": (
                    order.placed_at.strftime("%d-%m-%Y %H:%M")
                    if order.placed_at else "-"
                )
            })

        return JsonResponse({
            "status": True,
            "totalOrders": totalOrders,
            "totalProducts": totalProducts,
            "totalCustomers": totalCustomers,
            "totalSales": str(totalSales),
            "pendingOrders": pendingOrders,
            "processingOrders": processingOrders,
            "deliveredOrders": deliveredOrders,
            "cancelledOrders": cancelledOrders,
            "lowStockCount": lowStockCount,
            "monthlySales": monthlySales,
            "recentOrders": orderList
        }, status=200)

    except Exception as error:
        print("Admin dashboard error:", str(error))

        return JsonResponse({
            "status": False,
            "message": "Unable to load dashboard data.",
            "error": str(error)
        }, status=500)


# @api_view(["POST"])
# def admin_login_api(request):

#     email = request.data.get("email", "").strip()
#     password = request.data.get("password", "")

#     if not email or not password:
#         return JsonResponse({
#             "status": "error",
#             "message": "Email and password are required."
#         }, status=400)

#     try:
#         admin = AdminUser.objects.get(email__iexact=email)
#     except AdminUser.DoesNotExist:
#         return JsonResponse({
#             "status": "error",
#             "message": "Invalid email or password."
#         }, status=401)

#     if admin.password != password:
#         return JsonResponse({
#             "status": "error",
#             "message": "Invalid email or password."
#         }, status=401)

#     token = create_admin_token(admin)

#     return JsonResponse({
#         "status": "success",
#         "message": "Login successful.",
#         "token": token,
#         "admin": {
#             "id": admin.id,
#             "user_name": admin.user_name,
#             "email": admin.email
#         }
#     })



# @api_view(["GET"])
# def admin_profile_api(request):
#     token = request.headers.get("Authorization", "").strip()

#     admin = verify_admin_token(token)

#     if isinstance(admin, dict):
#         return JsonResponse(admin, status=401)

#     profileImage = ""

#     if admin.profile_image:
#         profileImage = request.build_absolute_uri(
#             admin.profile_image.url
#         )

#     return JsonResponse({
#         "status": "success",
#         "admin": {
#             "id": admin.id,
#             "user_name": admin.user_name,
#             "email": admin.email,
#             "profile_image": profileImage
#         }
#     })


# @api_view(["POST"])
# def admin_logout_api(request):

#     token = request.headers.get("Authorization", "")
    
    
#     admin = verify_admin_token(token)
   

#     if isinstance(admin, dict):
#         return JsonResponse(admin, status=401)

#     delete_admin_token(token)

#     return JsonResponse({
#         "status": "success",
#         "message": "Logout successful."
#     })



@csrf_exempt
@api_view(["POST"])
def admin_login_api(request):
    email = request.data.get("email", "")
    password = request.data.get("password", "")

    if not isinstance(email, str) or not isinstance(password, str):
        return JsonResponse({
            "status": "error",
            "message": "Invalid email or password."
        }, status=400)

    email = email.strip().lower()

    if not email or not password:
        return JsonResponse({
            "status": "error",
            "message": "Email and password are required."
        }, status=400)

    admin = AdminUser.objects.filter(
        email__iexact=email
    ).first()

    if not admin or admin.password != password:
        return JsonResponse({
            "status": "error",
            "message": "Invalid email or password."
        }, status=401)

    token = create_admin_token(admin)

    profile_image = ""

    if admin.profile_image:
        profile_image = request.build_absolute_uri(
            admin.profile_image.url
        )

    return JsonResponse({
        "status": "success",
        "message": "Login successful.",
        "token": token,
        "admin": {
            "id": admin.id,
            "user_name": admin.user_name,
            "email": admin.email,
            "profile_image": profile_image
        }
    })

@csrf_exempt
@api_view(["GET"])
def admin_profile_api(request):
    token = request.headers.get("Authorization", "").strip()

    admin = verify_admin_token(token)

    if isinstance(admin, dict):
        return JsonResponse(admin, status=401)

    profileImage = ""

    if admin.profile_image:
        profileImage = request.build_absolute_uri(
            admin.profile_image.url
        )

    response = JsonResponse({
        "status": "success",
        "admin": {
            "id": admin.id,
            "user_name": admin.user_name,
            "email": admin.email,
            "profile_image": profileImage
        }
    })

    response["Cache-Control"] = "no-store"
    return response

# ADMIN UPDATE PROFILE API
@csrf_exempt
@api_view(["POST"])
def admin_update_profile_api(request):
    token = request.headers.get("Authorization", "").strip()

    admin = verify_admin_token(token)

    if isinstance(admin, dict):
        return JsonResponse(admin, status=401)

    userName = request.data.get("user_name", "").strip()
    email = request.data.get("email", "").strip()

    if not userName or not email:
        return JsonResponse({
            "status": "error",
            "message": "Username and email are required."
        }, status=400)

    if AdminUser.objects.filter(
        email__iexact=email
    ).exclude(id=admin.id).exists():
        return JsonResponse({
            "status": "error",
            "message": "This email is already used."
        }, status=400)

    admin.user_name = userName
    admin.email = email

    if "profile_image" in request.FILES:
        imageFile = request.FILES["profile_image"]

        if imageFile.size > 2 * 1024 * 1024:
            return JsonResponse({
                "status": "error",
                "message": "Image must be 2 MB or smaller."
            }, status=400)

        if imageFile.content_type not in [
            "image/jpeg",
            "image/png",
            "image/webp"
        ]:
            return JsonResponse({
                "status": "error",
                "message": "Only JPG, PNG, and WEBP images are allowed."
            }, status=400)

        admin.profile_image = imageFile

    admin.save()

    profileImage = ""

    if admin.profile_image:
        profileImage = request.build_absolute_uri(
            admin.profile_image.url
        )

    return JsonResponse({
        "status": "success",
        "message": "Profile updated successfully.",
        "admin": {
            "id": admin.id,
            "user_name": admin.user_name,
            "email": admin.email,
            "profile_image": profileImage
        }
    })

# ADMIN LOGOUT API
@csrf_exempt
@api_view(["POST"])
def admin_logout_api(request):
    token = request.headers.get("Authorization", "").strip()

    if not token:
        return JsonResponse({
            "status": "error",
            "message": "Token is required."
        }, status=401)

    admin = verify_admin_token(token)

    if isinstance(admin, dict):
        # A token that is already revoked or expired is not valid.
        return JsonResponse(admin, status=401)

    delete_admin_token(token)

    return JsonResponse({
        "status": "success",
        "message": "Logout successful."
    })

# ADMIN FORGOT PASSWORD API
@csrf_exempt
@api_view(["POST"])
def admin_forgot_password_api(request):
    try:
        email = request.data.get("email", "")

        # Validate email input
        if not isinstance(email, str):
            return JsonResponse({
                "status": False,
                "message": "Email must be a valid string."
            }, status=400)

        email = email.strip().lower()

        if not email:
            return JsonResponse({
                "status": False,
                "message": "Email is required."
            }, status=400)

        # Find admin account
        admin = AdminUser.objects.filter(
            email__iexact=email
        ).first()

        # Do not reveal whether the account exists
        if not admin:
            return JsonResponse({
                "status": True,
                "message": "OTP will be sent."
            }, status=200)

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # Save hashed OTP and expiry time
        admin.otp = make_password(otp)
        admin.otp_created_at = django_timezone.now()
        admin.otp_expiry = django_timezone.now() + timedelta(minutes=10)

        admin.save(update_fields=[
            "otp",
            "otp_created_at",
            "otp_expiry"
        ])

        # Send OTP to admin email
        try:
            send_mail(
                subject="StyleCraft Admin Password Reset",
                message=(
                    f"Your password reset OTP is {otp}.\n\n"
                    "This OTP expires in 10 minutes."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin.email],
                fail_silently=False
            )

        except Exception as e:
            print("Forgot password email error:", repr(e))

            admin.otp = None
            admin.otp_created_at = None
            admin.otp_expiry = None

            admin.save(update_fields=[
                "otp",
                "otp_created_at",
                "otp_expiry"
            ])

            return JsonResponse({
                "status": False,
                "message": "Unable to send OTP. Please check email settings."
            }, status=500)

        return JsonResponse({
            "status": True,
            "message": "If the account exists, an OTP will be sent."
        }, status=200)

    except Exception as e:
        # Print the actual error in the Django terminal
        print("Forgot password API error:", repr(e))

        return JsonResponse({
            "status": False,
            "message": "Something went wrong. Check the Django terminal."
        }, status=500)

# ADMIN RESET PASSWORD API
@csrf_exempt
@api_view(["POST"])
def admin_reset_password_api(request):
    try:
        
        email = request.data.get("email", "").strip().lower()
        otp = request.data.get("otp", "").strip()
        new_password = request.data.get("newPassword", "")
        confirm_password = request.data.get("confirmPassword", "")

        if not all([email, otp, new_password, confirm_password]):
            return JsonResponse({
                "status": False,
                "message": "All fields are required."
            }, status=400)

        if new_password != confirm_password:
            return JsonResponse({
                "status": False,
                "message": "Passwords do not match."
            }, status=400)

        if len(new_password) < 8 or len(new_password) > 16:
            return JsonResponse({
                "status": False,
                "message": "Password must be 8 to 16 characters."
            }, status=400)

        has_upper = False
        has_lower = False
        has_digit = False
        has_special = False

        for char in new_password:
            if char.isupper():
                has_upper = True
            elif char.islower():
                has_lower = True
            elif char.isdigit():
                has_digit = True
            else:
                has_special = True

        if not (
            has_upper and has_lower and has_digit and has_special
        ):
            return JsonResponse({
                "status": False,
                "message": (
                    "Include uppercase, lowercase, number, "
                    "and special character."
                )
            }, status=400)

        try:
            admin = AdminUser.objects.get(email__iexact=email)
        except AdminUser.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Invalid or expired OTP."
            }, status=400)

        if not admin.otp or not admin.otp_expiry:
            return JsonResponse({
                "status": False,
                "message": "Please request a new OTP."
            }, status=400)

        if django_timezone.now() >= admin.otp_expiry:
            admin.otp = None
            admin.otp_expiry = None
            admin.save(update_fields=["otp", "otp_expiry"])

            return JsonResponse({
                "status": False,
                "message": "OTP has expired."
            }, status=400)

        
        # Verify the OTP
        if not check_password(otp, admin.otp):
            return JsonResponse({
                "status": False,
                "message": "Incorrect OTP."
            }, status=400)

        # Save password in the format expected by your current login API
        admin.password = new_password

        # Clear OTP fields after successful reset
        admin.otp = None
        admin.otp_created_at = None
        admin.otp_expiry = None

        admin.save(update_fields=[
            "password",
            "otp",
            "otp_created_at",
            "otp_expiry"
        ])

        return JsonResponse({
            "status": True,
            "message": "Password reset successfully. Please log in."
        }, status=200)

    except (ValueError, TypeError):
        return JsonResponse({
            "status": False,
            "message": "Invalid request data."
        }, status=400)

# GLOBAL SEARCH API 
@api_view(["GET"])
def global_page_search(request):

    search = request.GET.get("q", "").strip().lower()

    pages = [
        {
            "name": "Dashboard",
            "url_name": "adminIndex",
            "keywords": "home analytics overview"
        },
        {
            "name": "View Products",
            "url_name": "viewProducts",
            "keywords": "product list"
        },
        {
            "name": "Add New Product",
            "url_name": "addNewProduct",
            "keywords": "create product"
        },
        {
            "name": "Add New Product Variant",
            "url_name": "addNewProductVariant",
            "keywords": "create product variant"
        },
        {
            "name": "View Category",
            "url_name": "viewCategory",
            "keywords": "category list"
        },
        {
            "name": "Add New Category",
            "url_name": "addNewCategory",
            "keywords": "create category"
        },
        {
            "name": "Add New Stock",
            "url_name": "addNewStock",
            "keywords": "add stock"
        },
        {
            "name": "View Current Stock",
            "url_name": "viewCurrentStock",
            "keywords": "view stock list"
        },
        {
            "name": "Current Orders",
            "url_name": "currentOrders",
            "keywords": "pending orders"
        },
        {
            "name": "In Delivery",
            "url_name": "inDeliveryOrders",
            "keywords": "shipping delivery"
        },
        {
            "name": "Order History",
            "url_name": "orderHistory",
            "keywords": "previous orders"
        },
        {
            "name": "Total Payments",
            "url_name": "totalPayments",
            "keywords": "transactions"
        },
        {
            "name": "My Profile",
            "url_name": "adminProfile",
            "keywords": "account profile settings"
        },
    ]

    results = []

    for page in pages:

        searchable_text = (
            page["name"] + " " + page["keywords"]
        ).lower()

        if search and search not in searchable_text:
            continue

        try:
            page_url = reverse(
                "custom_admin:" + page["url_name"]
            )
        except Exception:
            continue

        results.append({
            "name": page["name"],
            "url": page_url,
        })

    return JsonResponse({
        "status": True,
        "total": len(results),
        "results": results,
    })