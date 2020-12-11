from django.contrib import admin
import admin_thumbnails
from mptt.admin import DraggableMPTTAdmin
from .models import *


class ProductImageInline(admin.TabularInline):
    model = Images
    readonly_fields = ('id',)
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'image_tag']
    list_filter = ['category']
    readonly_fields = ('image_tag',)
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductImageInline]


class CategoryAdmin(DraggableMPTTAdmin):
    mptt_indent_field = "title"
    list_display = ('tree_actions', 'indented_title',
                    'related_products_count', 'related_products_cumulative_count')
    list_display_links = ('indented_title',)
    prepopulated_fields = {'slug': ('title',)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Add cumulative product count
        qs = Category.objects.add_related_count(
            qs,
            Product,
            'category',
            'products_cumulative_count',
            cumulative=True)

        # Add non cumulative product count
        qs = Category.objects.add_related_count(qs,
                                                Product,
                                                'category',
                                                'products_count',
                                                cumulative=False)
        return qs

    def related_products_count(self, instance):
        return instance.products_count

    related_products_count.short_description = 'Related products (for this specific category)'

    def related_products_cumulative_count(self, instance):
        return instance.products_cumulative_count

    related_products_cumulative_count.short_description = 'Related products (in tree)'


@admin_thumbnails.thumbnail('image')
class ImagesAdmin(admin.ModelAdmin):
    list_display = ['image', 'title', 'image_thumbnail']


class SettingAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'update_at', 'status']


class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'update_at', 'status']
    readonly_fields = ('name', 'subject', 'email', 'message', 'ip')
    list_filter = ['status']


# Register your models here.
admin.site.register(Customer)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Images, ImagesAdmin)

admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ShippingAddress)

admin.site.register(Setting, SettingAdmin)
admin.site.register(ContactMessage, ContactMessageAdmin)
