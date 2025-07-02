import requests
from django.conf import settings

ORG_ID = "2709155626541"  # 👈 Your real org ID

def create_eventbrite_event(event):
    url = f"https://www.eventbriteapi.com/v3/organizations/{ORG_ID}/events/"
    
    headers = {
        "Authorization": f"Bearer {settings.EVENTBRITE_API['OAUTH_TOKEN']}",
        "Content-Type": "application/json",
    }

    data = {
        "event": {
            "name": {
                "html": event.title
            },
            "description": {
                "html": event.description or "No description"
            },
            "start": {
                "utc": f"{event.start_date}T09:00:00Z",
                "timezone": "UTC"
            },
            "end": {
                "utc": f"{event.end_date}T17:00:00Z",
                "timezone": "UTC"
            },
            "currency": "USD",
            "online_event": True
        }
    }

    response = requests.post(url, json=data, headers=headers)

    # Accept both 200 and 201 as success codes
    if response.status_code not in [200, 201]:
        raise Exception(f" Failed to create event: {response.status_code} - {response.text}")

    # You can choose to return either the ID or URL based on your needs
    response_data = response.json()
    return response_data.get("url") or f"https://www.eventbrite.com/e/{response_data.get('id')}"