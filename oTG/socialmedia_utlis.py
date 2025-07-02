import praw
import logging
from django.conf import settings
from .models import TravelTip

logger = logging.getLogger(__name__)

def post_to_reddit(travel_tip_id):
    """Posts  TravelTip to Reddit and returns the Reddit URL."""
    try:
        logger.info(f" Attempting to post TravelTip ID {travel_tip_id} to Reddit...")

        reddit = praw.Reddit(
            client_id=settings.REDDIT_API["REDDIT_CLIENT_ID"],
            client_secret=settings.REDDIT_API["REDDIT_CLIENT_SECRET"],
            username=settings.REDDIT_API["REDDIT_USERNAME"],
            password=settings.REDDIT_API["REDDIT_PASSWORD"],
            user_agent=settings.REDDIT_API["REDDIT_USER_AGENT"],
            check_for_async=False,
        )

        reddit.user.me()  
        

        travel_tip = TravelTip.objects.get(id=travel_tip_id)
       # print("Logged in as:", reddit.user.me())
        subreddit_name = "test"  
        subreddit = reddit.subreddit(subreddit_name)

        submission = subreddit.submit(
            title=travel_tip.title,
            selftext=travel_tip.content,
        )

        reddit_post_url = submission.url
        logger.info(f"Successfully posted TravelTip ID {travel_tip_id} to Reddit: {reddit_post_url}")

        return reddit_post_url  

    except Exception as e:
        error_message = f" Error posting TravelTip ID {travel_tip_id} to Reddit: {str(e)}"
        logger.error(error_message, exc_info=True)
        return f"Error: {str(e)}"
