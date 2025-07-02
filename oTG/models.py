from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.timezone import now 
from django.dispatch import receiver
from django.db.models.signals import post_save
from uuid import uuid4
from django.utils import timezone
from .services.eventbrite_api import create_eventbrite_event




#  Custom User Model
class User(AbstractUser):
    first_name = models.CharField(max_length=13)
    email = models.EmailField(unique=True)
    nationality = models.CharField(max_length=50, default='Pakistani')
    city = models.CharField(max_length=50, default='Unknown')
    postal_address = models.CharField(max_length=255, default='Not provided')
    mobile_number = models.CharField(max_length=15, unique=True, default='0000000000')
    
    preferred_travel_season = models.CharField(max_length=20, choices=[
        ('summer', 'Summer'), ('winter', 'Winter'), ('spring', 'Spring'), ('autumn', 'Autumn')
    ], default='summer')

    preferred_travel_type = models.CharField(max_length=20, choices=[
        ('adventure', 'Adventure'), 
        ('hiking', 'Hiking'), 
        ('beach', 'Beach'),  
        ('cultural', 'Cultural'),
        ('luxury', 'Luxury')  
    ], default='adventure')

    age_range = models.CharField(max_length=10, choices=[
        ('18-25', '18-25'), ('26-35', '26-35'), ('36-50', '36-50'), ('51+', '51+')
    ], default='18-25')

    budget_range = models.CharField(max_length=10, choices=[
        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High')
    ], default='medium')

    profile_pic = models.ImageField(upload_to='core/profile_pics/', blank=True, null=True)

    groups = models.ManyToManyField(Group, related_name="custom_user_set", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)
    def get_trip_count(self):
        return self.trips.count()
        
    def get_review_count(self):
        return review.objects.filter(user=self).count()
        
    def get_photo_count(self):
        return self.uploaded_photos.count()
        
    def get_favorite_season(self):
        """Returns the season the user has created the most trips for"""
        season_counts = self.trips.values('destination__season').annotate(
            count=models.Count('destination__season')
        ).order_by('-count')
        return season_counts[0]['destination__season'] if season_counts else None
    
    def get_favorite_travel_type(self):
        """Returns the travel type the user has created the most trips for"""
        type_counts = self.trips.values('destination__travel_type').annotate(
            count=models.Count('destination__travel_type')
        ).order_by('-count')
        return type_counts[0]['destination__travel_type'] if type_counts else None
    class Meta:
        db_table = "core_user"  #   Fix: Properly indented Meta class

    def __str__(self):
        return self.username

   
#   Destination Model

class Destination(models.Model):
    name = models.CharField(max_length=255)  
    description = models.TextField()
    location = models.CharField(max_length=255)  
    image = models.ImageField(upload_to='destinations/', blank=True, null=True)

    season = models.CharField(max_length=20, choices=[
        ('summer', 'Summer'), ('winter', 'Winter'), ('spring', 'Spring'), ('autumn', 'Autumn')
    ], default='summer')

    travel_type = models.CharField(max_length=20, choices=[
        ('adventure', 'Adventure'), ('hiking', 'Hiking'), ('beach', 'Beach'), ('cultural', 'Cultural'), ('luxury', 'Luxury')
    ], default='adventure')

    budget_range = models.CharField(max_length=10, choices=[
        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High')
    ], default='medium')
    longitude=models.FloatField(default=0.0)
    latitude=models.FloatField(default=0.0)
    is_popular = models.BooleanField(default=False) 
    
    def __str__(self):
        return self.name
    


#   Activity Model
class Activity(models.Model):
    name = models.CharField(max_length=255)  
    description = models.TextField(default='No description available')
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)  #   Allow null values

    def __str__(self):
        return self.name

    
@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    if created:
        UserPreference.objects.create(
            user=instance,
            season=instance.preferred_travel_season,
            activity_type=instance.preferred_travel_type
        )    

