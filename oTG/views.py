from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .form import CustomUserCreationForm, LoginForm ,UserProfileForm ,FeedbackForm, TripForm, PhotoUploadForm
from django.contrib.auth import get_user_model
import logging
from django.conf import settings
from .models import  Trip,Destination,TravelTip , Notification,Activity,UserPreference ,Event, review ,PhotoInteraction,PhotoComment,EventRegistration
from django.db.models import Count, Avg, Sum, F, Q
from django.db.models.functions import ExtractMonth, ExtractYear, TruncMonth
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse  
from django.db.utils import IntegrityError
from django.http import HttpResponseBadRequest
from .socialmedia_utlis import post_to_reddit
from django.http import HttpResponseForbidden
import praw
import json
from django.conf import settings
from django.views.decorators.http import require_POST
import uuid
from django.utils import timezone

User = get_user_model()  # Use Django's user model

from datetime import date

def home(request):
    popular_destinations = Destination.objects.filter(is_popular=True)
    all_photos = PhotoInteraction.objects.all().order_by('uploaded_at')[:9]
    events = Event.objects.filter(start_date__gte=date.today()).order_by('title')[:6]
    tips = TravelTip.objects.all().order_by('-created_at')[:4]
    
   
    
    return render(request, 'core/home.html', {
        'popular_destinations': popular_destinations,
        'all_photos': all_photos,
        
        'events': events,
        'tips': tips,
    })

def signup_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST,request=request)
        if form.is_valid():
            username = form.cleaned_data['username']
            print(form.cleaned_data)
            
            #   Check if the username is already taken
            if User.objects.filter(username=username).exists():
                form.add_error('username', 'This username is already taken. Please choose another one.')
            else:
                try:
                    user = form.save()
                    login(request, user) 
                    return redirect('dashboard')  #   Redirect after successful signup
                except IntegrityError:
                    form.add_error(None, "An error occurred while saving. Please try again.")
                    
    else:
        form = CustomUserCreationForm(request=request)
    
    return render(request, "core/signup.html", {"form": form})

def login_view(request):
    form = LoginForm(request, data=request.POST or None)  #   Pass request properly

    if request.method == "POST":
        if form.is_valid():
            user = form.cleaned_data["user"]  #   Get authenticated user
            login(request, user)  #   Log in user
            messages.success(request, "Login successful!")
            return redirect("dashboard")  #   Redirect to dashboard
        else:
            messages.error(request, "Invalid credentials. Please try again.")

    return render(request, "core/login.html", {"form": form})  #   Pass form
  #   Pass form 

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG) 
@login_required(login_url='login')
def dashboard(request):
    """Display personalized recommendations based on user preferences."""
    user = request.user

    #   Fetch user preferences or create default
    user_preferences, created = UserPreference.objects.get_or_create(user=user)
    preferred_season = user_preferences.season
    preferred_type = user_preferences.activity_type

    #   Debugging: Check user preferences
    logger.debug(f"Dashboard Loaded -> Season: {preferred_season}, Type: {preferred_type}")

    #   Fetch matching destinations
    recommended_destinations = Destination.objects.filter(
        Q(season=preferred_season) & Q(travel_type=preferred_type)& Q(latitude__isnull=False) & Q(longitude__isnull=False)  # Ensure it matches both!
    ).distinct()

    #   Fetch matching events
    recommended_events = Event.objects.filter(
        Q(event_type=preferred_type) & Q(season=preferred_season)  
    ).distinct()

    #   Fetch matching travel tips
    travel_tips = TravelTip.objects.filter(
        Q(title__icontains=preferred_type) | Q(title__icontains=preferred_season)
    ).distinct()

    #   Pass updated recommendations to the template
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()

    #   Debugging
    print(f"DEBUG: Unread Count: {unread_count}")
    for notif in notifications:
        print(f"DEBUG: Notification -> {notif.message}, Read: {notif.is_read}")
    
    # Filter only recommended destinations that have latitude & longitude
    destinations_with_coordinates = recommended_destinations.exclude(latitude=None, longitude=None)
    
    photos = PhotoInteraction.objects.all().order_by('-uploaded_at')
    
    feedback = review.objects.filter(destination__in=recommended_destinations).order_by("-created_at")
    # Calculate the average rating for each destination
    for destination in recommended_destinations:
        avg_rating = review.objects.filter(destination=destination).aggregate(Avg('rating'))['rating__avg']
        destination.average_rating = round(avg_rating, 1) if avg_rating else 0  # Round to 1 decimal place
 
    context = {
        'user': user,
        'preferred_season': preferred_season,
        'preferred_type': preferred_type,
        'recommended_destinations': recommended_destinations,
        'recommended_events': recommended_events,
        'travel_tips': travel_tips,
        'notifications':notifications,
        'unread_count ':unread_count ,
        'feedback':feedback,
        'photos':photos,
    }

    return render(request, 'core/dashboard.html', context)




