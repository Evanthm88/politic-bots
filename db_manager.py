from pymongo import MongoClient


def get_db():
    client = MongoClient('localhost:27017')
    db = client.politic_bots
    return db


def do_search(db, query):
    return db.tweets.find(query)


def find_tweets_by_author(db, author_id):
    query = {'type': 'user', 'keyword': author_id}
    return do_search(db, query)


def find_tweets_by_hashtag(db, hashtag):
    query = {'type': 'hashtag', 'keyword': hashtag}
    return do_search(db, query)


def aggregate(db, pipeline):
    return [doc for doc in db.tweets.aggregate(pipeline)]


def get_hashtags_by_movement(db, movement_name):
    pipeline = [
        {
            '$match': {
                'movimiento': {'$eq': movement_name},
                'type': {'$eq': 'hashtag'}
            }
        },
        {
            '$group': {
                '_id': '$keyword',
                'num_tweets': {'$sum': 1}
            }
        },
        {
            '$project': {
                'hastag': '$keyword',
                'count': '$num_tweets'
            }
        },
        {
            '$sort': {'count': -1}
        }
    ]
    return aggregate(db, pipeline)


def get_unique_users_by_movement(db, movement_name):
    # prepare the pipeline
    pipeline = [
        {
            '$match': {
                'movimiento': {'$eq': movement_name}
            }
        },
        {
            '$group': {
                '_id': '$tweet_obj.user.id_str',
                'screen_name': {'$first': '$tweet_obj.user.screen_name'},
                'verified': {'$first': '$tweet_obj.user.verified'},
                'location': {'$first': '$tweet_obj.user.location'},
                'url': {'$first': '$tweet_obj.user.url'},
                'name': {'$first': '$tweet_obj.user.name'},
                'description': {'$first': '$tweet_obj.user.description'},
                'followers': {'$first': '$tweet_obj.user.followers_count'},
                'friends': {'$first': '$tweet_obj.user.friends_count'},
                'created_at': {'$first': '$tweet_obj.user.created_at'},
                'time_zone': {'$first': '$tweet_obj.user.time_zone'},
                'geo_enabled': {'$first': '$tweet_obj.user.geo_enabled'},
                'language': {'$first': '$tweet_obj.user.lang'},
                'default_theme_background': {'$first': '$tweet_obj.user.default_profile'},
                'default_profile_image': {'$first': '$tweet_obj.user.default_profile_image'},
                'favourites_count': {'$last': '$tweet_obj.user.favourites_count'},
                'listed_count': {'$last': '$tweet_obj.user.listed_count'},
                'tweets_count': {'$sum': 1},
                'tweets': {'$push': {'text': '$tweet_obj.text',
                                     'quote':'$tweet_obj.quoted_status_id',
                                     'reply':'$tweet_obj.in_reply_to_status_id_str',
                                     'retweet': '$tweet_obj.retweeted_status.id_str'}}
            }
        },
        {
            '$sort': {'tweets_count': -1}
        }
    ]
    results = aggregate(db, pipeline)
    # calculate the number of rts, rps, and qts
    for result in results:
        ret_tweets = result['tweets']
        rt_count = 0
        qt_count = 0
        rp_count = 0
        for tweet in ret_tweets:
            if 'retweet' in tweet.keys():
                rt_count += 1
            elif 'quote' in tweet.keys():
                qt_count += 1
            elif tweet['reply'] != 'null':
                rp_count += 1
        result['retweets_count'] = rt_count
        result['quotes_count'] = qt_count
        result['replies_count'] = rp_count
        result['original_count'] = result['tweets_count'] - (rt_count+qt_count+rp_count)
    return results


def add_tweet(db, tweet, type_k, keyword, extraction_date, k_metadata):
    '''
        tweet: dictionary, information of the tweet
        type: string, take the value 'user' or 'hashtag'
        keyword: string, contains the text of the handle or hashtag
        extraction_date: string, date (dd/mm/yyyy) when the tweet was collected
        k_metadata: dictionary, metadata about the keyword
    '''
    enriched_tweet = {'type': type_k,
                      'keyword': keyword,
                      'tweet_obj': tweet,
                      'extraction_date': extraction_date}
    enriched_tweet.update(k_metadata)
    return db.tweets.insert(enriched_tweet)

