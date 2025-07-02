from django.urls import path
from django.conf import settings 
from django.conf.urls.static import static
from . import views


urlpatterns = [
    path('', views.home, name='home'),  # Home Page
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('notifications/read/',views.mark_notifications_as_read, name='mark_notifications_as_read'),
    path('personal-data/', views.personal_data, name='personal_data'),
    path('notifications/unread_count/', views.unread_count, name='unread_count'),
    path('post-to-reddit/<int:travel_tip_id>/', views.post_to_reddit_view, name='post_to_reddit'),
   path('destination-map/<int:destination_id>/', views.map_view, name='destination_map'),
    path("destination/<int:destination_id>/feedback/", views.submit_feedback, name="submit_feedback"),
    path('review/delete/<int:review_id>/', views.delete_review, name='delete_review'),
    
    
    
    path('trips/create/<int:destination_id>/', views.create_trip, name='create_trip'),
    path('my-trips/', views.user_trips, name='user_trips'),
    path('trip/<int:trip_id>/delete/', views.delete_trip, name='delete_trip'),
    path('trips/<int:trip_id>/', views.trip_detail, name='trip_detail'),
    path('trip/<int:trip_id>/edit/', views.edit_trip, name='edit_trip'),
   path('trips/<int:trip_id>/share/', views.share_trip_to_reddit, name='share_trip_on_reddit'),
   path('photo-wall/', views.photo_wall, name='photo_wall'),
   path('trip/<int:trip_id>/upload/', views.upload_photo, name='upload_photo'),

    path('like/<int:photo_id>/', views.like_photo, name='like_photo'),
    path('comment/<int:photo_id>/', views.comment_photo, name='comment_photo'),
    path('delete-photo/<int:photo_id>/', views.delete_photo, name='delete_photo'),
    
    path('bookings/', views.bookings_view, name='bookings_view'),
    path('event/<int:event_id>/view/', views.event_detail_view, name='event_detail'),
    path('book/<int:event_id>/', views.book_event, name='book_event'),
       
     path('analytics/', views.user_analytics, name='user_analytics'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)