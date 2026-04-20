from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction as db_transaction
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, timedelta

from .models import (
    User, Product, Part, Dealer, Supplier,
    DealerQuotation, DealerQuotationItem,
    SupplierQuotation, SupplierQuotationItem,
    DealerTransaction, DealerTransactionItem,
    SupplierTransaction, SupplierTransactionItem,
    StockLog,
)
from .forms import (
    LoginForm, ChangePasswordForm,
    UserCreateForm, UserEditForm,
    DealerUserCreateForm, SupplierUserCreateForm,
    ProductForm, PartForm,
    DealerForm, SupplierForm,
    DealerQuotationForm, DealerQuotationItemFormSet,
    DealerQuotationRequestForm, DealerQuotationRequestFormSet,
    SupplierQuotationForm, SupplierQuotationItemFormSet,
    SupplierQuotationOfferForm, SupplierQuotationOfferFormSet,
    DealerTransactionForm, DealerTransactionItemFormSet,
    SupplierTransactionForm, SupplierTransactionItemFormSet,
    StockAdjustForm,
)
from .decorators import admin_required


# ─── Helpers ────────────────────────────────────────────────────────────────

def _next_number(prefix, model, field):
    from django.db.models import Max
    today = date.today().strftime('%Y%m%d')
    pattern = f"{prefix}-{today}-"
    last = model.objects.filter(**{f"{field}__startswith": pattern}).aggregate(m=Max(field))['m']
    if last:
        seq = int(last.split('-')[-1]) + 1
    else:
        seq = 1
    return f"{prefix}-{today}-{seq:04d}"


def generate_dq_number():
    return _next_number('DQ', DealerQuotation, 'quotation_number')


def generate_sq_number():
    return _next_number('SQ', SupplierQuotation, 'quotation_number')


def generate_inv_number():
    return _next_number('INV', DealerTransaction, 'invoice_number')


def generate_po_number():
    return _next_number('PO', SupplierTransaction, 'purchase_order_number')


def paginate(request, qs, per_page=20):
    paginator = Paginator(qs, per_page)
    page = request.GET.get('page', 1)
    return paginator.get_page(page)


# ─── Auth ────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        messages.error(request, 'Invalid username or password.')
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def change_password(request):
    form = ChangePasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if not request.user.check_password(form.cleaned_data['old_password']):
            messages.error(request, 'Current password is incorrect.')
        else:
            request.user.set_password(form.cleaned_data['new_password1'])
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully.')
            return redirect('dashboard')
    return render(request, 'core/change_password.html', {'form': form})


# ─── Dashboard ───────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    ctx = {}
    if request.user.role == 'admin':
        ctx['product_count'] = Product.objects.filter(is_active=True).count()
        ctx['part_count'] = Part.objects.filter(is_active=True).count()
        ctx['dealer_count'] = Dealer.objects.filter(is_active=True).count()
        ctx['supplier_count'] = Supplier.objects.filter(is_active=True).count()
        ctx['pending_dq'] = DealerQuotation.objects.filter(status='sent').count()
        ctx['pending_sq'] = SupplierQuotation.objects.filter(status='requested').count()
        ctx['low_stock_products'] = Product.objects.filter(is_active=True).extra(
            where=['stock_quantity <= reorder_level']
        ).count()
        ctx['low_stock_parts'] = Part.objects.filter(is_active=True).extra(
            where=['stock_quantity <= reorder_level']
        ).count()
        ctx['recent_sales'] = DealerTransaction.objects.select_related('dealer')[:5]
        ctx['recent_purchases'] = SupplierTransaction.objects.select_related('supplier')[:5]
        ctx['monthly_sales'] = DealerTransaction.objects.filter(
            transaction_date__month=date.today().month,
            transaction_date__year=date.today().year,
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        ctx['monthly_purchases'] = SupplierTransaction.objects.filter(
            transaction_date__month=date.today().month,
            transaction_date__year=date.today().year,
        ).aggregate(total=Sum('total_amount'))['total'] or 0

    elif request.user.role == 'dealer':
        try:
            dealer = request.user.dealer_profile
            ctx['dealer'] = dealer
            ctx['quotation_count'] = dealer.quotations.count()
            ctx['transaction_count'] = dealer.transactions.count()
            ctx['pending_quotations'] = dealer.quotations.filter(status__in=['draft', 'sent']).count()
            ctx['pending_payments'] = dealer.transactions.filter(payment_status='pending').count()
            ctx['recent_quotations'] = dealer.quotations.select_related('dealer')[:5]
            ctx['recent_transactions'] = dealer.transactions.select_related('dealer')[:5]
        except Dealer.DoesNotExist:
            ctx['no_profile'] = True

    elif request.user.role == 'supplier':
        try:
            supplier = request.user.supplier_profile
            ctx['supplier'] = supplier
            ctx['quotation_count'] = supplier.quotations.count()
            ctx['transaction_count'] = supplier.transactions.count()
            ctx['pending_quotations'] = supplier.quotations.filter(status='requested').count()
            ctx['recent_quotations'] = supplier.quotations.select_related('supplier')[:5]
            ctx['recent_transactions'] = supplier.transactions.select_related('supplier')[:5]
        except Supplier.DoesNotExist:
            ctx['no_profile'] = True

    return render(request, 'core/dashboard.html', ctx)


# ─── Products ────────────────────────────────────────────────────────────────

@login_required
def product_list(request):
    qs = Product.objects.all()
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(product_id__icontains=q) | Q(category__icontains=q))
    cat = request.GET.get('category', '')
    if cat:
        qs = qs.filter(category=cat)
    page = paginate(request, qs)
    return render(request, 'core/products/list.html', {
        'page_obj': page, 'q': q, 'category': cat,
        'categories': Product.CATEGORY_CHOICES,
    })


