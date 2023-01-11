import firebase_admin
from firebase_admin import credentials, firestore
from scraper import Scraper
import pygeohash
import requests
import threading
from config import API_KEY

class FirebaseProcessor:
    """

    Handler to upload restaurant data to Firebase

    Use the 'start' method to begin processing.

    """

    RESTAURANTS_PER_PAGE = 10

    def __init__(self, page_scrape_amount):
        self._page_scrape_amount = page_scrape_amount
        self._db = self._init_firebase()
        self.restaurants_scraped_data, self.restaurants_scraped_url_data = self._get_data()

        self.thread_locks = []
        for i in range(self._page_scrape_amount):
            self.thread_locks.append(threading.Lock())

    def start(self):

        for page_number in range(self._page_scrape_amount):
            start = page_number*FirebaseProcessor.RESTAURANTS_PER_PAGE
            end = (page_number + 1)*FirebaseProcessor.RESTAURANTS_PER_PAGE
            t = threading.Thread(target=self._process_data, args=(start, end, page_number))
            t.start()

        for thread in threading.enumerate()[1:]:
            thread.join()

        print('Firebase Processor Completed')

    def _init_firebase(self):
        cred = credentials.Certificate('key.json')
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        return db

    def _get_data(self):
        scraper = Scraper(self._page_scrape_amount)
        scraper.start()
        restaurants_scraped_data = scraper.get_data()
        restaurant_scraped_url_data = scraper.get_url_data()

        return restaurants_scraped_data, restaurant_scraped_url_data

    def _get_geo_data(self, address):
        parameters = {'text': address, 'apiKey': API_KEY}
        response = requests.get('https://api.geoapify.com/v1/geocode/search', params=parameters)

        try:
            address_data = response.json()['features'][0]['properties']
            latitude = address_data['lat']
            longitude = address_data['lon']

            geohash = pygeohash.encode(latitude, longitude, precision=10)
        except Exception as e:
            print("The error is", e, "with address", address)
            latitude = None
            longitude = None
            geohash = None

        return latitude, longitude, geohash

    def _process_data(self, start, end, thread_no):
        for restaurant_no in range(start, end):
            restaurant_scraped_data = self.restaurants_scraped_data[restaurant_no]
            address = restaurant_scraped_data['restaurant_address']

            latitude, longitude, geohash = self._get_geo_data(address)

            restaurant_data = {
                'name': restaurant_scraped_data['restaurant_name'],
                'rating': restaurant_scraped_data['restaurant_rating'],
                'url': self.restaurants_scraped_url_data[restaurant_no],
                'address': restaurant_scraped_data['restaurant_address'],
                'price_type': restaurant_scraped_data['price_type'],
                'review_highlights': restaurant_scraped_data['review_highlights'],
                'geohash': geohash,
                'latitude': latitude,
                'longitude': longitude
            }

            self.thread_locks[thread_no].acquire()
            self._db.collection('venues').document().set(restaurant_data)
            self.thread_locks[thread_no].release()

