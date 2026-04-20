from django import forms
from django.forms import inlineformset_factory
from .models import (
    User, Product, Part, Dealer, Supplier,
    DealerQuotation, DealerQuotationItem,
    SupplierQuotation, SupplierQuotationItem,
    DealerTransaction, DealerTransactionItem,
    SupplierTransaction, SupplierTransactionItem,
)

FORM_CONTROL = {'class': 'form-control'}
FORM_SELECT = {'class': 'form-select'}
FORM_CHECK = {'class': 'form-check-input'}


# ─── Custom widgets with auto-price data attributes ──────────────────────────

class ProductSelectWidget(forms.Select):
    """Adds data-price / data-stock to each <option> so JS can auto-fill unit price."""
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None, **kwargs):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        pk = getattr(value, 'value', value)
        if pk:
            try:
                product = Product.objects.get(pk=int(pk))
                option['attrs']['data-price'] = str(product.unit_price)
                option['attrs']['data-stock'] = str(product.stock_quantity)
            except (Product.DoesNotExist, ValueError, TypeError):
                pass
        return option


class PartSelectWidget(forms.Select):
    """Adds data-price to each <option> so JS can auto-fill unit cost."""
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None, **kwargs):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        pk = getattr(value, 'value', value)
        if pk:
            try:
                part = Part.objects.get(pk=int(pk))
                option['attrs']['data-price'] = str(part.unit_cost)
            except (Part.DoesNotExist, ValueError, TypeError):
                pass
        return option


# ─── Auth ────────────────────────────────────────────────────────────────────

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={**FORM_CONTROL, 'autofocus': True, 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={**FORM_CONTROL, 'placeholder': 'Password'}))


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(label='Current Password', widget=forms.PasswordInput(attrs=FORM_CONTROL))
    new_password1 = forms.CharField(label='New Password', widget=forms.PasswordInput(attrs=FORM_CONTROL))
    new_password2 = forms.CharField(label='Confirm New Password', widget=forms.PasswordInput(attrs=FORM_CONTROL))

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('New passwords do not match.')
        if p1 and len(p1) < 8:
            raise forms.ValidationError('Password must be at least 8 characters.')
        return cleaned_data


# ─── User Management ─────────────────────────────────────────────────────────

class UserCreateForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs=FORM_CONTROL))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs=FORM_CONTROL))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone']
        widgets = {
            'username': forms.TextInput(attrs=FORM_CONTROL),
            'first_name': forms.TextInput(attrs=FORM_CONTROL),
            'last_name': forms.TextInput(attrs=FORM_CONTROL),
            'email': forms.EmailInput(attrs=FORM_CONTROL),
            'role': forms.Select(attrs=FORM_SELECT),
            'phone': forms.TextInput(attrs=FORM_CONTROL),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class DealerUserCreateForm(UserCreateForm):
    """UserCreateForm with role hidden — always creates a dealer user."""
    class Meta(UserCreateForm.Meta):
        fields = ['username', 'first_name', 'last_name', 'email', 'phone']


class SupplierUserCreateForm(UserCreateForm):
    """UserCreateForm with role hidden — always creates a supplier user."""
    class Meta(UserCreateForm.Meta):
        fields = ['username', 'first_name', 'last_name', 'email', 'phone']


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'phone', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs=FORM_CONTROL),
            'last_name': forms.TextInput(attrs=FORM_CONTROL),
            'email': forms.EmailInput(attrs=FORM_CONTROL),
            'role': forms.Select(attrs=FORM_SELECT),
            'phone': forms.TextInput(attrs=FORM_CONTROL),
            'is_active': forms.CheckboxInput(attrs=FORM_CHECK),
        }


# ─── Product / Part ───────────────────────────────────────────────────────────

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_id', 'name', 'category', 'description', 'unit_price', 'stock_quantity', 'reorder_level', 'is_active']
        widgets = {
            'product_id': forms.TextInput(attrs=FORM_CONTROL),
            'name': forms.TextInput(attrs=FORM_CONTROL),
            'category': forms.Select(attrs=FORM_SELECT),
            'description': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 3}),
            'unit_price': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs=FORM_CONTROL),
            'reorder_level': forms.NumberInput(attrs=FORM_CONTROL),
            'is_active': forms.CheckboxInput(attrs=FORM_CHECK),
        }


class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ['part_id', 'name', 'description', 'unit_cost', 'stock_quantity', 'reorder_level', 'supplier', 'is_active']
        widgets = {
            'part_id': forms.TextInput(attrs=FORM_CONTROL),
            'name': forms.TextInput(attrs=FORM_CONTROL),
            'description': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 3}),
            'unit_cost': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs=FORM_CONTROL),
            'reorder_level': forms.NumberInput(attrs=FORM_CONTROL),
            'supplier': forms.Select(attrs=FORM_SELECT),
            'is_active': forms.CheckboxInput(attrs=FORM_CHECK),
        }