@login_required(login_url='login')
def edit_profile(request):
    """Allow users to update travel preferences using a Django form."""
    user = request.user

    # Fetch user preferences or create if not exists
    user_preferences, created = UserPreference.objects.get_or_create(user=user)
    
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=user_preferences)
        if form.is_valid():
            # Save User model fields separately
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.city = form.cleaned_data['city']
            user.save()  # Save User model
            
            form.save()  # Save UserPreference model
            user.refresh_from_db()
            return redirect('dashboard')  # Reload dashboard with updated recommendations

    else:
        form = UserProfileForm(instance=user_preferences ,user=user)

    return render(request, 'core/edit_profile.html', {'form': form})

@login_required(login_url='login')
def mark_notifications_as_read(request):
    """Marks all unread notifications as read when user clicks the bell icon."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications have been marked as read.")
    return redirect('dashboard')

def user_logout(request):
    
    """Logout user and redirect to login page."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    request.session.flush() 
    return redirect('login')


@login_required
def personal_data(request):
    user = request.user  # Get logged-in user

    #   Fetch latest UserPreference data
    user_preferences, created = UserPreference.objects.get_or_create(user=user)

    context = {
        'user': user,
        'user_preferences': user_preferences,  # Pass the correct preferences
    }
    return render(request, 'core/personal_data.html', context)

@login_required
def unread_count(request):
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread_count': unread_count})

def post_to_reddit_view(request, travel_tip_id):
    """Handles the Reddit posting ."""
    logger.info(f"Received request to post TravelTip ID {travel_tip_id} to Reddit.")

    #  Ensure travel_tip exists
    travel_tip = get_object_or_404(TravelTip, id=travel_tip_id)

    #  Ensure request is via AJAX or GET
    if request.method != "GET":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

    #  Debugging logs
    logger.info(f" Found TravelTip: {travel_tip.title}")

    #  Post to Reddit
    reddit_url = post_to_reddit(travel_tip.id)

    # Error handling
    if "Error" in reddit_url:
        logger.error(f" Failed to post to Reddit: {reddit_url}")
        return JsonResponse({"status": "error", "message": reddit_url}, status=400)

    #  Store Reddit post URL in the database
    travel_tip.reddit_post_url = reddit_url
    travel_tip.save()

    #Create admin panel link
    admin_link = f"http://127.0.0.1:8000/admin/core/traveltip/{travel_tip.id}/"

    #  Success Response
    return JsonResponse({
        "status": "posted successfully",
        "reddit_url": reddit_url,
        "admin_link": admin_link
    })

# map integration according to destination 
def map_view(request, destination_id):  
    """Display a map with the selected destination's location."""
    destination = get_object_or_404(Destination, id=destination_id)
    feedbacks = review.objects.filter(destination=destination).order_by("-created_at")  # Get latest reviews

    form = FeedbackForm()  # Feedback form
    
    return render(request, "core/destination_map.html", {
        "destination": destination,
        "feedbacks": feedbacks,
        "form": form
    })

