from .models import *
from django.contrib import admin
from django.utils.html import format_html
from django.conf.urls.static import static

class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name','last_name', 'email', 'phone_number', 'image']
    def image(self, obj):
        if obj.profile_image:
            return format_html(
                '<img src="{}" width="70" height="70" '
                'style="object-fit:cover;border-radius:5px;" />',
                obj.profile_image.url
            )
admin.site.register(User, UserAdmin)

class AdminUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_name', 'email']
admin.site.register(AdminUser, AdminUserAdmin)

class AdminTokenAdmin(admin.ModelAdmin):
    list_display = ['token_id', 'user_id', 'token', 'created_at', 'expiry_time']
admin.site.register(AdminToken, AdminTokenAdmin)

class CountryAdmin(admin.ModelAdmin):
    list_display = ['country_id', 'country_name']
admin.site.register(Country, CountryAdmin)

class StateAdmin(admin.ModelAdmin):
    list_display = ['state_id', 'state_name', 'country_id']
admin.site.register(State, StateAdmin)

class CityAdmin(admin.ModelAdmin):
    list_display = ['city_id', 'city_name', 'state_id']
admin.site.register(City, CityAdmin)

class AreaAdmin(admin.ModelAdmin):
    list_display = ['area_id', 'area_name', 'city_id']
admin.site.register(Area, AreaAdmin)

class AddressAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'address_line1', 'address_line2', 'postal_code', 'country_id', 'state_id', 'city_id', 'address_type']
admin.site.register(Address, AddressAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'parent_category_id', 'name', 'description', 'categoryimage', 'status']
    def categoryimage(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="70" height="70" '
                'style="object-fit:cover;border-radius:5px;" />',
                obj.image.url
            )
admin.site.register(Category, CategoryAdmin)

class BrandAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'brandlogo', 'description', 'website', 'status']
    def brandlogo(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" width="70" height="70" '
                'style="object-fit:cover;border-radius:5px;" />',
                obj.logo.url
            )
admin.site.register(Brand, BrandAdmin)

class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'category_id', 'brand_id', 'name', 'short_description', 'description', 'gender', 'status']
admin.site.register(Product, ProductAdmin)

class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'product_id', 'productimage', 'alt_text']
    def productimage(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="80" height="80" '
                'style="object-fit:cover;border-radius:5px;" />',
                obj.image.url
            )
        return "No Image"
admin.site.register(ProductImage, ProductImageAdmin)

class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['id', 'product_id', 'color', 'size', 'mrp', 'selling_price', 'cost_price', 'stock_quantity', 'status']
admin.site.register(ProductVariant, ProductVariantAdmin)

class ProductInventoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'variant_id', 'quantity_change', 'operation', 'remarks']
admin.site.register(ProductInventory, ProductInventoryAdmin)

class WishlistAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'product_id']
admin.site.register(Wishlist, WishlistAdmin)

class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id']
admin.site.register(ShoppingCart, ShoppingCartAdmin)

class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart_id', 'product_variant_id', 'quantity', 'price', 'total']
admin.site.register(CartItem, CartItemAdmin)

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_number', 'user_id', 'address_id', 'subtotal', 'total_amount', 'payment_status', 'order_status']
    list_filter = ['order_status', 'payment_status']
admin.site.register(Order, OrderAdmin)

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_id', 'product_id', 'product_variant_id', 'product_name', 'total']
admin.site.register(OrderItem, OrderItemAdmin)

class paymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_id', 'payment_method', 'transaction_id', 'payment_status', 'amount', 'paid_at']
admin.site.register(Payment, paymentAdmin)

class PurchaseHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'order_id', 'product_variant_id', 'quantity', 'amount', 'purchase_date']
admin.site.register(PurchaseHistory, PurchaseHistoryAdmin)

class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_id', 'shipping_date', 'estimate_delivery', 'delivered_date', 'current_status']
admin.site.register(Shipment, ShipmentAdmin)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'product_id', 'user_id', 'rating', 'title', 'review', 'images', 'verified_purchase', 'created_at']
admin.site.register(Review, ReviewAdmin)

class TokenAdmin(admin.ModelAdmin):
    list_display = ['user_id','token']
admin.site.register(Token, TokenAdmin)

class DeliveryTokenAdmin(admin.ModelAdmin):
    list_display = ['deliveryPartner_id', 'token']
admin.site.register(DeliveryToken, DeliveryTokenAdmin)

class CardAdmin(admin.ModelAdmin):
    list_display = ['id', 'number', 'cvv', 'expire_date', 'balance', 'holder_name', 'is_active']
admin.site.register(Card, CardAdmin)

class DeliveryPartnerAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'mobile_number', 'email']
admin.site.register(DeliveryPartner, DeliveryPartnerAdmin)

class ShippingChargeAdmin(admin.ModelAdmin):
    list_display = ['id', 'area_id', 'city_id', 'state_id']
admin.site.register(ShippingCharge, ShippingChargeAdmin)