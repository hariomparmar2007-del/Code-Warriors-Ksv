from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User  
from django.contrib import messages

# ૧. લોગિન વ્યુ
def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password!")
            
    return render(request, 'core/login.html')

# ૨. ડેશબોર્ડ વ્યુ (રોલ બેઝ્ડ સેટિંગ્સ સાથે)
def dashboard_view(request):
    # જો યુઝર લોગિન ના હોય તો સીધો લોગિન પેજ પર મોકલો
    if not request.user.is_authenticated:
        return redirect('login')

    # અસલી વેન્ડર્સ કાઉન્ટ કરો
    total_vendors = User.objects.filter(is_superuser=False).exclude(username__startswith='rfq_').exclude(username__startswith='quote_').count()
    # RFQ કાઉન્ટ કરો
    total_rfqs = User.objects.filter(username__startswith='rfq_').count()
    
    context = {
        'role': "Admin" if request.user.is_superuser else "Vendor",
        'team_name': "VendorBridge Devs",
        'total_vendors': total_vendors, 
        'total_rfqs': total_rfqs, 
        'active_rfqs': total_rfqs, 
    }
    return render(request, 'core/dashboard.html', context)

# ૩. વેન્ડર મેનેજમેન્ટ વ્યુ
def vendor_management_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        company_name = request.POST.get('company_name')
        gst_number = request.POST.get('gst_number')
        category = request.POST.get('category')
        email = f"{username}@vendor.com"
        
        if username:
            username = username.strip().replace(" ", "_").lower()
            
            if not User.objects.filter(username=username).exists():
                new_vendor = User.objects.create_user(
                    username=username,
                    email=email,
                    password='admin123',
                    first_name=company_name, 
                    last_name=f"{gst_number}|{category}" 
                )
                new_vendor.save()
                messages.success(request, f"Vendor '{company_name}' registered successfully!")
                return redirect('vendor_management') 
            else:
                messages.warning(request, f"Username '{username}' already exists!")
                return redirect('vendor_management')

    all_users = User.objects.filter(is_superuser=False).exclude(username__startswith='rfq_').exclude(username__startswith='quote_') 
    vendors_list = []
    
    for u in all_users:
        gst = "N/A"
        cat = "N/A"
        if u.last_name and "|" in u.last_name:
            gst, cat = u.last_name.split("|", 1)
            
        vendors_list.append({
            'username': u.username,
            'company_name': u.first_name if u.first_name else u.username,
            'gst_number': gst,
            'category': cat
        })
    
    context = {
        'vendors': vendors_list, 
    }
    return render(request, 'core/vendor_management.html', context)

# ૪. આરએફક્યુ ક્રિએશન વ્યુ
def rfq_creation_view(request):
    if request.method == "POST":
        import random
        rfq_id = random.randint(1000, 9999)
        rfq_username = f"rfq_{rfq_id}"
        
        new_rfq = User.objects.create_user(
            username=rfq_username,
            email=f"rfq_{rfq_id}@company.com",
            password='rfq_password'
        )
        new_rfq.save()
        
        messages.success(request, f"RFQ #{rfq_id} Created successfully!")
        return redirect('dashboard') 
        
    return render(request, 'core/rfq_creation.html')

# ૫. ક્વોટેશન સબમિટ વ્યુ
def quotation_submission_view(request):
    if request.method == "POST":
        rfq_id = request.POST.get('rfq_id', '')
        price = request.POST.get('price_per_unit', '0')
        days = request.POST.get('delivery_days', '0')
        notes = request.POST.get('notes', '')
        
        vendor_name = request.user.first_name if request.user.is_authenticated and request.user.first_name else "Global Vendor Ltd"
        
        # આ વેન્ડરનો અસલી GST નંબર શોધી કાઢો જો લોગિન હોય તો, નહીંતર ડમી
        vendor_gst = "24GSTIN9999F1Z1"
        if request.user.is_authenticated and request.user.last_name and "|" in request.user.last_name:
            vendor_gst = request.user.last_name.split("|")[0]
            
        import random
        quote_unique_id = random.randint(100, 999)
        quote_username = f"quote_{quote_unique_id}"
        
        new_quote = User.objects.create_user(
            username=quote_username,
            email=f"{rfq_id}@bridge.com", 
            password="quote_password",
            first_name=vendor_name,           
            last_name=f"{price}|{days}|Pending|{vendor_gst}" # GST પણ અંદર જોડી દીધો
        )
        new_quote.save()
        
        messages.success(request, "Your Quotation has been submitted successfully!")
        return redirect('dashboard')

    all_rfqs = User.objects.filter(username__startswith='rfq_')
    rfq_data_list = []
    for r in all_rfqs:
        clean_id = r.username.replace('rfq_', '')
        rfq_data_list.append({
            'id': r.username,                
            'title': f"RFQ #{clean_id}"       
        })
        
    context = {
        'open_rfqs': rfq_data_list, 
    }
    return render(request, 'core/quotation_submission.html', context)