#   User Preferences Model
class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default="Default Preference")  #   Added default name
    season = models.CharField(max_length=20, choices=[
        ('summer', 'Summer'), ('winter', 'Winter'), ('spring', 'Spring'), ('autumn', 'Autumn')
    ], default='summer')
    activity_type = models.CharField(max_length=20, choices=[
        ('adventure', 'Adventure'), ('hiking', 'Hiking'), ('beach', 'Beach'), ('cultural', 'Cultural'), ('luxury', 'Luxury')
    ], default='adventure')  #   Added 'hiking'  
    activities = models.ManyToManyField(Activity, blank=True)  #   Store multiple activities
    date = models.DateField(default=now)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, null=True, blank=True)
    budget = models.CharField(max_length=10, choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')], default='Medium')
    city = models.CharField(max_length=50, default='Unknown')
    description = models.TextField(default="No description provided")  #   Added default description
    


    def __str__(self):
        return f"{self.name} - ({self.season}, {self.activity_type})"


def generate_ticket_code():
    return uuid4().hex.upper()


class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    max_attendees = models.PositiveIntegerField(default=50)
    location = models.CharField(max_length=255)

    event_type = models.CharField(max_length=20, choices=[
        ('adventure', 'Adventure'), ('hiking', 'Hiking'), ('beach', 'Beach'),
        ('cultural', 'Cultural'), ('luxury', 'Luxury')
    ], default='adventure')

    season = models.CharField(max_length=20, choices=[
        ('summer', 'Summer'), ('winter', 'Winter'), ('spring', 'Spring'), ('autumn', 'Autumn')
    ], default='summer')

    image = models.ImageField(upload_to='events/', blank=True, null=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    booking_url = models.URLField(blank=True, null=True)

    def generate_booking_url(self):
        print(f"🎯 Creating Eventbrite event for: {self.title}")
        return create_eventbrite_event(self)  # uses real Eventbrite API

    def save(self, *args, **kwargs):
        creating = self._state.adding  # This line must be inside the method
        super().save(*args, **kwargs)

    # Only generate booking URL after initial save
        if creating and not self.booking_url:
            self.booking_url = self.generate_booking_url()
            super().save(update_fields=["booking_url"])



    def __str__(self):
        return self.title

    def spots_left(self):
        try:
            return self.max_attendees - self.registrations.count()
        except TypeError:
            return 0  # Or log the issue for debugging


class EventRegistration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    timestamp = models.DateTimeField(auto_now_add=True)
    ticket_code = models.CharField(
        max_length=50,
        unique=True,
        default=generate_ticket_code  # ✅ safe, serializable
    )

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user.username} → {self.event.title}"

    #  double-check ticket_code uniqueness during save (very rare cases)
    def save(self, *args, **kwargs):
        if not self.ticket_code:
            while True:
                code = generate_ticket_code()
                if not EventRegistration.objects.filter(ticket_code=code).exists():
                    self.ticket_code = code
                    break
        super().save(*args, **kwargs)



#   Travel Tips Model
class TravelTip(models.Model):
    Tips_Choice=[
        ('adventure', 'Adventure'),
        ('hiking', 'Hiking'),
        ('beach', 'Beach'),
        ('cultural', 'Cultural'),
        ('luxury', 'Luxury'),
    ]
    title = models.CharField(
        max_length=255,
        choices=Tips_Choice,
        default='adventure'
    )  #   Added default title
    content = models.TextField(default='No content available')  #   Added default content
    created_at = models.DateTimeField(auto_now_add=True)
    reddit_post_url = models.URLField(blank=True, null=True)
    
    
    
    def __str__(self):
        return self.title

#   Trip Model (Includes Destination + Activities)
class Trip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')

    title = models.CharField(max_length=100, default='My Trip')  # Prevent null issue
    start_date = models.DateField(default=timezone.now)  # Set default instead of auto_now_add
    end_date = models.DateField(default=timezone.now)    # Same here

    destination = models.ForeignKey('Destination', on_delete=models.CASCADE, related_name='trips')
    accommodation = models.TextField(blank=True, null=True)
    activities = models.TextField(blank=True, null=True)

    is_shared = models.BooleanField(default=False)
    share_link = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} - {self.user.username}"




#   Notification Model (For Updates)
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255, default='no message')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)


    def __str__(self):
        return f"Notification for {self.user.username}"


class  review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.IntegerField(default=5)  # Rating from 1 to 5
    comment = models.TextField()
    likes = models.ManyToManyField(User, related_name='liked_reviews', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def likes_count(self):
        return self.likes.count()
    
    def __str__(self):
        return f"{self.user.username} - {self.destination.name} ({self.rating}/5)"
 
class PhotoInteraction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="uploaded_photos")
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='photos', null=True, blank=True)

    image = models.ImageField(upload_to='destination_photos/')
    caption = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_photos', blank=True)

    def total_likes(self):
        return self.likes.count()


class PhotoComment(models.Model):
    photo = models.ForeignKey(PhotoInteraction, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    commented_at = models.DateTimeField(auto_now_add=True)    