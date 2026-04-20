import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import User, Dealer, Supplier, Product, Part


class Command(BaseCommand):
    help = 'Seed random data for dealers, suppliers, products, and parts'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...\n')

        # --- Admin user ---
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@wams.com', 'role': 'admin', 'is_staff': True, 'is_superuser': True}
        )
        if created:
            admin.set_password('Admin@1234')
            admin.save()
            self.stdout.write(self.style.SUCCESS('  Admin user created'))
        else:
            self.stdout.write('  Admin user already exists, skipping')

        # --- Suppliers ---
        supplier_data = [
            ('Sharma Parts Co.', 'Rajesh Sharma', 'rajesh@sharmaparts.in', '9876543210', '45 Industrial Area, Mumbai', 'Mumbai'),
            ('MetalWorks Ltd.', 'Priya Mehta', 'priya@metalworks.in', '9876543211', '12 Steel Nagar, Pune', 'Pune'),
            ('Precision Components', 'Anil Verma', 'anil@precisioncomp.com', '9876543212', '7 Gear Road, Bangalore', 'Bangalore'),
            ('Bharat Fasteners', 'Sunita Rao', 'sunita@bharatfasteners.com', '9876543213', '88 Lajpat Nagar, Delhi', 'Delhi'),
            ('GreenChem Solutions', 'Vikram Patel', 'vikram@greenchem.in', '9876543214', '33 Chemical Zone, Ankleshwar', 'Ankleshwar'),
        ]

        suppliers = []
        for i, (company, contact, email, phone, addr, city) in enumerate(supplier_data):
            user, _ = User.objects.get_or_create(
                username=f'supplier{i+1}',
                defaults={'email': email, 'role': 'supplier'}
            )
            if user.password == '' or not user.has_usable_password():
                user.set_password('Supplier@123')
                user.save()

            supplier, created = Supplier.objects.get_or_create(
                user=user,
                defaults={
                    'company_name': company,
                    'contact_person': contact,
                    'email': email,
                    'phone': phone,
                    'address': addr,
                    'city': city,
                    'is_active': True,
                }
            )
            suppliers.append(supplier)
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  Supplier [{status}]: {company}')

        # --- Dealers ---
        dealer_data = [
            ('Ravi Enterprises', 'Ravi Gupta', 'ravi@ravienterprises.com', '9988776655', '22 Market Street, Mumbai', 'Mumbai', 500000),
            ('Sharma & Sons', 'Mohan Sharma', 'mohan@sharmaandsons.com', '9988776656', '5 Link Road, Pune', 'Pune', 750000),
            ('Apex Industries', 'Sneha Reddy', 'sneha@apexindustries.com', '9988776657', '14 Hi-Tech Park, Hyderabad', 'Hyderabad', 1000000),
            ('BuildWell Supplies', 'Arun Joshi', 'arun@buildwell.in', '9988776658', '77 Civil Lines, Lucknow', 'Lucknow', 300000),
            ('TechDistri Hub', 'Meera Shah', 'meera@techdistri.com', '9988776659', '3 Electronics City, Bangalore', 'Bangalore', 1200000),
            ('National Traders', 'Vijay Kumar', 'vijay@nationaltraders.com', '9988776660', '11 Mahatma Gandhi Rd, Chennai', 'Chennai', 600000),
            ('Om Industrial', 'Ramesh Patil', 'ramesh@omindustrial.com', '9988776661', '9 MIDC, Nashik', 'Nashik', 400000),
        ]

        dealers = []
        for i, (company, contact, email, phone, addr, city, credit) in enumerate(dealer_data):
            user, _ = User.objects.get_or_create(
                username=f'dealer{i+1}',
                defaults={'email': email, 'role': 'dealer'}
            )
            if user.password == '' or not user.has_usable_password():
                user.set_password('Dealer@123')
                user.save()

            dealer, created = Dealer.objects.get_or_create(
                user=user,
                defaults={
                    'company_name': company,
                    'contact_person': contact,
                    'email': email,
                    'phone': phone,
                    'address': addr,
                    'city': city,
                    'credit_limit': credit,
                    'is_active': True,
                }
            )
            dealers.append(dealer)
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  Dealer [{status}]: {company}')

        # --- Products ---
        product_data = [
            ('PRD-001', 'Industrial Motor 5HP', 'mechanical', 'High-efficiency 5HP three-phase induction motor for industrial machinery.', 45000),
            ('PRD-002', 'Control Panel 24V', 'electronics', '24V DC control panel with overload and short-circuit protection.', 12000),
            ('PRD-003', 'Hydraulic Pump 20L', 'mechanical', 'Double-acting hydraulic pump, 20L capacity, max 300 bar.', 28000),
            ('PRD-004', 'Circuit Breaker 63A', 'electronics', '63A AC miniature circuit breaker, 10kA breaking capacity.', 3500),
            ('PRD-005', 'Steel Bearing 6205', 'mechanical', 'Deep groove ball bearing 6205, 25x52x15mm, sealed.', 450),
            ('PRD-006', 'Pneumatic Valve Assembly', 'mechanical', '5/2 way pneumatic solenoid valve, 1/4" BSP ports.', 7800),
            ('PRD-007', 'Power Supply Unit 48V', 'electronics', '48V 10A SMPS power supply unit, wide input range.', 5500),
            ('PRD-008', 'Conveyor Belt 1m', 'mechanical', 'Reinforced rubber conveyor belt, 1m width, per metre.', 2200),
            ('PRD-009', 'Sensor Proximity 12mm', 'electronics', 'Inductive proximity sensor, 12mm sensing range, NPN output.', 1200),
            ('PRD-010', 'Hydraulic Cylinder 50mm', 'mechanical', 'Double-acting hydraulic cylinder, 50mm bore, 200mm stroke.', 15000),
            ('PRD-011', 'Chemical Solvent 5L', 'chemical', 'Industrial grade solvent, 5L container, low toxicity formula.', 3200),
            ('PRD-012', 'Safety Relay 24VDC', 'electronics', '24VDC safety relay, dual-channel, category 4 per ISO 13849.', 8900),
            ('PRD-013', 'Drive Belt V-type', 'mechanical', 'V-belt type A68, oil and heat resistant, per piece.', 380),
            ('PRD-014', 'PLC Module 16 I/O', 'electronics', '16-channel digital I/O PLC expansion module, 24V.', 14500),
            ('PRD-015', 'Insulating Fabric 2m', 'textile', 'Thermal insulating fabric, 2m roll, 1000°C rated.', 4100),
        ]

        products = []
        for pid, name, cat, desc, price in product_data:
            product, created = Product.objects.get_or_create(
                product_id=pid,
                defaults={
                    'name': name,
                    'category': cat,
                    'description': desc,
                    'unit_price': price,
                    'stock_quantity': random.randint(5, 200),
                    'reorder_level': random.randint(5, 25),
                    'is_active': True,
                }
            )
            products.append(product)
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  Product [{status}]: {name}')

        # --- Parts ---
        part_data = [
            ('PRT-001', 'Steel Bearing 6205', 'Ball bearing, sealed, for motor shafts.', 180, suppliers[0]),
            ('PRT-002', 'Copper Wire 2.5mm 100m', '100m roll of 2.5sqmm copper wire, red.', 4200, suppliers[1]),
            ('PRT-003', 'Rubber Seal Ring 30mm', 'NBR rubber O-ring, 30mm ID, per piece.', 25, suppliers[0]),
            ('PRT-004', 'Allen Key Set M3-M12', 'Metric allen key set, 9-piece, chrome vanadium.', 650, suppliers[2]),
            ('PRT-005', 'M8 Hex Bolt 50mm (box 100)', 'Galvanised M8x50 hex bolts, box of 100.', 1100, suppliers[3]),
            ('PRT-006', 'Solenoid Coil 24V', '24VDC solenoid coil for pneumatic valves.', 850, suppliers[2]),
            ('PRT-007', 'Hydraulic Hose 1/2" 2m', '1/2" BSP hydraulic hose, 2m length, 350 bar.', 1900, suppliers[0]),
            ('PRT-008', 'MOSFET IRF540N', 'N-channel MOSFET 100V 33A, Through-hole TO-220.', 55, suppliers[1]),
            ('PRT-009', 'Relay 24VDC 5Pin', '24VDC signal relay, 5-pin, 10A contacts.', 85, suppliers[2]),
            ('PRT-010', 'Thermal Paste 50g', 'High-performance thermal paste, 50g syringe.', 320, suppliers[4]),
            ('PRT-011', 'M6 Lock Nut (box 200)', 'M6 nylon insert lock nuts, box of 200.', 480, suppliers[3]),
            ('PRT-012', 'Circuit Board PCB 100x80', 'Custom FR4 PCB, 100x80mm, single-sided.', 240, suppliers[1]),
            ('PRT-013', 'LED 5mm Red (pack 50)', '5mm red LED, pack of 50, 2V forward voltage.', 120, suppliers[1]),
            ('PRT-014', 'Aluminium Sheet 2mm 1x1m', '2mm aluminium sheet, 1m x 1m, mill finish.', 2100, suppliers[0]),
            ('PRT-015', 'Cotton Webbing 50mm 10m', 'Industrial cotton webbing, 50mm width, 10m roll.', 380, suppliers[4]),
        ]

        for pid, name, desc, cost, supplier in part_data:
            part, created = Part.objects.get_or_create(
                part_id=pid,
                defaults={
                    'name': name,
                    'description': desc,
                    'unit_cost': cost,
                    'stock_quantity': random.randint(10, 500),
                    'reorder_level': random.randint(10, 50),
                    'supplier': supplier,
                    'is_active': True,
                }
            )
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  Part [{status}]: {name}')

        self.stdout.write(self.style.SUCCESS('\nSeed data complete!'))
        self.stdout.write(self.style.WARNING('  Dealers: dealer1-Dealer@123 ... dealer7-Dealer@123'))
        self.stdout.write(self.style.WARNING('  Suppliers: supplier1-Supplier@123 ... supplier5-Supplier@123'))
