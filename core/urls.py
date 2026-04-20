from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password, name='change_password'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),

    # Parts
    path('parts/', views.part_list, name='part_list'),
    path('parts/add/', views.part_create, name='part_create'),
    path('parts/<int:pk>/edit/', views.part_update, name='part_update'),
    path('parts/<int:pk>/delete/', views.part_delete, name='part_delete'),

    # Dealers
    path('dealers/', views.dealer_list, name='dealer_list'),
    path('dealers/add/', views.dealer_create, name='dealer_create'),
    path('dealers/<int:pk>/edit/', views.dealer_update, name='dealer_update'),
    path('dealers/<int:pk>/delete/', views.dealer_delete, name='dealer_delete'),

    # Suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.supplier_update, name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),

    # Dealer Quotations
    path('quotations/dealer/', views.dealer_quotation_list, name='dealer_quotation_list'),
    path('quotations/dealer/create/', views.dealer_quotation_create, name='dealer_quotation_create'),
    path('quotations/dealer/<int:pk>/', views.dealer_quotation_detail, name='dealer_quotation_detail'),
    path('quotations/dealer/<int:pk>/status/', views.dealer_quotation_update_status, name='dealer_quotation_status'),

    # Supplier Quotations
    path('quotations/supplier/', views.supplier_quotation_list, name='supplier_quotation_list'),
    path('quotations/supplier/create/', views.supplier_quotation_create, name='supplier_quotation_create'),
    path('quotations/supplier/<int:pk>/', views.supplier_quotation_detail, name='supplier_quotation_detail'),
    path('quotations/supplier/<int:pk>/status/', views.supplier_quotation_update_status, name='supplier_quotation_status'),

    # Dealer Transactions
    path('transactions/sales/', views.dealer_transaction_list, name='dealer_transaction_list'),
    path('transactions/sales/create/', views.dealer_transaction_create, name='dealer_transaction_create'),
    path('transactions/sales/<int:pk>/', views.dealer_transaction_detail, name='dealer_transaction_detail'),
    path('transactions/sales/<int:pk>/payment/', views.dealer_transaction_update_payment, name='dealer_transaction_payment'),

    # Supplier Transactions
    path('transactions/purchases/', views.supplier_transaction_list, name='supplier_transaction_list'),
    path('transactions/purchases/create/', views.supplier_transaction_create, name='supplier_transaction_create'),
    path('transactions/purchases/<int:pk>/', views.supplier_transaction_detail, name='supplier_transaction_detail'),
    path('transactions/purchases/<int:pk>/payment/', views.supplier_transaction_update_payment, name='supplier_transaction_payment'),

    # Stock
    path('stock/', views.stock_overview, name='stock_overview'),
    path('stock/product/<int:pk>/adjust/', views.stock_adjust_product, name='stock_adjust_product'),
    path('stock/part/<int:pk>/adjust/', views.stock_adjust_part, name='stock_adjust_part'),

    # Reports
    path('reports/', views.reports, name='reports'),

    # Users
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/reset-password/', views.user_reset_password, name='user_reset_password'),
]
