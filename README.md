# WAMS — Web Automated Manufacturing System

A fully working Django web application for managing manufacturing operations — products, parts, dealers, suppliers, quotations, transactions, and stock — with role-based access control.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.x, Django 4.2 |
| Database | SQLite (file-based, persistent disk on Render) |
| Frontend | Bootstrap 5 (CDN), Bootstrap Icons, vanilla JS |
| Static Files | WhiteNoise |
| Production Server | Gunicorn |
| Hosting | Render |

---

## Roles

| Role | What They Can Do |
|---|---|
| **Admin** | Full access — manage products, parts, dealers, suppliers, create quotations and transactions, adjust stock, view reports, manage users |
| **Dealer** | View product catalogue, submit purchase requests (quotations), view their own orders and invoices |
| **Supplier** | View parts catalogue, submit price quotations (offers), view their own purchase orders |

---

## Demo Credentials

> These accounts are seeded automatically on first run via `python manage.py create_admin`.

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@1234` |
| Dealer (sample) | `dealer1` | `Dealer@1234` |
| Supplier (sample) | `supplier1` | `Supplier@1234` |

> The dealer1 and supplier1 accounts are created by the seed script below. On a fresh deploy you only get the admin account; dealers and suppliers are created by the admin through the UI.

---

## Running Locally

### 1. Clone / navigate to the project

```bash
cd Assignment5
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create the default admin account

```bash
python manage.py create_admin
```

This creates `admin` / `Admin@1234`. Override with environment variables if needed:

```bash
ADMIN_USERNAME=myadmin ADMIN_PASSWORD=MyPass@99 ADMIN_EMAIL=me@example.com python manage.py create_admin
```

### 6. (Optional) Seed sample data

Run this once to add sample products, parts, a dealer, and a supplier so you can explore the system immediately:

```bash
python manage.py shell -c "
from decimal import Decimal
from core.models import User, Dealer, Supplier, Product, Part

# Sample dealer
if not User.objects.filter(username='dealer1').exists():
    u = User.objects.create_user('dealer1', 'dealer@example.com', 'Dealer@1234', role='dealer', first_name='Ravi', last_name='Kumar')
    Dealer.objects.create(user=u, company_name='Ravi Enterprises', contact_person='Ravi Kumar', email='dealer@example.com', phone='9876543210', address='123 Market Street', city='Mumbai', credit_limit=500000)
    print('dealer1 created')

# Sample supplier
if not User.objects.filter(username='supplier1').exists():
    u = User.objects.create_user('supplier1', 'supplier@example.com', 'Supplier@1234', role='supplier', first_name='Priya', last_name='Sharma')
    Supplier.objects.create(user=u, company_name='Sharma Parts Co.', contact_person='Priya Sharma', email='supplier@example.com', phone='9123456789', address='456 Industrial Area', city='Pune')
    print('supplier1 created')

# Products
s = Supplier.objects.first()
if not Product.objects.exists():
    Product.objects.create(product_id='PRD-001', name='Industrial Motor 5HP', category='mechanical', unit_price=Decimal('12500'), stock_quantity=50, reorder_level=10)
    Product.objects.create(product_id='PRD-002', name='Control Panel Unit', category='electronics', unit_price=Decimal('8750'), stock_quantity=30, reorder_level=5)
    Product.objects.create(product_id='PRD-003', name='Hydraulic Pump', category='mechanical', unit_price=Decimal('22000'), stock_quantity=20, reorder_level=5)
    print('3 products created')

# Parts
if not Part.objects.exists():
    Part.objects.create(part_id='PRT-001', name='Steel Bearing 6205', unit_cost=Decimal('180'), stock_quantity=200, reorder_level=50, supplier=s)
    Part.objects.create(part_id='PRT-002', name='Copper Wire 2.5mm', unit_cost=Decimal('650'), stock_quantity=100, reorder_level=30, supplier=s)
    Part.objects.create(part_id='PRT-003', name='Rubber Seal Ring', unit_cost=Decimal('95'), stock_quantity=500, reorder_level=100, supplier=s)
    print('3 parts created')
"
```

### 7. Run the development server

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## Deploying to Render

### Prerequisites