@login_required
@admin_required
def product_create(request):
    form = ProductForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Product created.')
        return redirect('product_list')
    return render(request, 'core/products/form.html', {'form': form, 'title': 'Add Product'})


@login_required
@admin_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Product updated.')
        return redirect('product_list')
    return render(request, 'core/products/form.html', {'form': form, 'title': 'Edit Product', 'object': product})


@login_required
@admin_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        if DealerTransactionItem.objects.filter(product=product).exists():
            product.is_active = False
            product.save()
            messages.warning(request, 'Product has linked transactions; marked as inactive instead.')
        else:
            product.delete()
            messages.success(request, 'Product deleted.')
        return redirect('product_list')
    return render(request, 'core/confirm_delete.html', {'object': product, 'object_name': product.name})


# ─── Parts ───────────────────────────────────────────────────────────────────

@login_required
def part_list(request):
    qs = Part.objects.select_related('supplier').all()
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(part_id__icontains=q))
    page = paginate(request, qs)
    return render(request, 'core/parts/list.html', {'page_obj': page, 'q': q})


@login_required
@admin_required
def part_create(request):
    form = PartForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Part created.')
        return redirect('part_list')
    return render(request, 'core/parts/form.html', {'form': form, 'title': 'Add Part'})


@login_required
@admin_required
def part_update(request, pk):
    part = get_object_or_404(Part, pk=pk)
    form = PartForm(request.POST or None, instance=part)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Part updated.')
        return redirect('part_list')
    return render(request, 'core/parts/form.html', {'form': form, 'title': 'Edit Part', 'object': part})


@login_required
@admin_required
def part_delete(request, pk):
    part = get_object_or_404(Part, pk=pk)
    if request.method == 'POST':
        if SupplierTransactionItem.objects.filter(part=part).exists():
            part.is_active = False
            part.save()
            messages.warning(request, 'Part has linked transactions; marked as inactive instead.')
        else:
            part.delete()
            messages.success(request, 'Part deleted.')
        return redirect('part_list')
    return render(request, 'core/confirm_delete.html', {'object': part, 'object_name': part.name})


# ─── Dealers ─────────────────────────────────────────────────────────────────

@login_required
@admin_required
def dealer_list(request):
    qs = Dealer.objects.select_related('user').all()
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(company_name__icontains=q) | Q(city__icontains=q))
    page = paginate(request, qs)
    return render(request, 'core/dealers/list.html', {'page_obj': page, 'q': q})


@login_required
@admin_required
def dealer_create(request):
    dealer_form = DealerForm(request.POST or None)
    user_form = DealerUserCreateForm(request.POST or None)
    if request.method == 'POST':
        if dealer_form.is_valid() and user_form.is_valid():
            user = user_form.save(commit=False)
            user.role = 'dealer'
            user.save()
            dealer = dealer_form.save(commit=False)
            dealer.user = user
            dealer.save()
            messages.success(request, f'Dealer "{dealer.company_name}" created. Login: username="{user.username}", password as set.')
            return redirect('dealer_list')
    return render(request, 'core/dealers/form.html', {
        'dealer_form': dealer_form, 'user_form': user_form, 'title': 'Add Dealer'
    })


