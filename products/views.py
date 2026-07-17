# products/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .models import Product

PRODUCT_FIELDS = ["name", "description", "price", "product_type", "status", "project", "asset"]


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        qs = Product.objects.all()
        status = self.request.GET.get("status")
        if status and status != "all":
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Product.STATUS_CHOICES
        ctx["current_status"] = self.request.GET.get("status", "all")
        return ctx


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    fields = PRODUCT_FIELDS
    template_name = "products/product_form.html"

    def get_success_url(self):
        return reverse("products:detail", kwargs={"pk": self.object.pk})


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    fields = PRODUCT_FIELDS
    template_name = "products/product_form.html"

    def get_success_url(self):
        return reverse("products:detail", kwargs={"pk": self.object.pk})


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = "products/product_confirm_delete.html"
    success_url = reverse_lazy("products:list")