@login_required
@require_POST
def delete_review(request, review_id):
    try:
        user_review = review.objects.get(pk=review_id, user=request.user)
        destination_id = user_review.destination.id  # save before delete
        user_review.delete()
        messages.success(request, 'Review deleted successfully!')
        return redirect('destination_map', destination_id=destination_id)
    except review.DoesNotExist:
        messages.error(request, 'Review not found')
        # Redirect to a fallback page, adjust as needed
        return redirect('destination_map', destination_id=destination_id)
    
@login_required
def submit_feedback(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id)

    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.destination = destination
            feedback.save()

            return JsonResponse({
                "success": True,
                "username": feedback.user.username,  
                "rating": feedback.rating,
                "comment": feedback.comment,
                "date": feedback.created_at.strftime('%Y-%m-%d %H:%M')  # Format date
            })
    
    return JsonResponse({"success": False})
    
# create travel trip by user 
@login_required
def create_trip(request, destination_id):
    destination = get_object_or_404(Destination, pk=destination_id)
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.destination = destination
            trip.user = request.user  # Assuming you have user authentication
            trip.save()
            messages.success(request, f"Trip to {destination.name} created successfully!")
            return redirect('trip_detail', trip_id=trip.id)  # Redirect to the trip detail page
        else:
            messages.error(request, "There was an error creating the trip. Please correct the form below.")
    else:
        form = TripForm(initial={'destination': destination})

    context = {
        'destination': destination,
        'form': form,
    }
    return render(request, 'core/create_trip.html', context)

@login_required
def user_trips(request):
    trips = Trip.objects.filter(user=request.user)
    return render(request, 'core/user_trip.html', {'trips': trips})

@login_required
def trip_detail(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    other_trips = Trip.objects.filter(user=request.user)
    return render(request, 'core/trip_detail.html', {
        'trip': trip,
        'other_trips': other_trips,
        'request': request,  # Pass the request object to the template
    })
@login_required
def edit_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    if request.method == 'POST':
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            form.save()
            messages.success(request, 'Trip updated successfully!')
            return redirect('user_trips')
    else:
        form = TripForm(instance=trip)
    return render(request, 'core/edit_trip.html', {'form': form, 'destination': trip.destination})

def delete_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    
    if trip.user != request.user:
        return HttpResponseForbidden("You are not allowed to delete this trip.")
    
    if request.method == 'POST':
        trip.delete()
        messages.success(request, 'Trip deleted successfully.')
        return redirect('user_trips')


@login_required
def share_trip_to_reddit(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)

    if trip.is_shared:
        messages.info(request, "This trip has already been shared on Reddit.")
        return redirect("trip_detail", trip_id=trip.id)

    reddit = praw.Reddit(
        client_id=settings.REDDIT_API["REDDIT_CLIENT_ID"],
        client_secret=settings.REDDIT_API["REDDIT_CLIENT_SECRET"],
        username=settings.REDDIT_API["REDDIT_USERNAME"],
        password=settings.REDDIT_API["REDDIT_PASSWORD"],
        user_agent=settings.REDDIT_API["REDDIT_USER_AGENT"],
    )

    try:
        subreddit = reddit.subreddit("test")  # Change to your actual subreddit
        title = f"My Trip to {trip.destination.name} – {trip.title}"
        body = (
            f"**Trip Details**\n"
            f"**Start Date**: {trip.start_date}\n"
            f"**End Date**: {trip.end_date}\n"
            f"**Activities**: {trip.activities or 'N/A'}\n"
            f"**Accommodation**: {trip.accommodation or 'N/A'}\n"
        )

        post = subreddit.submit(title, selftext=body)

        # Save post URL and shared status
        trip.is_shared = True
        trip.share_link= post.url
        trip.save()

        messages.success(request, "Trip shared successfully on Reddit!")
        return redirect("trip_detail", trip_id=trip.id)

    except Exception as e:
        print("Reddit share failed:", e)
        messages.error(request, "Something went wrong while sharing the trip.")
        return redirect("trip_detail", trip_id=trip.id)


@login_required
def photo_wall(request):
    my_photos = PhotoInteraction.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'core/photo_wall.html', {'photos': my_photos})