@login_required
@admin_required
def dealer_update(request, pk):
    dealer = get_object_or_404(Dealer, pk=pk)
    form = DealerForm(request.POST or None, instance=dealer)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Dealer updated.')
        return redirect('dealer_list')
    return render(request, 'core/dealers/edit_form.html', {'form': form, 'dealer': dealer})


@login_required
@admin_required
def dealer_delete(request, pk):
    dealer = get_object_or_404(Dealer, pk=pk)
    if request.method == 'POST':
        dealer.is_active = False
        dealer.save()
        dealer.user.is_active = False
        dealer.user.save()
        messages.success(request, 'Dealer deactivated.')
        return redirect('dealer_list')
    return render(request, 'core/confirm_delete.html', {'object': dealer, 'object_name': dealer.company_name, 'action': 'deactivate'})


# ─── Suppliers ───────────────────────────────────────────────────────────────

@login_required
@admin_required
def supplier_list(request):
    qs = Supplier.objects.select_related('user').all()
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(company_name__icontains=q) | Q(city__icontains=q))
    page = paginate(request, qs)
    return render(request, 'core/suppliers/list.html', {'page_obj': page, 'q': q})


@login_required
@admin_required
def supplier_create(request):
    supplier_form = SupplierForm(request.POST or None)
    user_form = SupplierUserCreateForm(request.POST or None)
    if request.method == 'POST':
        if supplier_form.is_valid() and user_form.is_valid():
            user = user_form.save(commit=False)
            user.role = 'supplier'
            user.save()
            supplier = supplier_form.save(commit=False)
            supplier.user = user
            supplier.save()
            messages.success(request, f'Supplier "{supplier.company_name}" created. Login: username="{user.username}", password as set.')
            return redirect('supplier_list')
    return render(request, 'core/suppliers/form.html', {
        'supplier_form': supplier_form, 'user_form': user_form, 'title': 'Add Supplier'
    })


@login_required
@admin_required
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    form = SupplierForm(request.POST or None, instance=supplier)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Supplier updated.')
        return redirect('supplier_list')
    return render(request, 'core/suppliers/edit_form.html', {'form': form, 'supplier': supplier})


@login_required
@admin_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.is_active = False
        supplier.save()
        supplier.user.is_active = False
        supplier.user.save()
        messages.success(request, 'Supplier deactivated.')
        return redirect('supplier_list')
    return render(request, 'core/confirm_delete.html', {'object': supplier, 'object_name': supplier.company_name, 'action': 'deactivate'})


# ─── Dealer Quotations ───────────────────────────────────────────────────────

@login_required
def dealer_quotation_list(request):
    if request.user.role == 'dealer':
        try:
            qs = request.user.dealer_profile.quotations.all()
        except Dealer.DoesNotExist:
            qs = DealerQuotation.objects.none()
    else:
        qs = DealerQuotation.objects.select_related('dealer').all()
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(quotation_number__icontains=q) | Q(dealer__company_name__icontains=q))
    page = paginate(request, qs)
    return render(request, 'core/quotations/dealer_list.html', {
        'page_obj': page, 'q': q, 'status': status,
        'status_choices': DealerQuotation.STATUS_CHOICES,
    })