# ─── Dealer / Supplier Profiles ───────────────────────────────────────────────

class DealerForm(forms.ModelForm):
    class Meta:
        model = Dealer
        fields = ['company_name', 'contact_person', 'email', 'phone', 'address', 'city', 'credit_limit', 'is_active']
        widgets = {
            'company_name': forms.TextInput(attrs=FORM_CONTROL),
            'contact_person': forms.TextInput(attrs=FORM_CONTROL),
            'email': forms.EmailInput(attrs=FORM_CONTROL),
            'phone': forms.TextInput(attrs=FORM_CONTROL),
            'address': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2}),
            'city': forms.TextInput(attrs=FORM_CONTROL),
            'credit_limit': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs=FORM_CHECK),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['company_name', 'contact_person', 'email', 'phone', 'address', 'city', 'is_active']
        widgets = {
            'company_name': forms.TextInput(attrs=FORM_CONTROL),
            'contact_person': forms.TextInput(attrs=FORM_CONTROL),
            'email': forms.EmailInput(attrs=FORM_CONTROL),
            'phone': forms.TextInput(attrs=FORM_CONTROL),
            'address': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2}),
            'city': forms.TextInput(attrs=FORM_CONTROL),
            'is_active': forms.CheckboxInput(attrs=FORM_CHECK),
        }


# ─── Dealer Quotations ────────────────────────────────────────────────────────

class DealerQuotationForm(forms.ModelForm):
    """Used by admin to create a quotation for a dealer."""
    class Meta:
        model = DealerQuotation
        fields = ['dealer', 'valid_until', 'status', 'notes']
        widgets = {
            'dealer': forms.Select(attrs=FORM_SELECT),
            'valid_until': forms.DateInput(attrs={**FORM_CONTROL, 'type': 'date'}),
            'status': forms.Select(attrs=FORM_SELECT),
            'notes': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2}),
        }


class DealerQuotationRequestForm(forms.ModelForm):
    """Used by dealers to submit their own purchase requests."""
    class Meta:
        model = DealerQuotation
        fields = ['valid_until', 'notes']
        labels = {
            'valid_until': 'Required By Date',
            'notes': 'Additional Notes / Special Requirements',
        }
        widgets = {
            'valid_until': forms.DateInput(attrs={**FORM_CONTROL, 'type': 'date'}),
            'notes': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 3, 'placeholder': 'e.g. urgent delivery needed, specific batch requirements…'}),
        }


class DealerQuotationItemForm(forms.ModelForm):
    class Meta:
        model = DealerQuotationItem
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': ProductSelectWidget(attrs={**FORM_SELECT, 'class': 'form-select product-select'}),
            'quantity': forms.NumberInput(attrs={**FORM_CONTROL, 'min': 1, 'class': 'form-control qty-input'}),
            'unit_price': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.01', 'class': 'form-control price-input'}),
        }


class DealerQuotationItemRequestForm(forms.ModelForm):
    """Line item for dealer purchase requests — price is their expected/budgeted price."""
    class Meta:
        model = DealerQuotationItem
        fields = ['product', 'quantity', 'unit_price']
        labels = {
            'unit_price': 'Budget Price per Unit (₹)',
        }
        widgets = {
            'product': ProductSelectWidget(attrs={**FORM_SELECT, 'class': 'form-select product-select'}),
            'quantity': forms.NumberInput(attrs={**FORM_CONTROL, 'min': 1, 'class': 'form-control qty-input'}),
            'unit_price': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.01', 'class': 'form-control price-input', 'placeholder': 'Auto-filled from catalogue'}),
        }


DealerQuotationItemFormSet = inlineformset_factory(
    DealerQuotation, DealerQuotationItem,
    form=DealerQuotationItemForm,
    extra=1, can_delete=True, min_num=1, validate_min=True,
)

DealerQuotationRequestFormSet = inlineformset_factory(
    DealerQuotation, DealerQuotationItem,
    form=DealerQuotationItemRequestForm,
    extra=1, can_delete=True, min_num=1, validate_min=True,
)


# ─── Supplier Quotations ──────────────────────────────────────────────────────

class SupplierQuotationForm(forms.ModelForm):
    """Used by admin to request a quotation from a supplier."""
    class Meta:
        model = SupplierQuotation
        fields = ['supplier', 'valid_until', 'status', 'notes']
        widgets = {
            'supplier': forms.Select(attrs=FORM_SELECT),
            'valid_until': forms.DateInput(attrs={**FORM_CONTROL, 'type': 'date'}),
            'status': forms.Select(attrs=FORM_SELECT),
            'notes': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2}),
        }


class SupplierQuotationOfferForm(forms.ModelForm):
    """Used by suppliers to submit their own price offers."""
    class Meta:
        model = SupplierQuotation
        fields = ['valid_until', 'notes']
        labels = {
            'valid_until': 'Offer Valid Until',
            'notes': 'Terms, Delivery Details & Notes',
        }
        widgets = {
            'valid_until': forms.DateInput(attrs={**FORM_CONTROL, 'type': 'date'}),
            'notes': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 3, 'placeholder': 'e.g. delivery timeline, payment terms, quality certifications…'}),
        }


