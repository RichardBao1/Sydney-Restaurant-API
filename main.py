from flask import Flask, request
import firebase_admin
from firebase_admin import credentials, firestore
import pygeohash
from os import environ

# Collecting database
cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
docs = db.collection('venues')

# Initialising Flask App
app = Flask(__name__)
app.secret_key = environ.get('SECRET_KEY')


@app.route('/search', methods=['GET'])
def main():
    """Handler for server queries"""

    args = request.args
    response_handler = ResponseHandler()

    if args.get('name') is not None:
        response_handler.param_name_handler(args.get('name'))
    elif args.get('rating') is not None:
        response_handler.param_rating_handler(args.get('rating'))
    elif args.get('price_type') is not None:
        response_handler.param_price_type_handler(args.get('price_type'))
    elif args.get('latitude') is not None and args.get('longitude') is not None:
        response_handler.param_lat_lon_handler(float(args.get('latitude')), float(args.get('longitude')))
    else:
        # Case where query was formatted incorrectly
        return 'Incorrect formatting'

    return response_handler.output


@app.errorhandler(404)
def page_not_found(e):
    """Handler for queries with incorrect paths"""
    return 'Wrong page'


class ResponseHandler:
    """

    Handler for the 4 different get response types to server

    """

    # For self.param_lat_lon_handler, returning all venus < 5000m
    GREATEST_DISTANCE = 5000

    def __init__(self):
        self.output = {'venues': []}
        self.dist_to_loc_list = []

    def param_name_handler(self, name):
        """determines the venues that contain 'name' in ascending order"""

        for doc in docs.stream():
            venue_data = doc.to_dict()
            if name in venue_data['name']:
                index = self.find_name_insert_pos(venue_data['name'])
                self.output['venues'].insert(index, venue_data)

    def find_name_insert_pos(self, name):
        """determines the index to insert the new venue by alphabetical order"""

        for index, venue_data in enumerate(self.output['venues']):
            if name < venue_data['name']:
                return index

        return len(self.output['venues'])

    def param_rating_handler(self, rating_benchmark):
        """determines the venues that contain a rating higher or above benchmark"""

        rating_benchmark = float(rating_benchmark)

        # In form {rating: [restaurantdata1, restaurantdata, ... ]}
        rating_dict = {}

        for doc in docs.stream():
            venue_data = doc.to_dict()
            rating = venue_data['rating']
            if rating >= rating_benchmark:
                if rating in rating_dict:
                    rating_dict[rating].append(venue_data)
                else:
                    rating_dict[rating] = [venue_data]

        rating_range = list(rating_dict.keys())
        rating_range.sort(reverse=True)
        for rating in rating_range:
            for venue_data in rating_dict[rating]:
                self.output['venues'].append(venue_data)

    def param_price_type_handler(self, price_type):
        """determines all venues that contain price type equal to 'price_type'"""

        query_docs = docs.where('price_type', '==', price_type)
        for doc in query_docs.stream():
            venue_data = doc.to_dict()
            index = self.find_name_insert_pos(venue_data['name'])
            self.output['venues'].insert(index, venue_data)

    def param_lat_lon_handler(self, lat, lon):
        """determines all venues within 5km of given coordinates"""

        target_geohash = pygeohash.encode(lat, lon, precision=10)
        for doc in docs.stream():
            venue_data = doc.to_dict()
            if venue_data['geohash'] == None:
                venue_data['geohash'] = ""

            distance = pygeohash.geohash_haversine_distance(target_geohash, venue_data['geohash'])
            if distance < ResponseHandler.GREATEST_DISTANCE:
                index = self.find_dist_insert_pos(distance, self.dist_to_loc_list)
                self.dist_to_loc_list.insert(index, distance)
                self.output['venues'].insert(index, venue_data)

    def find_dist_insert_pos(self, distance, dist_to_loc_list):
        """determines index to insert new venue by distance"""

        for index, venue_data in enumerate(dist_to_loc_list):
            if distance < dist_to_loc_list[index]:
                return index

        return len(self.output['venues'])


if __name__ == '__main__':
    app.run(debug=True)
