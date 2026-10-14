from django.urls import path
from .views import *

app_name = 'custom_admin'

urlpatterns = [

    path("admin-index/", view=index, name="adminIndex"),
    path("admin-profile/", view=profile, name="adminProfile"),
    path("admin-login/", view=admin_login, name="adminLogin"),
    path("admin-forgot-password/", view=admin_forgot_password, name="adminForgotPassword"),
    # path("products/", view=products, name="products"),
    path("add-new-product/", view=add_new_product, name="addNewProduct"),
    path("view-products/", view=view_products, name="viewProducts"),
    path("add-new-product-variant/", view=add_new_product_variant, name="addNewProductVariant"),
    path("edit-product/<int:product_id>/", view=edit_product_page, name="editProduct"),
    # path("categories/", view=categories, name="categories"),
    path("add-new-category/", view=add_new_category, name="addNewCategory"),
    path("view-category/", view=view_category, name="viewCategory"),
    path("edit-category/<int:category_id>/", view=edit_category_page, name="editCategory"),
    # path("stock-management/", view=stock_management, name="stockManagement"),
    path("add-new-stock/", view=add_new_stock, name="addNewStock"),
    path("view-current-stock/", view=view_current_stock, name="viewCurrentStock"),
    path("edit-stock/<int:variant_id>/", view=edit_stock_page, name="editStock"),
    # path("orders/", view=orders, name="orders"),
    path("current-orders/", view=current_orders, name="currentOrders"),
    path("in-delivery-orders/", view=in_delivery_orders, name="inDeliveryOrders"),
    path("order-history/", view=order_history, name="orderHistory"),
    path("order-details/<int:orderId>/", view=order_details_page, name="orderDetails"),
    # path("payments/", view=payments, name="payments"),
    path("total-payments/", view=total_payments, name="totalPayments"),

    # Product API URLs
    path("api/get-brands/", view=get_all_brands, name="getBrandsApi"),
    path("api/add-product/", view=add_product, name="addProductApi"),
    path("api/get-products/", view=get_all_products, name="getProductsApi"),
    path("api/get-single-product/<int:product_id>/", view=get_single_product, name="getSingleProductApi"),
    path("api/edit-product/<int:product_id>/", view=edit_product, name="editProductApi"),
    path("api/delete-product/", view=delete_product, name="deleteProductApi"),

    # Category API URLs
    path("api/add-category/", view=add_category, name="addCategoryApi"),
    path("api/get-categories/", view=get_all_categories, name="getCategoriesApi"),
    path("api/get-single-category/<int:category_id>/", view=get_single_category, name="getSingleCategoryApi"),
    path("api/edit-category/<int:category_id>/", view=edit_category, name="editCategoryApi"),
    path("api/delete-category/", view=delete_category, name="deleteCategoryApi"),

    # Order API URLs
    path("api/get-current-orders/", view=get_current_orders, name="getCurrentOrdersApi"),
    path("api/get-delivery-orders/", view=get_delivery_orders, name="getDeliveryOrdersApi"),
    path("api/get-orders-history/", view=get_orders_history, name="getOrdersHistoryApi"),
    path("api/get-orders-detail/<int:orderId>/", view=get_order_detail, name="getOrdersDetailApi"),
    path("api/change-order-status/", view=change_order_status, name="changeOrderStatusApi"),

    # STOCK APIs
    path("api/get-stock-products/", view=get_stock_products, name="getStockProducts"),
    path("api/get-product-stock-variants/", view=get_product_stock_variants, name="getProductStockVariants"),
    path("api/add-stock/", view=add_stock, name="addStock"),
    path("api/add-product-variant/", view=add_product_variant, name="createStockVariant"),
    path("api/get-current-stock/", view=get_current_stock, name="getCurrentStock"),
    path("api/get-stock-detail/", view=get_stock_detail, name="getStockDetail"),
    path("api/update-stock/", view=update_stock, name="updateStock"),
    path("api/delete-stock/", view=delete_stock, name="deleteStock"),

    # PAYMENT API
    path("api/get-total-payments/", view=get_total_payments, name="getTotalPayments"),

    path("api/get-admin-dashboard-data/", view=get_admin_dashboard_data, name="adminDashboardData"),
    path("api/admin-login-api/", view=admin_login_api, name="adminLoginApi"),
    path("api/admin-profile-api/", view=admin_profile_api, name="adminProfileApi"),
    path("api/admin-update-profile-api/", view=admin_update_profile_api, name="adminUpdateProfileApi"),
    path("api/admin-logout-api/", view=admin_logout_api, name="adminLogoutApi"),
    path("api/admin-forgot-password-api/", view=admin_forgot_password_api, name="adminForgotPasswordApi"),
    path("api/admin-reset-password-api/", view=admin_reset_password_api, name="adminResetPasswordApi"),

    # GLOBAL PAGE SEARCH API
    path("api/global-page-search/", view=global_page_search, name="globalPageSearchApi"),
]