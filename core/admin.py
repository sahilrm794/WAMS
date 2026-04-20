from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Product, Part, Dealer, Supplier,
    DealerQuotation, DealerQuotationItem,
    SupplierQuotation, SupplierQuotationItem,
    DealerTransaction, DealerTransactionItem,
    SupplierTransaction, SupplierTransactionItem,
    StockLog,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'is_active']
    list_filter = ['role', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('WAMS', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('WAMS', {'fields': ('role', 'phone')}),
    )


class DealerQuotationItemInline(admin.TabularInline):
    model = DealerQuotationItem
    extra = 0


class SupplierQuotationItemInline(admin.TabularInline):
    model = SupplierQuotationItem
    extra = 0


class DealerTransactionItemInline(admin.TabularInline):
    model = DealerTransactionItem
    extra = 0


class SupplierTransactionItemInline(admin.TabularInline):
    model = SupplierTransactionItem
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'name', 'category', 'unit_price', 'stock_quantity', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'product_id']


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ['part_id', 'name', 'unit_cost', 'stock_quantity', 'supplier', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'part_id']


@admin.register(Dealer)
class DealerAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'contact_person', 'city', 'phone', 'is_active']
    search_fields = ['company_name', 'city']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'contact_person', 'city', 'phone', 'is_active']
    search_fields = ['company_name', 'city']


@admin.register(DealerQuotation)
class DealerQuotationAdmin(admin.ModelAdmin):
    list_display = ['quotation_number', 'dealer', 'status', 'total_amount', 'valid_until']
    inlines = [DealerQuotationItemInline]


@admin.register(SupplierQuotation)
class SupplierQuotationAdmin(admin.ModelAdmin):
    list_display = ['quotation_number', 'supplier', 'status', 'total_amount', 'valid_until']
    inlines = [SupplierQuotationItemInline]


@admin.register(DealerTransaction)
class DealerTransactionAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'dealer', 'total_amount', 'payment_status', 'transaction_date']
    inlines = [DealerTransactionItemInline]


@admin.register(SupplierTransaction)
class SupplierTransactionAdmin(admin.ModelAdmin):
    list_display = ['purchase_order_number', 'supplier', 'total_amount', 'payment_status', 'transaction_date']
    inlines = [SupplierTransactionItemInline]


@admin.register(StockLog)
class StockLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'product', 'part', 'change_type', 'quantity_change', 'quantity_after', 'reference']
    list_filter = ['change_type']