- A [Render](https://render.com) account
- The project pushed to a GitHub repository

### Steps

1. **Push to GitHub**

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

2. **Create a new Web Service on Render**
   - Go to [render.com/dashboard](https://dashboard.render.com) → **New** → **Web Service**
   - Connect your GitHub repository
   - Render auto-detects `render.yaml` — all settings are pre-configured

3. **Set the `ADMIN_PASSWORD` environment variable**
   - In Render dashboard → your service → **Environment**
   - Add `ADMIN_PASSWORD` with a strong password (this is the only secret you need to set manually)

4. **Deploy**
   - Render runs `build.sh` automatically:
     - Installs dependencies
     - Collects static files
     - Runs migrations
     - Creates the admin user
   - After deploy, visit your `.onrender.com` URL

### What `render.yaml` configures

```yaml
- Build command:   ./build.sh
- Start command:   gunicorn wams.wsgi:application
- Persistent disk: /var/data (1 GB) — SQLite database stored here
- SECRET_KEY:      auto-generated by Render
- DB_PATH:         /var/data/db.sqlite3
```

> **Note on SQLite and Render:** The `render.yaml` mounts a 1 GB persistent disk at `/var/data`. This keeps your database across redeploys. Persistent disks require a paid Render plan. On the free tier the filesystem resets on each deploy — use the seed script in `build.sh` or switch to PostgreSQL if you need free-tier persistence.

---

## Key Workflows

### Admin creates a Dealer account

1. Login as admin → **Dealers** → **Add Dealer**
2. Fill in login credentials (username + password) and company details
3. The dealer can now login with those credentials

### Admin creates a Supplier account

1. Login as admin → **Suppliers** → **Add Supplier**
2. Fill in login credentials and company details
3. The supplier can now login

### Dealer submits a Purchase Request

1. Login as dealer → **Submit Purchase Request** (dashboard or My Quotations)
2. Set required-by date, add products + quantities + budget price
3. Catalogue price auto-fills when a product is selected
4. Submit → status set to **Sent** → admin is notified

### Supplier submits a Price Quotation

1. Login as supplier → **Submit Price Quotation** (dashboard or My Quotations)
2. Set offer validity date, add parts + available quantity + offered price
3. Reference price shown as a hint when a part is selected
4. Submit → status set to **Received** → admin reviews

### Admin processes a Dealer Quotation

1. **Dealer Quotations** → open the request
2. Change status to **Accepted**
3. Click **Create Invoice from this Quotation**
4. Confirm items and save — stock is automatically deducted

### Admin processes a Supplier Quotation

1. **Supplier Quotations** → open the offer
2. Change status to **Accepted**
3. Click **Create Purchase Order**
4. Confirm items and save — part stock is automatically incremented

---

## Project Structure

```
Assignment5/
├── wams/                   # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                   # Main application
│   ├── models.py           # All database models
│   ├── views.py            # All views (role-aware)
│   ├── forms.py            # All forms and formsets
│   ├── urls.py             # URL routing
│   ├── decorators.py       # Role-based access decorators
│   ├── admin.py            # Django admin registrations
│   └── management/
│       └── commands/
│           └── create_admin.py
├── templates/
│   ├── base.html           # Sidebar layout base template
│   ├── registration/
│   │   └── login.html
│   └── core/
│       ├── dashboard.html
│       ├── products/
│       ├── parts/
│       ├── dealers/
│       ├── suppliers/
│       ├── quotations/     # dealer_form, dealer_request_form, supplier_form, supplier_offer_form
│       ├── transactions/
│       ├── stock/
│       ├── reports/
│       └── users/
├── static/
│   └── css/style.css
├── manage.py
├── requirements.txt
├── build.sh                # Render build script
└── render.yaml             # Render deployment config
```

---

## Data Models

| Model | Description |
|---|---|
| `User` | Extended Django user with `role` field (admin / dealer / supplier) |
| `Product` | Finished goods with category, price, stock level |
| `Part` | Raw components linked to a supplier |
| `Dealer` | Company profile linked to a dealer User |
| `Supplier` | Company profile linked to a supplier User |
| `DealerQuotation` + Items | Purchase request from dealer or quotation issued by admin |
| `SupplierQuotation` + Items | Price offer from supplier or request raised by admin |
| `DealerTransaction` + Items | Sales invoice; auto-decrements product stock |
| `SupplierTransaction` + Items | Purchase order; auto-increments part stock |
| `StockLog` | Audit trail of every stock change |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | insecure dev key | Django secret key — always set in production |
| `DEBUG` | `True` | Set to `False` in production |
| `DB_PATH` | `./db.sqlite3` | Path to SQLite file |
| `ADMIN_USERNAME` | `admin` | Username for the auto-created admin |
| `ADMIN_PASSWORD` | `Admin@1234` | Password for the auto-created admin |
| `ADMIN_EMAIL` | `admin@wams.com` | Email for the auto-created admin |
