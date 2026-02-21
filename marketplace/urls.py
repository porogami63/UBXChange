from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.home, name='home'),
    path('listings/', views.listing_list, name='listing_list'),
    path('listings/<int:pk>/', views.listing_detail, name='listing_detail'),
    path('listings/create/', views.listing_create, name='listing_create'),
    path('listings/<int:pk>/edit/', views.listing_edit, name='listing_edit'),
    path('listings/<int:pk>/delete/', views.listing_delete, name='listing_delete'),
    path('listings/<int:pk>/sold/', views.listing_mark_sold, name='listing_mark_sold'),
    path('listings/<int:pk>/buy/', views.initiate_purchase, name='initiate_purchase'),
    path('my-listings/', views.my_listings, name='my_listings'),
    path('favorites/', views.favorites_list, name='favorites'),
    path('listings/<int:pk>/favorite/', views.favorite_toggle, name='favorite_toggle'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('messages/', views.inbox, name='inbox'),
    path('messages/<int:pk>/', views.conversation_view, name='conversation'),
    path('listings/<int:pk>/message/', views.message_send, name='message_send'),
    path('transactions/<int:transaction_id>/', views.transaction_detail, name='transaction_detail'),
    path('transactions/<int:transaction_id>/confirm/', views.confirm_transaction, name='confirm_transaction'),
    path('transactions/<int:transaction_id>/complete/', views.complete_transaction, name='complete_transaction'),
    path('forum/', views.forum_index, name='forum'),
    path('forum/new/', views.forum_create_post, name='forum_create'),
    path('forum/<int:pk>/', views.forum_post_detail, name='forum_post'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('user/<str:username>/', views.public_profile_view, name='public_profile'),
    path('user/<str:username>/review/', views.leave_review, name='leave_review'),
]
