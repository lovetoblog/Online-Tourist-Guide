from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .socialmedia_utlis import post_to_reddit
from .models import User, Destination, Activity, UserPreference, TravelTip, Trip, Notification ,Event,EventRegistration,review

#   User Admin
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username','first_name', 'email', 'city', 'mobile_number', 'preferred_travel_season')
    list_filter = ('preferred_travel_season', 'preferred_travel_type', 'age_range', 'budget_range')

#   Destination Admin
@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'location','season','image','budget_range','travel_type')
    search_fields = ('name', 'location')

    list_filter = ('season', 'budget_range', 'travel_type')

#   User Preference Admin
@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'season', 'activity_type')
    list_filter = ('season', 'activity_type')
    search_fields = ('name','season')
    readonly_fields = [field.name for field in UserPreference._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'destination', 'rating', 'created_at')
    list_filter = ('destination', 'rating')
    search_fields = ('user', 'comment')
    
#   Travel Tip Admin
@admin.register(TravelTip)
class TravelTipAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'created_at', 'socialshare', 'reddit_link')
    search_fields = ('title', 'content')

    def socialshare(self, obj):
        """Creates a share button to post a TravelTip to Reddit."""
        try:
            share_url = reverse("post_to_reddit", args=[obj.id])
        except Exception as e:
             return f"Error: {e}"
          
        return format_html(
        '''<a href="{}" style="text-decoration: none; display: flex; align-items: center;  padding: 5px 10px; color: black; border-radius: 5px;">
            <img src="https://cdn0.iconfinder.com/data/icons/social-15/200/share-icon-512.png" 
                width="20" height="20" style="margin-right: 5px;" alt="Share on Reddit">
            Share on Reddit
        </a>''',
        share_url
    )
    def reddit_link(self, obj):
        """Shows a link to view the post on Reddit, if available."""
        if obj.reddit_post_url:
            return format_html('<a href="{}" target="_blank">View on Reddit</a>', obj.reddit_post_url)
        return "Not Posted"
    
    reddit_link.short_description = "Reddit Post"
    
    
#   Trip Admin
@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "share_link", "destination", "start_date")
    list_filter = ("share_link", "destination")
    readonly_fields = [field.name for field in Trip._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    

#   Notification Admin
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    
    

# 🔹 Inline: Show EventRegistration within Event Admin
class EventRegistrationInline(admin.TabularInline):
    model = EventRegistration
    extra = 0
    readonly_fields = ('user', 'timestamp', 'ticket_code')
    can_delete = False


# 🔹 Admin: Manage Events
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'max_attendees', 'current_attendance_display', 'spots_left', 'booking_url_display')
    inlines = [EventRegistrationInline]
    readonly_fields = ('booking_url',)

    def current_attendance_display(self, obj):
        return obj.registrations.count()
    current_attendance_display.short_description = "Current Attendance"
    
    def booking_url_display(self, obj):
        if obj.booking_url:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.booking_url, obj.booking_url)
        return "Not generated yet"
admin.site.register(EventRegistration) 
    


    
admin.site.site_header = "OnlineTouristGuide Adminstration"
admin.site.site_title = "OnlineTouristGuide Panel"
admin.site.index_title = "Welcome to OnlineTouristGuide "    