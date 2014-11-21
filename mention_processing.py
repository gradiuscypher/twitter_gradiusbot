import datetime


def road_to_10k(tweet_list, author):
    status_count = author.statuses_count
    tweets_today = len(tweet_list)
    tweets_remaining = 10000 - status_count
    last_day = datetime.datetime(2014, 12, 31)
    today = datetime.datetime.now()
    days_remaining = (last_day - today).days + 1
    tweets_per_day = tweets_remaining / days_remaining
    reply = "@" + author.name + ":\n"
    reply += "Sent: " + str(status_count) + " tweets so far.\n"
    reply += "Sent: " + str(tweets_today) + " tweets today.\n"
    reply += "Remaining: " + str(days_remaining) + " days.\n"
    reply += "Tweets/Day: " + str(tweets_per_day)

    return reply
