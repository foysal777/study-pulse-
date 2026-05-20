from django.contrib.admin import AdminSite
from django.shortcuts import redirect
from django.urls import reverse


class CustomAdminSite(AdminSite):
    """Custom admin site with dashboard redirect"""
    
    def index(self, request, extra_context=None):
        """Redirect admin index to custom dashboard"""
        return redirect('admin_dashboard')


custom_admin_site = CustomAdminSite(name='custom_admin')