@login_required
def upload_photo(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)

    if request.method == 'POST':
        image = request.FILES.get('image')
        caption = request.POST.get('caption', '')

        if image:
            PhotoInteraction.objects.create(
                user=request.user,
                trip=trip,
                image=image,
                caption=caption
            )
            return redirect('photo_wall')  # or home

    return render(request, 'core/userupload_dest.html', {'trip': trip})

@require_POST
@login_required
def like_photo(request, photo_id):
    photo = PhotoInteraction.objects.get(id=photo_id)
    if request.user in photo.likes.all():
        photo.likes.remove(request.user)
    else:
        photo.likes.add(request.user)
    return redirect('home')

@require_POST
@login_required
def comment_photo(request, photo_id):
    comment_text = request.POST.get('comment')
    photo = PhotoInteraction.objects.get(id=photo_id)
    if comment_text:
        PhotoComment.objects.create(user=request.user, photo=photo, comment=comment_text)
    return redirect('home')


@login_required
def delete_photo(request, photo_id):
    photo = get_object_or_404(PhotoInteraction, id=photo_id)

    if request.user == photo.user:
        photo.delete()
        messages.success(request, "Photo deleted successfully.")
    else:
        messages.error(request, "You do not have permission to delete this photo.")

    return redirect('dashboard')  # 

@login_required
def event_detail_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Check if current user has a booking for this event
    registration = EventRegistration.objects.filter(user=request.user, event=event).first()
     # Get upcoming events (e.g., events starting from today)
    

    return render(request, 'core/event_detail.html', {
        'event': event,
        'registration': registration,
        
    })

@login_required
def bookings_view(request):
    user = request.user  # Get the current logged-in user
    
    # Fetch all events
    all_events = Event.objects.all()

    # Fetch events that the current user has booked
    booked_events = EventRegistration.objects.filter(user=user).values_list('event', flat=True)
    
    # Create two lists: one for booked events, one for non-booked events
    booked_registrations = EventRegistration.objects.select_related('event').filter(user=user)

    booked_events_list = [
        {
        'event': reg.event,
        'ticket_code': reg.ticket_code
    }
    for reg in booked_registrations
    ]
    non_booked_events_list = all_events.exclude(id__in=booked_events)
    
    calendar_events = []
    
    for e in all_events:
        calendar_events.append({
            'id': e.id,
            'title': e.title,
            'start': e.start_date.strftime("%Y-%m-%d"),
            'end': e.end_date.strftime("%Y-%m-%d") if e.end_date else None,
            'color': '#ff9800' if e.event_type == 'adventure' else 
                     '#4caf50' if e.event_type == 'hiking' else
                     '#03a9f4' if e.event_type == 'beach' else
                     '#9c27b0' if e.event_type == 'cultural' else
                     '#f44336' if e.event_type == 'luxury' else '#607d8b'
        })

    context = {
        'booked_events_list': booked_events_list,
        'non_booked_events_list': non_booked_events_list,
        'calendar_events': json.dumps(calendar_events)  # Pass events as JSON
    }
    
    return render(request, 'core/bookings_list.html', context)


@login_required
def book_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if event.spots_left() <= 0:
        messages.error(request, "No spots left for this event.")
        return redirect('dashboard')

    reg, created = EventRegistration.objects.get_or_create(
        user=request.user,
        event=event,
        defaults={'ticket_code': uuid.uuid4().hex.upper()}
    )

    if not created:
        messages.info(request, "You already booked this event.")
        return redirect('dashboard')

    messages.success(request, f"Booking successful! Your ticket: {reg.ticket_code}")
    return render(request, 'core/booking_success.html', {'registration': reg})



