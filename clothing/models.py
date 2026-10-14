from django.db import models

# Create your models here.

class User(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=254)
    dial_code = models.CharField(max_length=4)
    phone_number = models.BigIntegerField()
    password = models.CharField(max_length=16)
    gender_choice = ((1, 'Male'), (2, "Female"), (3, 'Other'))
    gender = models.IntegerField(choices=gender_choice, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='users/', default='users/default.jpg', null=True, blank=True)
    status = models.BooleanField(default=False, null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    mobile_verified = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    otp = models.IntegerField(null=True, blank=True)
    otp_verified = models.BooleanField(default=False)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.first_name

class AdminUser(models.Model):
    id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=50)
    profile_image = models.ImageField(upload_to="admin_profiles/", blank=True, null=True)
    email = models.EmailField(max_length=254)
    password = models.CharField(max_length=16)
    otp = models.CharField(max_length=128, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user_name
    
class AdminToken(models.Model):
    token_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(AdminUser, on_delete=models.CASCADE, null=True, blank=True)
    token = models.CharField(max_length=500, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField()

class Country(models.Model):
    country_id = models.AutoField(primary_key=True)
    country_name = models.CharField(max_length=50)

    def __str__(self):
        return self.country_name

class State(models.Model):
    state_id = models.AutoField(primary_key=True)
    state_name = models.CharField(max_length=50)
    country_id = models.ForeignKey(Country, on_delete=models.CASCADE)

    def __str__(self):
        return self.state_name

class City(models.Model):
    city_id = models.AutoField(primary_key=True)
    city_name = models.CharField(max_length=50)
    state_id = models.ForeignKey(State, on_delete=models.CASCADE)

    def __str__(self):
        return self.city_name

class Area(models.Model):
    area_id = models.AutoField(primary_key=True)
    area_name = models.CharField(max_length=50)
    city_id = models.ForeignKey(City, on_delete=models.CASCADE)

    def __str__(self):
        return self.area_name

class Address(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    dial_code = models.CharField(max_length=4)
    phone_number = models.BigIntegerField()
    address_line1 = models.TextField(max_length=255)
    address_line2 = models.TextField(max_length=255)
    country_id = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    state_id = models.ForeignKey(State, on_delete=models.CASCADE, null=True, blank=True)
    city_id = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True)
    area_id = models.ForeignKey(Area, on_delete=models.CASCADE, null=True, blank=True)
    postal_code = models.BigIntegerField()
    landmark = models.CharField(max_length=255)
    address_type_choice = ((1, 'Home'), (2, 'Work'), (3, 'Other'))
    address_type = models.IntegerField(choices=address_type_choice, default=1)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

class Category(models.Model):
    id = models.AutoField(primary_key=True)
    parent_category_id = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=255)
    image = models.ImageField(upload_to='category/', default='', null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    def __str__(self):
        return self.name

class Brand(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    logo = models.ImageField(upload_to='brandlogo/')
    description = models.TextField(max_length=255)
    website = models.URLField(max_length=200)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    category_id = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand_id = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    short_description = models.CharField(max_length=100)
    description = models.TextField(max_length=255)
    gender_choice = ((1, 'Female'), (2, 'Male'), (3, 'Others')) 
    gender = models.IntegerField(choices=gender_choice)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    id = models.AutoField(primary_key=True)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product/')
    alt_text = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_id.name

class ProductVariant(models.Model):
    id = models.AutoField(primary_key=True)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.CharField(max_length=25)
    color_code = models.CharField(max_length=7)
    size = models.CharField(max_length=10)
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField()
    minimum_stock = models.IntegerField()
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.product_id.name

class ProductInventory(models.Model):
    id = models.AutoField(primary_key=True)
    variant_id = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity_change = models.IntegerField()
    operation_choice = ((1, 'Add'), (2, 'Update'), (3, 'Delete'))
    operation = models.IntegerField(choices=operation_choice)
    remarks = models.TextField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

class Wishlist(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class ShoppingCart(models.Model):   
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user_id.first_name

class CartItem(models.Model):
    id = models.AutoField(primary_key=True)
    cart_id = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE)
    product_variant_id = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class Order(models.Model):
    id = models.AutoField(primary_key=True)
    order_number = models.CharField(unique=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    address_id = models.ForeignKey(Address, on_delete=models.CASCADE)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status_choices = ((1, 'Pending'), (2, 'Paid'), (3, 'Failed'), (4, 'Refunded'))
    payment_status = models.IntegerField(choices=payment_status_choices)
    order_status_choices = ((1, 'Pending'), (2, 'Processing'), (3, 'Delivered'), (4, 'Cancelled'))
    order_status = models.IntegerField(choices=order_status_choices)
    notes = models.TextField(max_length=200)
    placed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.order_number
    
class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_variant_id = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    color = models.CharField(max_length=7, default='#ffffff')
    size = models.CharField(max_length=10)
    quantity = models.IntegerField()
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.order_id.order_number
    
class Payment(models.Model):
    id = models.AutoField(primary_key=True)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment_method_choices = ((1, 'COD'), (2, 'Online'), (3, 'Card'))
    payment_method = models.IntegerField(choices=payment_method_choices)
    transaction_id = models.CharField(max_length=128, null=True, blank=True)
    payment_status_choices = ((1, 'Pending'), (2, 'Paid'), (3, 'Failed'), (4, 'Refunded'))
    payment_status = models.IntegerField(choices=payment_status_choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(null=True, blank=True)

class PurchaseHistory(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE)
    product_variant_id = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateField(auto_now_add=True)

class Review(models.Model):
    id = models.AutoField(primary_key=True)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    title = models.CharField(max_length=100)
    review = models.TextField(max_length=255)
    images = models.ImageField(upload_to='review/', null=True, blank=True)
    verified_purchase = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ReturnRequest(models.Model):
    id = models.AutoField(primary_key=True)
    order_item_id = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    reason = models.TextField(max_length=255)
    return_status_choices = ((1, 'Requested'), (2, 'Approved'), (3, 'Pickup'), (4, 'Received'), (5, 'Rejected'), (6, 'Completed'))
    return_status = models.IntegerField(choices=return_status_choices)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class Card(models.Model):
    id = models.AutoField(primary_key=True)
    number = models.CharField(max_length=16)
    cvv = models.CharField(max_length=3)
    expire_date = models.CharField(max_length=5)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    holder_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)       

class DeliveryPartner(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    mobile_number = models.IntegerField()
    email = models.EmailField(max_length=254)
    password = models.CharField(max_length=16)

    def __str__(self):
        return self.first_name

class Shipment(models.Model):
    id = models.AutoField(primary_key=True)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE)
    delivery_partner_id = models.ForeignKey(DeliveryPartner, on_delete=models.SET_NULL, null=True, blank=True)
    shipping_date = models.DateTimeField()
    estimate_delivery = models.DateTimeField()
    delivered_date = models.DateField(null=True, blank=True)
    current_status_choices = ((1, 'Pending'), (2, 'Picked Up'), (3, 'Out for Delivery'), (4, 'Delivered'), (5, 'Exception/Delayed'))
    current_status = models.IntegerField(choices=current_status_choices) 

class Token(models.Model):
    token_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField()

class DeliveryToken(models.Model):
    token_id = models.AutoField(primary_key=True)
    deliveryPartner_id = models.ForeignKey(DeliveryPartner, on_delete=models.CASCADE, null=True, blank=True)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField()

class ShippingCharge(models.Model):
    id = models.AutoField(primary_key=True)
    area_id = models.ForeignKey(Area, on_delete=models.CASCADE)
    city_id = models.ForeignKey(City, on_delete=models.CASCADE)
    state_id = models.ForeignKey(State, on_delete=models.CASCADE)