# ૬. ક્વોટેશન કમ્પેરિઝન વ્યુ
def quotation_comparison_view(request):
    selected_rfq_id = request.GET.get('rfq_id', '')
    all_rfqs_db = User.objects.filter(username__startswith='rfq_')
    all_rfqs_list = []
    for r in all_rfqs_db:
        clean_id = r.username.replace('rfq_', '')
        all_rfqs_list.append({
            'id': r.username,
            'title': f"RFQ #{clean_id}"
        })

    quotations_list = []
    lowest_quote_id = None
    lowest_price = float('inf')

    if selected_rfq_id:
        quote_users = User.objects.filter(username__startswith='quote_', email=f"{selected_rfq_id}@bridge.com")
        
        for q in quote_users:
            price_val = 0
            status = "Pending"
            
            if q.last_name and "|" in q.last_name:
                parts = q.last_name.split("|")
                try:
                    price_val = float(parts[0])
                except:
                    price_val = 0
                status = parts[2] if len(parts) > 2 else "Pending"
            
            if price_val < lowest_price and status == "Pending":
                lowest_price = price_val
                lowest_quote_id = q.username.replace('quote_', '')

            quotations_list.append({
                'id': q.username.replace('quote_', ''),
                'vendor': {'company_name': q.first_name},
                'total_price': price_val,
                'status': status
            })

    context = {
        'all_rfqs': all_rfqs_list,          
        'selected_rfq_id': selected_rfq_id,  
        'quotations': quotations_list,      
        'lowest_quote_id': lowest_quote_id,  
    }
    return render(request, 'core/quotation_comparison.html', context)

# ૭. ક્વોટેશન અપ્રૂવલ એક્શન (🔥 સુપર સિક્યોર લોક: હવે ફક્ત એડમિન જ અપ્રૂવ કરી શકશે!)
def approve_quotation_action(request, quote_id=None):
    # 🛑 સિક્યોરિટી ચેક: જો યુઝર લોગિન ના હોય અથવા એ એડમિન (Superuser) ના હોય તો એને રોકી દો!
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, "🛡️ Access Denied! Only Company Admin can approve quotations.")
        return redirect('login') # 👈 સીધો લોગિન પેજ પર ધક્કો મારી દો
        
    # જો એ સાચો એડમિન હશે તો જ નીચેનો અપ્રૂવલ કોડ રન થશે
    quote_username = f"quote_{quote_id}"
    try:
        q_user = User.objects.get(username=quote_username)
        if q_user.last_name and "|" in q_user.last_name:
            parts = q_user.last_name.split("|")
            gst_val = parts[3] if len(parts) > 3 else "N/A"
            q_user.last_name = f"{parts[0]}|{parts[1]}|Approved|{gst_val}"
            q_user.save()
        messages.success(request, f"Quotation #{quote_id} Approved! PO Generated.")
    except User.DoesNotExist:
        pass
    return redirect('quotation_comparison')

# ૮. ઇન્વોઇસ વ્યુ (🔥 ૧૦0% ફિક્સ: હવે તમારા HTML ના બધા જ ડાયનેમિક વેરિએબલ્સ સાથે ગણતરી કરશે!)
def invoice_view(request, quote_id=None):
    quote_username = f"quote_{quote_id}"
    
    # ડીફોલ્ટ ડેટા સેટ કરવો
    vendor_name = "Global Supplier Ltd"
    gst_no = "24AAAAV1234F1Z1"
    subtotal = 0.0
    
    try:
        q_user = User.objects.get(username=quote_username)
        vendor_name = q_user.first_name
        if q_user.last_name and "|" in q_user.last_name:
            parts = q_user.last_name.split("|")
            subtotal = float(parts[0])
            gst_no = parts[3] if len(parts) > 3 else "24AAAAV1234F1Z1"
    except:
        pass
        
    # ૧૮% GST ની લાઈવ ગણતરી
    tax_amount = round(subtotal * 0.18, 2)
    final_amount = round(subtotal + tax_amount, 2)
    
    import random
    context = {
        'team_name': "VendorBridge Devs",
        'po_number': f"PO-2026-{random.randint(1000, 9999)}",
        'invoice_number': f"INV-{quote_id}-{random.randint(10, 99)}",
        'quote': {
            'vendor': {
                'company_name': vendor_name,
                'gst_number': gst_no
            }
        },
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'final_amount': final_amount
    }
        
    return render(request, 'core/invoice.html', context)

# ૯. લોગઆઉટ વ્યુ
def logout_view(request):
    logout(request)
    return redirect('login')