import requests
from bs4 import BeautifulSoup
import threading


class Scraper:
    """

    Handler to scrape restaurant details off Yelp.

    Use the 'start' method to begin processing.

    Optimised by threading, using 'page_scrape_amount' of threads to scrape each page in parallel.

    """

    RESTAURANT_URL_BASE = "https://www.yelp.com/search?find_desc=Restaurants&find_loc=Sydney+New+South+Wales&start="
    RESTAURANT_CARD_URL_BASE = "https://www.yelp.com"
    RESTAURANTS_PER_PAGE = 10

    def __init__(self, page_scrape_amount):
        self._page_scrape_amount = page_scrape_amount
        self.restaurants_data_list = []
        self.restaurants_url_data_list = []

        self.thread_locks = [] # Contains 'page_scrape_amount' of locks
        for i in range(self._page_scrape_amount):
            self.thread_locks.append(threading.Lock())

    def start(self):
        """Main process to scrape data and initiate threading"""

        for page_number in range(self._page_scrape_amount):
            t = threading.Thread(target=self._website_scraper, args=(page_number, ))
            t.start()

        for thread in threading.enumerate()[1:]:
            thread.join()

    def get_data(self):
        """Getter function to receive restaurant data"""

        return self.restaurants_data_list

    def get_url_data(self):
        """Getter function to recieve url cards of restaurants"""

        return self.restaurants_url_data_list

    def _website_scraper(self, page_number):
        """Data scraper for entire page of website"""

        url = Scraper.RESTAURANT_URL_BASE + str(page_number * Scraper.RESTAURANTS_PER_PAGE)
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        top_restaurants_scrape = soup.find(class_="searchResultsContainer__09f24__EZHb0").ul.contents[
                                    2: 2 + Scraper.RESTAURANTS_PER_PAGE]

        for restaurant_scrape in top_restaurants_scrape:
            self._restaurant_scraper(restaurant_scrape, page_number)

    def _restaurant_scraper(self, restaurant_scrape, page_number):
        """Data scraper for restaurant card"""

        restaurant_card_url = Scraper.RESTAURANT_CARD_URL_BASE + restaurant_scrape.find(class_="css-1egxyvc").a.attrs[
            'href']
        page = requests.get(restaurant_card_url)
        restaurant_card_scrape = BeautifulSoup(page.content, "html.parser")

        restaurant_name = self._get_restaurant_name(restaurant_scrape)
        restaurant_rating = self._get_restaurant_rating(restaurant_scrape)
        price_type = self._get_price_type(restaurant_scrape)
        restaurant_address = self._get_restaurant_address(restaurant_card_scrape)
        review_highlights = self._get_review_highlights(restaurant_card_scrape)

        restaurant_data = {'restaurant_name': restaurant_name, 'restaurant_rating': restaurant_rating,
                           'restaurant_address': restaurant_address, 'price_type': price_type,
                           'review_highlights': review_highlights}

        self.thread_locks[page_number].acquire()
        self.restaurants_data_list.append(restaurant_data)
        self.restaurants_url_data_list.append(restaurant_card_url)
        self.thread_locks[page_number].release()

    def _get_restaurant_name(self, restaurant_scrape):
        """Getter function to scrape for name of restaurant"""

        return restaurant_scrape.find(class_="css-1m051bw").attrs['name']

    def _get_restaurant_rating(self, restaurant_scrape):
        """Getter function to scrape for rating of restaurant"""

        return float(restaurant_scrape.find(class_="five-stars__09f24__mBKym").attrs['aria-label'].strip('star rating'))

    def _get_price_type(self, restaurant_scrape):
        """Getter function to determine the price range of restaurant"""

        if len(restaurant_scrape.find_all(class_="priceRange__09f24__mmOuH")) == 0:
            price_type = ""
        else:
            price_type = restaurant_scrape.find(class_="priceRange__09f24__mmOuH").text

        return price_type

    def _get_restaurant_address(self, restaurant_card_scrape):
        """Getter function to determine address of restaurant"""

        try:
            return restaurant_card_scrape.find_all(class_="css-qyp8bo")[-1].text
        except IndexError:
            print('Unable to scrape website address')
            return ""

    def _get_review_highlights(self, restaurant_card_scrape):
        """Getter function to get the top 3 review highlights of restaurant"""

        review_highlights = []
        review_container_scrape = restaurant_card_scrape.find_all(class_="css-2sacua")

        if len(review_container_scrape) >= 3:
            for review_no in range(3):
                review_list = review_container_scrape[review_no].find_all(text=True)
                review_highlights.append(" ".join(review_list[1:-4]))

        return review_highlights

