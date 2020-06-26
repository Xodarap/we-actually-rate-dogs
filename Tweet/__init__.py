import logging
import azure.functions as func
import tweepy
import requests
import re
import os

auth = tweepy.OAuthHandler(os.environ['tw1'], os.environ['tw2'])
auth.set_access_token(os.environ['tw3'], os.environ['tw4'])
api = tweepy.API(auth)

def process_image(status):
    url = status.entities['media'][0]['media_url']
    r = requests.get(url = url)
    post_url = 'https://tiktokhot.azurewebsites.net/api/classify?code=WKdDWUMfuFd8k/YKntvMhQC1uOTxpxGuEEOuEZ36XaRg0FidnazwNg=='
    resp = requests.post(post_url, files = {'btw_test': r.content} )
    return resp.json()

def post_tweet(rating, orig_id):
    val = round(rating['score'],2)
    message = f'@dog_rates: This dog is actually {val}/5'
    api.update_status(message, in_reply_to_status_id = orig_id)
    return func.HttpResponse(f'Tweet posted: {message}')

def filter_tweet(status):
    if (not 'media' in status.entities) or len(status.entities['media']) == 0:
        return (False, func.HttpResponse(f"No image attached"))
    if not re.search('.*(\d\/\d\d).*', status.full_text):
        return (False, func.HttpResponse(f"Not a rating tweet"))
    if 'urls' in status.entities and len(status.entities['urls']) > 0:
        for url in status.entities['urls']:
            if re.search('.*gofundme.*', url['expanded_url']):
                return (False, func.HttpResponse(f"Go fund me"))
    return (True, None)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    tweet_id = req.params.get('tweet_id')
    logging.info(f'Tweet id: {tweet_id}.')    
    try:
        status = api.get_status(tweet_id, include_entities = True, tweet_mode='extended')
        (valid, resp) = filter_tweet(status)
        if not valid:
            return resp
        response = process_image(status)
        if response is None:
            return func.HttpResponse(f"No image attached")
        return post_tweet(response, tweet_id)
    except Exception as e:
        logging.error(f'btw: {e}')
        raise e
