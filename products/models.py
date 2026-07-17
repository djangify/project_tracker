# products/models.py
from django.db import models


class Product(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("retired", "Retired"),
    ]

    TYPE_CHOICES = [
        ("digital_download", "Digital download"),
        ("service", "Service"),
        ("course", "Course"),
        ("membership", "Membership"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    product_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="digital_download")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
        help_text="The business this product belongs to",
    )
    asset = models.ForeignKey(
        "assets.Asset",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
        help_text="The deliverable file, if there is one",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name

    @property
    def total_revenue(self):
        return self.sales.aggregate(total=models.Sum("amount"))["total"] or 0

    @property
    def sale_count(self):
        return self.sales.count()


class Sale(models.Model):
    """A single sale of a Product to a Contact. Supersedes the flat
    made_purchase/revenue fields on crm.Contact once real sales exist —
    those fields stay for backward compatibility but this is the source of
    truth for multi-product tracking."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales")
    contact = models.ForeignKey(
        "crm.Contact", null=True, blank=True, on_delete=models.SET_NULL, related_name="sales"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    funnel_step = models.ForeignKey(
        "products.FunnelStep", null=True, blank=True, on_delete=models.SET_NULL, related_name="sales"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        who = self.contact.name if self.contact else "Unknown"
        return f"{self.product.name} → {who} (£{self.amount})"


class FunnelStep(models.Model):
    """One step/offer in a product's funnel (e.g. the main offer, an
    order-bump, an upsell/OTO). Lives inside products rather than its own
    app until there's enough of these to justify splitting out."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="funnel_steps")
    name = models.CharField(max_length=200)
    position = models.PositiveIntegerField(default=0, help_text="Order in the funnel, lowest first")
    price_override = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Leave blank to use the product's normal price",
    )
    is_oto = models.BooleanField("Is one-time-offer / upsell", default=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return f"{self.product.name} — {self.name}"

    @property
    def effective_price(self):
        return self.price_override if self.price_override is not None else self.product.price
