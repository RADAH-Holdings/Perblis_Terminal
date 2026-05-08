from django.urls import path

from accounts.views.user_views import me, update_role, upload_document, public_profile

urlpatterns = [
    path('me/', me, name='user-me'),
    path('me/role/', update_role, name='user-role'),
    path('me/documents/', upload_document, name='user-documents'),
    path('<uuid:user_id>/', public_profile, name='user-public-profile'),
]
