# clinic_catalog/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from platform_accounts.models import Account

class Category(models.Model):
    """
    Categories for organizing catalog items (services, products, etc.)
    """
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='categories',
        verbose_name=_('account')
    )
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcategories',
        verbose_name=_('parent category')
    )
    is_active = models.BooleanField(_('active'), default=True)
    
    # Display order
    display_order = models.PositiveIntegerField(_('display order'), default=0)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['display_order', 'name']
        unique_together = [['account', 'name', 'parent']]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class CatalogItem(models.Model):
    """
    Base class for items in the catalog (services, products, etc.)
    """
    TYPE_CHOICES = (
        ('service', _('Service')),
        ('procedure', _('Procedure')),
        ('product', _('Product')),
        ('package', _('Package')),
    )
    
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='catalog_items',
        verbose_name=_('account')
    )
    code = models.CharField(_('code'), max_length=50)
    name = models.CharField(_('name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='items',
        verbose_name=_('category')
    )
    item_type = models.CharField(_('type'), max_length=20, choices=TYPE_CHOICES)
    
    # Pricing
    price = models.DecimalField(
        _('price'), 
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    variable_price = models.BooleanField(
        _('variable price'), 
        default=False,
        help_text=_('If enabled, the price can be adjusted when creating a procedure')
    )
    tax_rate = models.DecimalField(
        _('tax rate'), 
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('catalog item')
        verbose_name_plural = _('catalog items')
        ordering = ['code', 'name']
        unique_together = [['account', 'code']]
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Package(models.Model):
    """
    A package is a collection of catalog items offered together.
    """
    catalog_item = models.OneToOneField(
        CatalogItem, 
        on_delete=models.CASCADE,
        related_name='package_details',
        verbose_name=_('catalog item')
    )
    included_items = models.ManyToManyField(
        CatalogItem,
        through='PackageItem',
        related_name='included_in_packages',
        verbose_name=_('included items')
    )
    
    # Discount information
    discount_type = models.CharField(
        _('discount type'),
        max_length=20,
        choices=(
            ('percentage', _('Percentage')),
            ('fixed', _('Fixed Amount')),
        ),
        default='percentage'
    )
    discount_value = models.DecimalField(
        _('discount value'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    class Meta:
        verbose_name = _('package')
        verbose_name_plural = _('packages')
    
    def __str__(self):
        return self.catalog_item.name


class PackageItem(models.Model):
    """
    Represents items included in a package with quantity.
    """
    package = models.ForeignKey(
        Package, 
        on_delete=models.CASCADE,
        related_name='package_items',
        verbose_name=_('package')
    )
    item = models.ForeignKey(
        CatalogItem, 
        on_delete=models.CASCADE,
        related_name='in_packages',
        verbose_name=_('item')
    )
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    
    class Meta:
        verbose_name = _('package item')
        verbose_name_plural = _('package items')
        unique_together = [['package', 'item']]
    
    def __str__(self):
        return f"{self.package.catalog_item.name} - {self.item.name} x{self.quantity}"