@login_required
def dealer_quotation_create(request):
    if request.user.role == 'dealer':
        try:
            dealer_profile = request.user.dealer_profile
        except Dealer.DoesNotExist:
            messages.error(request, 'Your dealer profile is not set up yet. Contact the admin.')
            return redirect('dashboard')

        form = DealerQuotationRequestForm(request.POST or None)
        formset = DealerQuotationRequestFormSet(request.POST or None)
        if request.method == 'POST' and form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                quotation = form.save(commit=False)
                quotation.quotation_number = generate_dq_number()
                quotation.dealer = dealer_profile
                quotation.status = 'sent'
                quotation.created_by = request.user
                quotation.save()
                items = formset.save(commit=False)
                total = 0
                for item in items:
                    item.quotation = quotation
                    item.subtotal = item.quantity * item.unit_price
                    item.save()
                    total += item.subtotal
                for obj in formset.deleted_objects:
                    obj.delete()
                quotation.total_amount = total
                quotation.save()
            messages.success(request, f'Purchase request {quotation.quotation_number} submitted to admin.')
            return redirect('dealer_quotation_detail', pk=quotation.pk)
        return render(request, 'core/quotations/dealer_request_form.html', {
            'form': form, 'formset': formset, 'title': 'Submit Purchase Request',
        })

    elif request.user.role == 'admin':
        form = DealerQuotationForm(request.POST or None)
        formset = DealerQuotationItemFormSet(request.POST or None)
        if request.method == 'POST' and form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                quotation = form.save(commit=False)
                quotation.quotation_number = generate_dq_number()
                quotation.created_by = request.user
                quotation.save()
                items = formset.save(commit=False)
                total = 0
                for item in items:
                    item.quotation = quotation
                    item.subtotal = item.quantity * item.unit_price
                    item.save()
                    total += item.subtotal
                for obj in formset.deleted_objects:
                    obj.delete()
                quotation.total_amount = total
                quotation.save()
            messages.success(request, f'Quotation {quotation.quotation_number} created.')
            return redirect('dealer_quotation_detail', pk=quotation.pk)
        return render(request, 'core/quotations/dealer_form.html', {
            'form': form, 'formset': formset, 'title': 'Create Dealer Quotation',
        })

    messages.error(request, 'Access denied.')
    return redirect('dashboard')


@login_required
def dealer_quotation_detail(request, pk):
    if request.user.role == 'dealer':
        try:
            quotation = get_object_or_404(DealerQuotation, pk=pk, dealer=request.user.dealer_profile)
        except Dealer.DoesNotExist:
            messages.error(request, 'Profile not found.')
            return redirect('dashboard')
    else:
        quotation = get_object_or_404(DealerQuotation, pk=pk)
    return render(request, 'core/quotations/dealer_detail.html', {'quotation': quotation})


@login_required
@admin_required
def dealer_quotation_update_status(request, pk):
    quotation = get_object_or_404(DealerQuotation, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(DealerQuotation.STATUS_CHOICES):
            quotation.status = new_status
            quotation.save()
            messages.success(request, f'Status updated to {quotation.get_status_display()}.')
    return redirect('dealer_quotation_detail', pk=pk)


# ─── Supplier Quotations ─────────────────────────────────────────────────────

@login_required
def supplier_quotation_list(request):
    if request.user.role == 'supplier':
        try:
            qs = request.user.supplier_profile.quotations.all()
        except Supplier.DoesNotExist:
            qs = SupplierQuotation.objects.none()
    else:
        qs = SupplierQuotation.objects.select_related('supplier').all()
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(quotation_number__icontains=q) | Q(supplier__company_name__icontains=q))
    page = paginate(request, qs)
    return render(request, 'core/quotations/supplier_list.html', {
        'page_obj': page, 'q': q, 'status': status,
        'status_choices': SupplierQuotation.STATUS_CHOICES,
    })


@login_required
def supplier_quotation_create(request):
    if request.user.role == 'supplier':
        try:
            supplier_profile = request.user.supplier_profile
        except Supplier.DoesNotExist:
            messages.error(request, 'Your supplier profile is not set up yet. Contact the admin.')
            return redirect('dashboard')

        form = SupplierQuotationOfferForm(request.POST or None)
        formset = SupplierQuotationOfferFormSet(request.POST or None)
        if request.method == 'POST' and form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                quotation = form.save(commit=False)
                quotation.quotation_number = generate_sq_number()
                quotation.supplier = supplier_profile
                quotation.status = 'received'
                quotation.created_by = request.user
                quotation.save()
                items = formset.save(commit=False)
                total = 0
                for item in items:
                    item.quotation = quotation
                    item.subtotal = item.quantity * item.unit_cost
                    item.save()
                    total += item.subtotal
                for obj in formset.deleted_objects:
                    obj.delete()
                quotation.total_amount = total
                quotation.save()
            messages.success(request, f'Quotation {quotation.quotation_number} submitted successfully.')
            return redirect('supplier_quotation_detail', pk=quotation.pk)
        return render(request, 'core/quotations/supplier_offer_form.html', {
            'form': form, 'formset': formset, 'title': 'Submit Price Quotation',
        })

    elif request.user.role == 'admin':
        form = SupplierQuotationForm(request.POST or None)
        formset = SupplierQuotationItemFormSet(request.POST or None)
        if request.method == 'POST' and form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                quotation = form.save(commit=False)
                quotation.quotation_number = generate_sq_number()
                quotation.created_by = request.user
                quotation.save()
                items = formset.save(commit=False)
                total = 0
                for item in items:
                    item.quotation = quotation
                    item.subtotal = item.quantity * item.unit_cost
                    item.save()
                    total += item.subtotal
                for obj in formset.deleted_objects:
                    obj.delete()
                quotation.total_amount = total
                quotation.save()
            messages.success(request, f'Quotation {quotation.quotation_number} created.')
            return redirect('supplier_quotation_detail', pk=quotation.pk)
        return render(request, 'core/quotations/supplier_form.html', {
            'form': form, 'formset': formset, 'title': 'Create Supplier Quotation',
        })

    messages.error(request, 'Access denied.')
    return redirect('dashboard')


