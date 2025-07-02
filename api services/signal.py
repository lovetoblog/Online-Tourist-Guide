from .services.eventbrite_api import create_eventbrite_event

@receiver(post_save, sender=Event)
def generate_booking_url(sender, instance, created, **kwargs):
    if created and not instance.booking_url:
        try:
            eventbrite_url = create_eventbrite_event(instance)
            instance.booking_url = eventbrite_url
            instance.save()
        except Exception as e:
            print("Eventbrite error:", e)
