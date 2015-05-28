import tweepy
import random
import datetime
import time
from block_io import BlockIo
import internetmademe.markov
from configparser import RawConfigParser
from mention_processing import road_to_10k


class GradiusBot():

    def __init__(self):
        print("Building GradiusBot...")
        config = RawConfigParser()
        self.useful_data = RawConfigParser()
        config.read('config.cfg')

        #Setup Auth
        consumer_key = config.get('Twitter', 'consumer_key')
        consumer_secret = config.get('Twitter', 'consumer_secret')
        access_token = config.get('Twitter', 'access_token')
        access_token_secret = config.get('Twitter', 'access_token_secret')
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)

        #Setup Dogecoin
        blockio_key = config.get('BlockIO', 'key')
        blockio_pin = config.get('BlockIO', 'pin')
        self.blockio_addr = config.get('BlockIO', 'addr')
        self.blockio = BlockIo(blockio_key, blockio_pin)

        #Setup Config
        self.target = config.get('Config', 'target')
        self.owner = config.get('Config', 'owner')
        self.name = self.api.me().name.lower()

    def balance_since_last_tweet(self):
        self.useful_data.read('data.cfg')
        last_time = self.useful_data.get('Data', 'time_since_last_balance')
        balance = 0.0
        temp_time = 0

        transaction_list = self.blockio.get_transactions(type='received', addresses=self.blockio_addr)

        for transaction in transaction_list['data']['txs']:
            if float(transaction['time']) > float(last_time):
                for amounts in transaction['amounts_received']:
                    print("in for amounts")
                    balance += float(amounts['amount'])

            if transaction['time'] > temp_time:
                temp_time = transaction['time']

        self.useful_data.set('Data', 'time_since_last_balance', temp_time)
        print("setting time", temp_time)
        datafile = open('data.cfg', 'w')
        self.useful_data.write(datafile)
        datafile.close()

        return balance

    def fortune_tweet(self):
        m = internetmademe.markov.Markov()
        fortune_starters = [
            'you will',
            'you are',
            'you have',
            "you're",
            'you',
        ]

        starter = random.choice(fortune_starters)
        chain = random.randint(2, 3)

        tweet = m.generate_sentence(chain, starter, 5, 15)

        fortune_message = "I've gotten enough Doge for a fortune!\n"

        while len(tweet) > 100:
            print("Tweet was too long, generating a new tweet...")
            tweet = m.generate_sentence(chain, "*", 5, 15)
            print("Candidate tweet:", tweet)

        print("Updating status...")
        print("Candidate tweet:", fortune_message + tweet)
        self.api.update_status(status=tweet)

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

    def markov_tweet(self):
        chain = random.randint(2, 3)
        print("Generating tweet...")
        m = internetmademe.markov.Markov()
        tweet = m.generate_sentence(chain, "*", 5, 20)
        print("Candidate tweet:", tweet)

        while len(tweet) > 140:
            print("Tweet was too long, generating a new tweet...")
            tweet = m.generate_sentence(chain, "*", 5, 20)
            print("Candidate tweet:", tweet)

        print("Updating status...")
        self.api.update_status(status=tweet)

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

    def run_full_loop(self, talk_chance_percent, sleep_time, fortune_cost=100):
        while True:
            self.useful_data.read('data.cfg')
            remaining_balance = self.useful_data.get('Data', 'balance_remainder')
            current_balance = self.balance_since_last_tweet() + float(remaining_balance)

            is_talking = random.randint(0, 100)

            #Try to talk with something random
            if talk_chance_percent > is_talking:
                print("Triggered talk chance:", talk_chance_percent, ">", is_talking)
                self.markov_tweet()

            #See if you've gotten enough Doge for a fortune
            while current_balance >= fortune_cost:
                current_balance -= fortune_cost
                print("Triggered fortune tweet. Remaining balance:", current_balance)
                self.fortune_tweet()

            self.useful_data.set('Data', 'balance_remainder', current_balance)
            print("keeping remaining balance", current_balance)
            datafile = open('data.cfg', 'w')
            self.useful_data.write(datafile)
            datafile.close()

            time.sleep(sleep_time)
