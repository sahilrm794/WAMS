from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('dealer', 'Dealer'),
        ('supplier', 'Supplier'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='dealer')
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Supplier(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='supplier_profile')
    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name

    class Meta:
        ordering = ['company_name']


class Dealer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dealer_profile')
    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name

    class Meta:
        ordering = ['company_name']


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('mechanical', 'Mechanical'),
        ('chemical', 'Chemical'),
        ('textile', 'Textile'),
        ('other', 'Other'),
    ]
    product_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product_id} – {self.name}"

    @property
    def low_stock(self):
        return self.stock_quantity <= self.reorder_level

    class Meta:
        ordering = ['name']


class Part(models.Model):
    part_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='parts')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.part_id} – {self.name}"

    @property
    def low_stock(self):
        return self.stock_quantity <= self.reorder_level

    class Meta:
        ordering = ['name']


class DealerQuotation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    quotation_number = models.CharField(max_length=50, unique=True)
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE, related_name='quotations')
    issue_date = models.DateField(auto_now_add=True)
    valid_until = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='dealer_quotations_created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.quotation_number

    class Meta:
        ordering = ['-created_at']


class DealerQuotationItem(models.Model):
    quotation = models.ForeignKey(DealerQuotation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class SupplierQuotation(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('received', 'Received'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    quotation_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='quotations')
    issue_date = models.DateField(auto_now_add=True)
    valid_until = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='supplier_quotations_created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.quotation_number

    class Meta:
        ordering = ['-created_at']


class SupplierQuotationItem(models.Model):
    quotation = models.ForeignKey(SupplierQuotation, on_delete=models.CASCADE, related_name='items')
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.part.name} x {self.quantity}"


class DealerTransaction(models.Model):
    PAYMENT_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]
    invoice_number = models.CharField(max_length=50, unique=True)
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE, related_name='transactions')
    quotation = models.ForeignKey(DealerQuotation, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_date = models.DateField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='dealer_transactions_created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_number

    class Meta:
        ordering = ['-created_at']


class DealerTransactionItem(models.Model):
    transaction = models.ForeignKey(DealerTransaction, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class SupplierTransaction(models.Model):
    PAYMENT_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ]
    purchase_order_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='transactions')
    quotation = models.ForeignKey(SupplierQuotation, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_date = models.DateField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='supplier_transactions_created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.purchase_order_number

    class Meta:
        ordering = ['-created_at']


class SupplierTransactionItem(models.Model):
    transaction = models.ForeignKey(SupplierTransaction, on_delete=models.CASCADE, related_name='items')
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.part.name} x {self.quantity}"


class StockLog(models.Model):
    CHANGE_TYPE_CHOICES = [
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('adjustment', 'Adjustment'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name='stock_logs')
    part = models.ForeignKey(Part, on_delete=models.CASCADE, null=True, blank=True, related_name='stock_logs')
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPE_CHOICES)
    quantity_change = models.IntegerField()
    quantity_after = models.PositiveIntegerField()
    reference = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        item = self.product or self.part
        return f"{item} | {self.change_type} | {self.quantity_change:+d}"

    class Meta:
        ordering = ['-created_at']
