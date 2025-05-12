from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'title')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'title')
    list_filter = ('title',)
    
    fieldsets = (
        ('Kullanıcı Bilgileri', {
            'fields': ('user',)
        }),
        ('Ünvan Bilgisi', {
            'fields': ('title',)
        }),
    )
