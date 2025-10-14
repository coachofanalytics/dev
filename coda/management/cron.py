# from django.core.management import call_command
import tweepy
import requests
from management.models import Advertisement

"""

Twitter and Facebook AD management Scripts below

"""


def advertisement():
    """
    This function will post the latest Facebook Ad
    """
    context = Advertisement.objects.all().first()
    apiKey = context.twitter_api_key
    apiSecret = context.twitter_api_secret
    accessToken = context.twitter_access_token
    accessTokenSecret = context.twitter_access_token_secret

    # 3. Create Oauth client and set authentication and create API object
    oauth = tweepy.OAuthHandler(apiKey, apiSecret)
    oauth.set_access_token(accessToken, accessTokenSecret)

    api = tweepy.API(oauth)

    # 4. upload media
    media = api.media_upload(context.image)

    api.update_status(
        status=context.tweet_description,
        media_ids=[context.tweet_media],
    )

    """
        This function will post the latest Facebook Ad
    """

    facebook_page_id = context.facebook_page_id
    access_token = context.facebook_access_token
    url = "https://graph.facebook.com/{}/photos".format(facebook_page_id)
    msg = context.post_description
    image_location = context.image
    payload = {
        "url": image_location,
        "access_token": access_token,
        "message": msg,
    }

    # Send the POST request
    requests.post(url, data=payload)
