from django.db import models
from django.contrib.auth.models import User

# ૧. યુઝર પ્રોફાઇલ અને રોલ્સ (User Roles)
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('procurement_officer', 'Procurement Officer'),
        ('manager', 'Manager'),
        ('vendor', 'Vendor'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='vendor')
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

# ૨. વેન્ડર પ્રોફાઇલ (Vendor Details)
class Vendor(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=15, unique=True)
    category = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='Active')

    def __str__(self):
        return self.company_name

# ૩. આર.એફ.ક્યૂ (RFQ - Request for Quotation)
class RFQ(models.Model):
    STATUS_CHOICES = [('Open', 'Open'), ('Closed', 'Closed')]
    title = models.CharField(max_length=255)
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    deadline = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# ૪. કોટેશન (Vendor Quotations)
class Quotation(models.Model):
    STATUS_CHOICES = [('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')]
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name='quotations')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_days = models.PositiveIntegerField()
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"Quote by {self.vendor.company_name} for {self.rfq.title}"