@login_required
def supplier_quotation_detail(request, pk):
    if request.user.role == 'supplier':
        try:
            quotation = get_object_or_404(SupplierQuotation, pk=pk, supplier=request.user.supplier_profile)
        except Supplier.DoesNotExist:
            messages.error(request, 'Profile not found.')
            return redirect('dashboard')
    else:
        quotation = get_object_or_404(SupplierQuotation, pk=pk)
    return render(request, 'core/quotations/supplier_detail.html', {'quotation': quotation})


@login_required
@admin_required
def supplier_quotation_update_status(request, pk):
    quotation = get_object_or_404(SupplierQuotation, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(SupplierQuotation.STATUS_CHOICES):
            quotation.status = new_status
            quotation.save()
            messages.success(request, f'Status updated to {quotation.get_status_display()}.')
    return redirect('supplier_quotation_detail', pk=pk)


# ─── Dealer Transactions ─────────────────────────────────────────────────────

@login_required
def dealer_transaction_list(request):
    if request.user.role == 'dealer':
        try:
            qs = request.user.dealer_profile.transactions.all()
        except Dealer.DoesNotExist:
            qs = DealerTransaction.objects.none()
    else:
        qs = DealerTransaction.objects.select_related('dealer').all()
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(payment_status=status)
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(invoice_number__icontains=q) | Q(dealer__company_name__icontains=q))
    page = paginate(request, qs)
    return render(request, 'core/transactions/dealer_list.html', {
        'page_obj': page, 'q': q, 'status': status,
    })


@login_required
@admin_required
def dealer_transaction_create(request):
    form = DealerTransactionForm(request.POST or None)
    formset = DealerTransactionItemFormSet(request.POST or None)
    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                trans = form.save(commit=False)
                trans.invoice_number = generate_inv_number()
                trans.created_by = request.user
                trans.save()
                items = formset.save(commit=False)
                total = 0
                stock_error = None
                for item in items:
                    if item.product.stock_quantity < item.quantity:
                        stock_error = f'Insufficient stock for "{item.product.name}" (available: {item.product.stock_quantity}).'
                        break
                if stock_error:
                    trans.delete()
                    messages.error(request, stock_error)
                else:
                    for item in items:
                        item.transaction = trans
                        item.subtotal = item.quantity * item.unit_price
                        item.save()
                        product = item.product
                        product.stock_quantity -= item.quantity
                        product.save()
                        StockLog.objects.create(
                            product=product,
                            change_type='sale',
                            quantity_change=-item.quantity,
                            quantity_after=product.stock_quantity,
                            reference=trans.invoice_number,
                            created_by=request.user,
                        )
                        total += item.subtotal
                    for obj in formset.deleted_objects:
                        obj.delete()
                    trans.total_amount = total
                    trans.save()
                    messages.success(request, f'Invoice {trans.invoice_number} created.')
                    return redirect('dealer_transaction_detail', pk=trans.pk)
    return render(request, 'core/transactions/dealer_form.html', {
        'form': form, 'formset': formset, 'title': 'Create Sales Invoice',
    })


@login_required
def dealer_transaction_detail(request, pk):
    if request.user.role == 'dealer':
        try:
            trans = get_object_or_404(DealerTransaction, pk=pk, dealer=request.user.dealer_profile)
        except Dealer.DoesNotExist:
            messages.error(request, 'Profile not found.')
            return redirect('dashboard')
    else:
        trans = get_object_or_404(DealerTransaction, pk=pk)
    return render(request, 'core/transactions/dealer_detail.html', {'transaction': trans})