class SupplierQuotationItemForm(forms.ModelForm):
    class Meta:
        model = SupplierQuotationItem
        fields = ['part', 'quantity', 'unit_cost']
        widgets = {
            'part': PartSelectWidget(attrs={**FORM_SELECT, 'class': 'form-select part-select'}),
            'quantity': forms.NumberInput(attrs={**FORM_CONTROL, 'min': 1, 'class': 'form-control qty-input'}),
            'unit_cost': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.01', 'class': 'form-control price-input'}),
        }


class SupplierQuotationOfferItemForm(forms.ModelForm):
    """Line item for supplier offers — they set the price they're offering."""
    class Meta:
        model = SupplierQuotationItem
        fields = ['part', 'quantity', 'unit_cost']
        labels = {
            'unit_cost': 'Your Offered Price per Unit (₹)',
        }
        widgets = {
            'part': PartSelectWidget(attrs={**FORM_SELECT, 'class': 'form-select part-select'}),
            'quantity': forms.NumberInput(attrs={**FORM_CONTROL, 'min': 1, 'class': 'form-control qty-input', 'placeholder': 'Available quantity'}),
            'unit_cost': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.01', 'class': 'form-control price-input', 'placeholder': 'Your offered price'}),
        }


SupplierQuotationItemFormSet = inlineformset_factory(
    SupplierQuotation, SupplierQuotationItem,
    form=SupplierQuotationItemForm,
    extra=1, can_delete=True, min_num=1, validate_min=True,
)

SupplierQuotationOfferFormSet = inlineformset_factory(
    SupplierQuotation, SupplierQuotationItem,
    form=SupplierQuotationOfferItemForm,
    extra=1, can_delete=True, min_num=1, validate_min=True,
)


# ─── Dealer Transactions ──────────────────────────────────────────────────────

class DealerTransactionForm(forms.ModelForm):
    class Meta:
        model = DealerTransaction
        fields = ['dealer', 'quotation', 'payment_status', 'notes']
        widgets = {
            'dealer': forms.Select(attrs=FORM_SELECT),
            'quotation': forms.Select(attrs=FORM_SELECT),
            'payment_status': forms.Select(attrs=FORM_SELECT),
            'notes': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quotation'].required = False
        self.fields['quotation'].queryset = DealerQuotation.objects.filter(status='accepted')


class DealerTransactionItemForm(forms.ModelForm):
    class Meta:
        model = DealerTransactionItem
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': ProductSelectWidget(attrs={**FORM_SELECT, 'class': 'form-select product-select'}),
            'quantity': forms.NumberInput(attrs={**FORM_CONTROL, 'min': 1, 'class': 'form-control qty-input'}),
            'unit_price': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.01', 'class': 'form-control price-input'}),
        }


DealerTransactionItemFormSet = inlineformset_factory(
    DealerTransaction, DealerTransactionItem,
    form=DealerTransactionItemForm,
    extra=1, can_delete=True, min_num=1, validate_min=True,
)


# ─── Supplier Transactions ────────────────────────────────────────────────────

class SupplierTransactionForm(forms.ModelForm):
    class Meta:
        model = SupplierTransaction
        fields = ['supplier', 'quotation', 'payment_status', 'notes']
        widgets = {
            'supplier': forms.Select(attrs=FORM_SELECT),
            'quotation': forms.Select(attrs=FORM_SELECT),
            'payment_status': forms.Select(attrs=FORM_SELECT),
            'notes': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quotation'].required = False
        self.fields['quotation'].queryset = SupplierQuotation.objects.filter(status='accepted')


class SupplierTransactionItemForm(forms.ModelForm):
    class Meta:
        model = SupplierTransactionItem
        fields = ['part', 'quantity', 'unit_cost']
        widgets = {
            'part': PartSelectWidget(attrs={**FORM_SELECT, 'class': 'form-select part-select'}),
            'quantity': forms.NumberInput(attrs={**FORM_CONTROL, 'min': 1, 'class': 'form-control qty-input'}),
            'unit_cost': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.01', 'class': 'form-control price-input'}),
        }


SupplierTransactionItemFormSet = inlineformset_factory(
    SupplierTransaction, SupplierTransactionItem,
    form=SupplierTransactionItemForm,
    extra=1, can_delete=True, min_num=1, validate_min=True,
)


# ─── Stock ────────────────────────────────────────────────────────────────────

class StockAdjustForm(forms.Form):
    quantity_change = forms.IntegerField(
        label='Quantity Change (+/-)',
        widget=forms.NumberInput(attrs=FORM_CONTROL),
        help_text='Positive to add stock, negative to reduce.',
    )
    reason = forms.CharField(
        widget=forms.TextInput(attrs=FORM_CONTROL),
        max_length=200,
    )
