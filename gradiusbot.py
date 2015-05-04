import tweepy
import datetime
import time
import internetmademe.markov
from configparser import RawConfigParser
from mention_processing import road_to_10k


class GradiusBot():

    def __init__(self):
        print("Building GradiusBot...")
        config = RawConfigParser()
        config.read('config.cfg')

        #Setup Auth
        consumer_key = config.get('Twitter', 'consumer_key')
        consumer_secret = config.get('Twitter', 'consumer_secret')
        access_token = config.get('Twitter', 'access_token')
        access_token_secret = config.get('Twitter', 'access_token_secret')
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)

        #Setup Config
        self.target = config.get('Config', 'target')
        self.owner = config.get('Config', 'owner')
        self.name = self.api.me().name.lower()

    def get_tweets_in_period(self, seconds):
        now = datetime.datetime.utcnow()
        result_list = []
        next_page = True
        page = 0

        while next_page:
            # print("We're going on to page: " + str(page))
            tweets = self.api.user_timeline(self.target, page=page)

            for tweet in tweets:
                time_difference = now - tweet.created_at
                total_diff = time_difference.seconds + (time_difference.days*86400)
                # print total_diff
                if total_diff > seconds:
                        next_page = False
                else:
                    result_list.append(tweet)

            page += 1

        return result_list

    def markov_tweet_loop(self):
        while True:
            print("Generating tweet...")
            m = internetmademe.markov.Markov()
            tweet = m.generate_sentence(2, "*", 5, 15)
            print("Candidate tweet:", tweet)

            while len(tweet) > 140:
                print("Tweet was too long, generating a new tweet...")
                tweet = m.generate_sentence(2, "*", 5, 15)
                print("Candidate tweet:", tweet)

            print("Updating status...")
            self.api.update_status(status=tweet)
            print("Sleeping for 600s...")
            time.sleep(300)
            print("Sleeping for 300s...")
            time.sleep(150)
            print("Sleeping for 150s...")
            time.sleep(90)
            print("Sleeping for 60s...")
            time.sleep(60)

    def process_mentions(self, max_age):
        mentions = self.recent_mentions(max_age)

        for m in mentions:
            m_lower = m.text.lower()
            message_text = m_lower.replace('@'+self.name, '').strip().split()

            # Owner only functions
            if m.author.name.lower() == self.owner:
                print(message_text)
                if message_text[0] == '!progress':
                    reply = road_to_10k(self.get_tweets_in_period(86400), m.author)
                    self.api.update_status(reply, m.id)

    def recent_mentions(self, max_age):
        now = datetime.datetime.utcnow()
        result_list = []
        next_page = True
        page = 0

        while next_page:
            # print("We're going on to page: " + str(page))
            mentions = self.api.mentions_timeline(page=page)

            for tweet in mentions:
                time_difference = now - tweet.created_at
                total_diff = time_difference.seconds + (time_difference.days*86400)
                # print total_diff

                if len(mentions) < 20:
                    next_page = False

                if total_diff > max_age:
                    next_page = False
                else:
                    result_list.append(tweet)

            page += 1

        return result_list

