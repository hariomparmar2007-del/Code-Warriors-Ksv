from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('vendors/', views.vendor_management_view, name='vendor_management'),
    path('rfq/', views.rfq_creation_view, name='rfq_creation'),
    path('submit-quote/', views.quotation_submission_view, name='quotation_submission'),
    path('compare-quotes/', views.quotation_comparison_view, name='quotation_comparison'),
    
    # નવી જોડેલી મેજિક લિંક્સ
    path('approve-quote/<int:quote_id>/', views.approve_quotation_action, name='approve_quotation'),
    path('invoice/<int:quote_id>/', views.invoice_view, name='view_invoice'),
]