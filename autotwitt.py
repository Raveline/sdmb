def send_tweet(tweet):
    resp = twitter.post('statuses/update.json', data = { 'status' : 'Test' })
    return resp.status
