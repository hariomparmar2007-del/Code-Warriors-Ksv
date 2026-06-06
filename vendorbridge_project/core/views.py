from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile, Vendor, RFQ, Quotation

# ૧. લોગિન લોજિક (Login Screen)
def login_view(request):
    error_message = None
    if request.method == "POST":
        u = request.POST.get('username')
        p = request.POST.get('password')
        
        user = authenticate(username=u, password=p)
        if user is not None:
            login(request, user)
            UserProfile.objects.get_or_create(user=user, defaults={'role': 'admin'})
            return redirect('dashboard')
        else:
            error_message = "ખોટો આઈડી અથવા પાસવર્ડ!"
            
    return render(request, 'core/login.html', {'error': error_message})

# ૨. ડેશબોર્ડ લોજિક (Dashboard Screen)
@login_required
def dashboard_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'admin'})
    role = profile.role
    
    total_rfqs = RFQ.objects.count()
    open_rfqs = RFQ.objects.filter(status='Open').count()
    total_vendors = Vendor.objects.count()
    
    context = {
        'role': role,
        'total_rfqs': total_rfqs,
        'open_rfqs': open_rfqs,
        'total_vendors': total_vendors,
        'team_name': 'Code-Warriors-Ksv'
    }
    
    return render(request, 'core/dashboard.html', context)

# ૩. લોગઆઉટ લોજિક
def logout_view(request):
    logout(request)
    return redirect('login')

# ૪. વેન્ડર મેનેજમેન્ટ લોજિક (Vendor Management Screen)
@login_required
def vendor_management_view(request):
    if request.method == "POST":
        company_name = request.POST.get('company_name')
        gst_number = request.POST.get('gst_number')
        category = request.POST.get('category')
        username = request.POST.get('username')
        
        user = User.objects.create_user(username=username, password='vendor123')
        profile = UserProfile.objects.create(user=user, role='vendor')
        
        Vendor.objects.create(
            user_profile=profile,
            company_name=company_name,
            gst_number=gst_number,
            category=category
        )
        return redirect('vendor_management')
        
    all_vendors = Vendor.objects.all()
    return render(request, 'core/vendor_management.html', {'vendors': all_vendors})

# ૫. આર.એફ.ક્યૂ ક્રિએશન લોજિક (RFQ Creation Screen)
@login_required
def rfq_creation_view(request):
    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description')
        quantity = request.POST.get('quantity')
        
        deadline = timezone.now() + timezone.timedelta(days=2)
        
        RFQ.objects.create(
            title=title,
            description=description,
            quantity=quantity,
            deadline=deadline,
            created_by=request.user
        )
        return redirect('rfq_creation')

    all_rfqs = RFQ.objects.all()
    return render(request, 'core/rfq_creation.html', {'rfqs': all_rfqs})

# ૬. વેન્ડર ક્વોટેશન સબમિશન (Vendor Quotation Submission Screen)
@login_required
def quotation_submission_view(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
        vendor = Vendor.objects.get(user_profile=profile)
    except (UserProfile.DoesNotExist, Vendor.DoesNotExist):
        vendor = None

    if request.method == "POST" and vendor:
        rfq_id = request.POST.get('rfq_id')
        price_per_unit = float(request.POST.get('price_per_unit'))
        delivery_days = request.POST.get('delivery_days')
        notes = request.POST.get('notes')
        
        rfq = RFQ.objects.get(id=rfq_id)
        total_price = price_per_unit * rfq.quantity
        
        Quotation.objects.create(
            rfq=rfq,
            vendor=vendor,
            price_per_unit=price_per_unit,
            total_price=total_price,
            delivery_days=delivery_days,
            notes=notes
        )
        return redirect('quotation_submission')

    open_rfqs = RFQ.objects.filter(status='Open')
    my_quotations = Quotation.objects.filter(vendor=vendor) if vendor else []
    
    context = {
        'open_rfqs': open_rfqs,
        'my_quotations': my_quotations,
        'vendor': vendor
    }
    return render(request, 'core/quotation_submission.html', context)

# ૭. ક્વોટેશન સરખામણી અને અપ્રૂવલ (Quotation Comparison & Approval Workflow)
@login_required
def quotation_comparison_view(request):
    all_rfqs = RFQ.objects.all()
    selected_rfq_id = request.GET.get('rfq_id')
    quotations = []
    lowest_quote_id = None

    if selected_rfq_id:
        quotations = Quotation.objects.filter(rfq_id=selected_rfq_id).order_by('total_price')
        if quotations.exists():
            lowest_quote_id = quotations.first().id

    context = {
        'all_rfqs': all_rfqs,
        'quotations': quotations,
        'selected_rfq_id': selected_rfq_id,
        'lowest_quote_id': lowest_quote_id
    }
    return render(request, 'core/quotation_comparison.html', context)

# ૮. મંજૂરી આપવાનું લોજિક (Approve Action)
@login_required
def approve_quotation_action(request, quote_id):
    quote = get_object_or_404(Quotation, id=quote_id)
    quote.status = 'Approved'
    quote.save()
    
    # જેવું આ કોટેશન પાસ થાય એટલે એના મેઈન RFQ ને બંધ (Closed) કરી દેવું
    quote.rfq.status = 'Closed'
    quote.rfq.save()
    
    # બાકીના બધા જ ભાવોને ઓટોમેટિક Reject કરી દેવા
    Quotation.objects.filter(rfq=quote.rfq).exclude(id=quote_id).update(status='Rejected')
    
    return redirect(f'/compare-quotes/?rfq_id={quote.rfq.id}')

# ૯. પર્ચેઝ ઓર્ડર અને ઇન્વોઇસ જનરેશન પ્રિન્ટ પેજ (PO & Invoice Generation Screen)
@login_required
def invoice_view(request, quote_id):
    quote = get_object_or_404(Quotation, id=quote_id)
    
    # ૧૮% GST ટેક્સ અને ફાઇનલ અમાઉન્ટની લાઈવ ગણતરી (Tax Calculations)
    subtotal = float(quote.total_price)
    tax_amount = subtotal * 0.18
    final_amount = subtotal + tax_amount
    
    context = {
        'quote': quote,
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'final_amount': final_amount,
        'po_number': f"PO-2026-00{quote.id}", # ઓટો જનરેટેડ PO નંબર
        'invoice_number': f"INV-2026-00{quote.id}", # ઓટો જનરેટેડ બિલ નંબર
        'date': timezone.now().date(),
        'team_name': 'Code-Warriors-Ksv'
    }
    return render(request, 'core/invoice.html', context)