@login_required
@admin_required
def dealer_transaction_update_payment(request, pk):
    trans = get_object_or_404(DealerTransaction, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('payment_status')
        if status in dict(DealerTransaction.PAYMENT_CHOICES):
            trans.payment_status = status
            trans.save()
            messages.success(request, 'Payment status updated.')
    return redirect('dealer_transaction_detail', pk=pk)


# ─── Supplier Transactions ───────────────────────────────────────────────────

@login_required
def supplier_transaction_list(request):
    if request.user.role == 'supplier':
        try:
            qs = request.user.supplier_profile.transactions.all()
        except Supplier.DoesNotExist:
            qs = SupplierTransaction.objects.none()
    else:
        qs = SupplierTransaction.objects.select_related('supplier').all()
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(payment_status=status)
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(purchase_order_number__icontains=q) | Q(supplier__company_name__icontains=q))
    page = paginate(request, qs)
    return render(request, 'core/transactions/supplier_list.html', {
        'page_obj': page, 'q': q, 'status': status,
    })


@login_required
@admin_required
def supplier_transaction_create(request):
    form = SupplierTransactionForm(request.POST or None)
    formset = SupplierTransactionItemFormSet(request.POST or None)
    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                trans = form.save(commit=False)
                trans.purchase_order_number = generate_po_number()
                trans.created_by = request.user
                trans.save()
                items = formset.save(commit=False)
                total = 0
                for item in items:
                    item.transaction = trans
                    item.subtotal = item.quantity * item.unit_cost
                    item.save()
                    part = item.part
                    part.stock_quantity += item.quantity
                    part.save()
                    StockLog.objects.create(
                        part=part,
                        change_type='purchase',
                        quantity_change=item.quantity,
                        quantity_after=part.stock_quantity,
                        reference=trans.purchase_order_number,
                        created_by=request.user,
                    )
                    total += item.subtotal
                for obj in formset.deleted_objects:
                    obj.delete()
                trans.total_amount = total
                trans.save()
            messages.success(request, f'Purchase Order {trans.purchase_order_number} created.')
            return redirect('supplier_transaction_detail', pk=trans.pk)
    return render(request, 'core/transactions/supplier_form.html', {
        'form': form, 'formset': formset, 'title': 'Create Purchase Order',
    })


@login_required
def supplier_transaction_detail(request, pk):
    if request.user.role == 'supplier':
        try:
            trans = get_object_or_404(SupplierTransaction, pk=pk, supplier=request.user.supplier_profile)
        except Supplier.DoesNotExist:
            messages.error(request, 'Profile not found.')
            return redirect('dashboard')
    else:
        trans = get_object_or_404(SupplierTransaction, pk=pk)
    return render(request, 'core/transactions/supplier_detail.html', {'transaction': trans})