@login_required
def user_analytics(request):
    """
    Provides comprehensive analytics dashboard for the user showing their travel patterns,
    engagement metrics, and personalized insights.
    """
    user = request.user
    current_date = timezone.now()
    
    # Basic user stats
    user_stats = {
        'trip_count': user.get_trip_count(),
        'review_count': user.get_review_count(),
        'photo_count': user.get_photo_count(),
        'event_registrations': EventRegistration.objects.filter(user=user).count(),
        'favorite_season': user.get_favorite_season() or user.preferred_travel_season,
        'favorite_travel_type': user.get_favorite_travel_type() or user.preferred_travel_type,
    }
    
    # Time-based analytics
    # Get trips per month for the last 12 months
    last_year = current_date - timedelta(days=365)
    trips_by_month = Trip.objects.filter(
        user=user, 
        created_at__gte=last_year
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Format for chart.js
    months_labels = []
    trips_data = []
    
    for entry in trips_by_month:
        months_labels.append(entry['month'].strftime('%b %Y'))
        trips_data.append(entry['count'])
    
    # Travel patterns by season
    season_data = Trip.objects.filter(user=user).values(
        'destination__season'
    ).annotate(
        count=Count('id')
    ).order_by('destination__season')
    
    season_labels = [item['destination__season'] for item in season_data]
    season_counts = [item['count'] for item in season_data]
    
    # Travel patterns by type
    type_data = Trip.objects.filter(user=user).values(
        'destination__travel_type'
    ).annotate(
        count=Count('id')
    ).order_by('destination__travel_type')
    
    type_labels = [item['destination__travel_type'] for item in type_data]
    type_counts = [item['count'] for item in type_data]
    
    # Engagement metrics
    engagement_data = {
        'photo_likes_received': PhotoInteraction.objects.filter(
            user=user
        ).aggregate(
            total_likes=Sum('likes')
        )['total_likes'] or 0,
        'reviews_submitted': review.objects.filter(user=user).count(),
        'photos_uploaded': PhotoInteraction.objects.filter(user=user).count(),
        'events_attended': EventRegistration.objects.filter(user=user).count(),
    }
    
    # Budget analysis
    budget_data = Trip.objects.filter(user=user).values(
        'destination__budget_range'
    ).annotate(
        count=Count('id')
    ).order_by('destination__budget_range')
    
    budget_labels = [item['destination__budget_range'] for item in budget_data]
    budget_counts = [item['count'] for item in budget_data]
    
    # Top-rated destinations by this user
    top_rated_destinations = review.objects.filter(
        user=user
    ).order_by('-rating')[:5].select_related('destination')
    
    # Most visited destinations
    most_visited = Trip.objects.filter(user=user).values(
        'destination__name', 'destination__id'
    ).annotate(
        visit_count=Count('destination')
    ).order_by('-visit_count')[:5]
    
    # Personalized recommendations based on analytics
    # Find destinations similar to what user has highly rated or visited multiple times
    favorite_destination_types = review.objects.filter(
        user=user, rating__gte=4
    ).values_list('destination__travel_type', flat=True)
    
    if favorite_destination_types:
        recommended_destinations = Destination.objects.filter(
            travel_type__in=favorite_destination_types,
            season=user.preferred_travel_season
        ).exclude(
            id__in=Trip.objects.filter(user=user).values_list('destination_id', flat=True)
        )[:5]
    else:
        recommended_destinations = Destination.objects.filter(
            season=user.preferred_travel_season,
            travel_type=user.preferred_travel_type
        )[:5]
    
    # Format all chart data for JavaScript
    chart_data = {
        'trips_by_month': {
            'labels': months_labels,
            'data': trips_data
        },
        'season_breakdown': {
            'labels': season_labels,
            'data': season_counts
        },
        'type_breakdown': {
            'labels': type_labels,
            'data': type_counts
        },
        'budget_breakdown': {
            'labels': budget_labels,
            'data': budget_counts
        }
    }
    # print(chart_data)
    return render(request, 'core/user_analytics.html', {
        'user': user,
        'user_stats': user_stats,
        'chart_data': json.dumps(chart_data),
        'engagement_data': engagement_data,
        'top_rated_destinations': top_rated_destinations,
        'most_visited': most_visited,
        'recommended_destinations': recommended_destinations,
    })
