# Sydney-Restaurant-Analyser

API remotely hosted on GCP and Firebase top Sydney restaurants based on categories including name, rating, price-type and distance. Data collected through Yelp API and optimised through multithreading.

### API LINK

https://bright-ab1d9.ts.r.appspot.com/


| Endpoint | Description | Params | Response Body
| ------------- | ------------- | ------------- | ------------- |
| /search?name={}  | Return the venues whose name contains the string @param(“name”). Sort the results by name in ascending order  | name : str (e.g. “the%20rocks%20cafe”) | {“venues” : [VenueSchema]}|
| /search?rating={}  | Return the venues whose rating is greater than the numerical value of @param(“rating”). Sort the results by rating in descending order.  | rating : str (e.g. 4) | {“venues” : [VenueSchema]}|
|/search?price_type={}| Return the venues with `price_type` that matches @param(“price_type”). Sort the results by name in ascending order. | price_type : str (e.g. “$$”) |  {“venues” : [VenueSchema]} | 
|/search?latitude={} &longitude={}| Return the venues within 5km of (@param(“latitude”), @param(“longitude”)). Sort the results by distance in ascending order. | latitude : str (e.g. -34.10285), longitude : str (e.g. 153.5231) | {“venues” : [VenueSchema]} |


Example request: https://bright-ab1d9.ts.r.appspot.com/search?price_type=$$$
