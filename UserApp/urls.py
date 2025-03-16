from django.urls import path
from . import views  # Import all views from userapp

urlpatterns = [
    # Notes Sharing App URLs
    path('', views.signup, name='signup'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('ViewNotes/', views.ViewNotes, name='ViewNotes'),
    path('pdf/delete/<int:pdf_id>/', views.delete_pdf, name='delete_pdf'),
    path('AboutUs/', views.AboutUs, name='AboutUs'),

    # Chatting App URLs (integrated under /dashboard/chat/)
    path('dashboard/chat/', views.index, name='chat_index'),
    path('dashboard/chat/<str:username>/', views.chat_room, name='chat_room'),
    path('dashboard/chat/get_unread_count/', views.get_unread_count, name='get_unread_count'),

    # Group Chat URLs
    path('dashboard/chat/group/create/', views.create_group, name='create_group'),
    path('dashboard/chat/group/<int:group_id>/', views.group_chat, name='group_chat'),
    path('dashboard/chat/group/<int:group_id>/leave/', views.leave_group, name='leave_group'),
    path('dashboard/chat/group/<int:group_id>/add_members/', views.add_group_members, name='add_group_members')
]