@login_required
@admin_required
def supplier_transaction_update_payment(request, pk):
    trans = get_object_or_404(SupplierTransaction, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('payment_status')
        if status in dict(SupplierTransaction.PAYMENT_CHOICES):
            trans.payment_status = status
            trans.save()
            messages.success(request, 'Payment status updated.')
    return redirect('supplier_transaction_detail', pk=pk)


# ─── Stock ───────────────────────────────────────────────────────────────────

@login_required
@admin_required
def stock_overview(request):
    products = Product.objects.filter(is_active=True).order_by('name')
    parts = Part.objects.filter(is_active=True).select_related('supplier').order_by('name')
    recent_logs = StockLog.objects.select_related('product', 'part', 'created_by').order_by('-created_at')[:20]
    return render(request, 'core/stock/overview.html', {
        'products': products, 'parts': parts, 'recent_logs': recent_logs,
    })


@login_required
@admin_required
def stock_adjust_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = StockAdjustForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        change = form.cleaned_data['quantity_change']
        new_qty = product.stock_quantity + change
        if new_qty < 0:
            messages.error(request, 'Stock cannot go below zero.')
        else:
            product.stock_quantity = new_qty
            product.save()
            StockLog.objects.create(
                product=product,
                change_type='adjustment',
                quantity_change=change,
                quantity_after=new_qty,
                reference=form.cleaned_data['reason'],
                created_by=request.user,
            )
            messages.success(request, f'Stock adjusted. New quantity: {new_qty}')
            return redirect('stock_overview')
    return render(request, 'core/stock/adjust.html', {'form': form, 'item': product, 'item_type': 'Product'})


@login_required
@admin_required
def stock_adjust_part(request, pk):
    part = get_object_or_404(Part, pk=pk)
    form = StockAdjustForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        change = form.cleaned_data['quantity_change']
        new_qty = part.stock_quantity + change
        if new_qty < 0:
            messages.error(request, 'Stock cannot go below zero.')
        else:
            part.stock_quantity = new_qty
            part.save()
            StockLog.objects.create(
                part=part,
                change_type='adjustment',
                quantity_change=change,
                quantity_after=new_qty,
                reference=form.cleaned_data['reason'],
                created_by=request.user,
            )
            messages.success(request, f'Stock adjusted. New quantity: {new_qty}')
            return redirect('stock_overview')
    return render(request, 'core/stock/adjust.html', {'form': form, 'item': part, 'item_type': 'Part'})


# ─── Reports ─────────────────────────────────────────────────────────────────

@login_required
@admin_required
def reports(request):
    today = date.today()
    date_from = request.GET.get('date_from', (today - timedelta(days=30)).isoformat())
    date_to = request.GET.get('date_to', today.isoformat())
    try:
        d_from = date.fromisoformat(date_from)
        d_to = date.fromisoformat(date_to)
    except ValueError:
        d_from = today - timedelta(days=30)
        d_to = today

    sales = DealerTransaction.objects.filter(
        transaction_date__range=[d_from, d_to]
    ).select_related('dealer')
    purchases = SupplierTransaction.objects.filter(
        transaction_date__range=[d_from, d_to]
    ).select_related('supplier')

    sales_by_dealer = sales.values('dealer__company_name').annotate(
        total=Sum('total_amount'), count=Count('id')
    ).order_by('-total')
    purchases_by_supplier = purchases.values('supplier__company_name').annotate(
        total=Sum('total_amount'), count=Count('id')
    ).order_by('-total')

    top_products = DealerTransactionItem.objects.filter(
        transaction__transaction_date__range=[d_from, d_to]
    ).values('product__name').annotate(
        qty=Sum('quantity'), revenue=Sum('subtotal')
    ).order_by('-revenue')[:10]

    top_parts = SupplierTransactionItem.objects.filter(
        transaction__transaction_date__range=[d_from, d_to]
    ).values('part__name').annotate(
        qty=Sum('quantity'), cost=Sum('subtotal')
    ).order_by('-cost')[:10]

    ctx = {
        'date_from': d_from.isoformat(),
        'date_to': d_to.isoformat(),
        'total_sales': sales.aggregate(t=Sum('total_amount'))['t'] or 0,
        'total_purchases': purchases.aggregate(t=Sum('total_amount'))['t'] or 0,
        'sales_count': sales.count(),
        'purchases_count': purchases.count(),
        'sales_by_dealer': sales_by_dealer,
        'purchases_by_supplier': purchases_by_supplier,
        'top_products': top_products,
        'top_parts': top_parts,
        'low_products': Product.objects.filter(is_active=True).extra(where=['stock_quantity <= reorder_level']),
        'low_parts': Part.objects.filter(is_active=True).extra(where=['stock_quantity <= reorder_level']),
    }
    return render(request, 'core/reports/index.html', ctx)


# ─── User Management ─────────────────────────────────────────────────────────

@login_required
@admin_required
def user_list(request):
    qs = User.objects.all().order_by('role', 'username')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
    role = request.GET.get('role', '')
    if role:
        qs = qs.filter(role=role)
    page = paginate(request, qs)
    return render(request, 'core/users/list.html', {
        'page_obj': page, 'q': q, 'role': role,
        'role_choices': User.ROLE_CHOICES,
    })


@login_required
@admin_required
def user_create(request):
    form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'User "{form.cleaned_data["username"]}" created.')
        return redirect('user_list')
    return render(request, 'core/users/form.html', {'form': form, 'title': 'Create User'})


@login_required
@admin_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserEditForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'User updated.')
        return redirect('user_list')
    return render(request, 'core/users/form.html', {'form': form, 'title': f'Edit {user.username}', 'object': user})


@login_required
@admin_required
def user_reset_password(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            user.set_password(new_password)
            user.save()
            messages.success(request, f'Password reset for {user.username}.')
        return redirect('user_list')
    return render(request, 'core/users/reset_password.html', {'target_user': user})
