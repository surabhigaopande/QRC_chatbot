# This app gives different features for the various Wi-Fi technologies.


import csv
import logging
import random
import unicodedata

from flask import Flask, jsonify, request
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)

# List of (wifi tech, feature, urls).
wifi = []

# Map from technology string to list of wifi objects.
wifi_by_tech = {}

# Map from url string to list of wifi objects.
wifi_by_url = {}



# Read in wifi tech and features.
with open('features.csv', 'rb') as wifi_file:
  feature_reader = csv.reader(wifi_file)

  # Skip the header line.
  next(feature_reader, None)

  # Each line of the csv has the format
  # "technology, feature, url".
  for row in feature_reader:
    feature = row[0]
    tech = row[1]
    url= row[2]
    wifi_object = (feature, tech, url)
    wifi.append(wifi_object)
    normalized_tech = tech.lower()
    if normalized_tech not in wifi_by_tech:
      wifi_by_tech[normalized_tech] = []
    wifi_by_tech[normalized_tech].append(wifi_object)
   
# Exception for a bad request from the client.
class BadRequestError(ValueError):
  pass

# Returns a wifi feature object matching the parameters of the request, or None if
# there are no matching features.
def _get_feature():
  # Extract the tech and url parameters. For robustness, the parameter
  # names can be capitalized in any way.
  tech = None
  url = None
  parameters = request.json['result']['parameters']
  print "paramaters is "+str(parameters)
  if parameters:
    for key, value in parameters.items():
      if key.lower() == 'tech':
        tech = unicodedata.normalize('NFKC', value).lower()
      elif key.lower() == 'url':
        url = unicodedata.normalize('NFKC', value).lower()
      else:
        raise BadRequestError('Unrecognized parameter in request: ' + key)

  # Find the set of features for a given tech (all features if not specified).
  applicable_tech_features = set()
  if tech:
    if tech in wifi_by_tech:
      applicable_tech_features = set(wifi_by_tech[tech])
  else:
    applicable_tech_features = set(wifi)

  
  # # Return None if there are no matching quotes.
  if len(applicable_tech_features) == 0:
     return None

  # Return one of the matching quotes randomly.
  feature_to_return = random.choice(applicable_tech_features)

  return feature_to_return


class FeatureSearch(Resource):
  # Handles a request from API.AI. The relevant part of the body is:
  # {
  #   "result": {
  #       "parameters": {
  #           <key>: <value>,
  #           <key>: <value>
  #       },
  #       "action": <action>
  #   }
  # }
  # See the README for the full API, and for a full sample request see
  # https://api.ai/docs/fulfillment#request.
  def post(self):
    try:
      if not request.json:
        raise BadRequestError('No json body was provided in the request.')

      if 'result' not in request.json:
        raise BadRequestError('"result" was not provided in the request body.')

      if 'action' not in request.json['result']:
        raise BadRequestError('No "action" was provided in the request.')

      action = request.json['result']['action']

      if action == 'get_feature_event':
        feature = _get_feature()
        if feature:
          response_body = {
            'followupEvent': {
                'name': 'respond_with_feature',
                'data': {
                    'feature': feature[0],
                    'tech': feature[1]
                }
            }}
        else:
          response_body = {
            'followupEvent': {
                'name': 'respond_with_feature',
                'data': {}
            }}

      elif action == 'get_feature_response':
        feature = _get_feature()
        if feature:
          response = 'Here is an interesting WiFi feature for the ' + feature[1] + ' technology : ' + feature[1]
        else:
          response = 'I have no matching WiFi feature.'
        response_body = {'speech': response, 'displayText': response}

      # elif action == 'get_bio_event':
        # bio = _get_bio()
        # if bio:
          # response_body = {
            # 'followupEvent': {
                # 'name': 'respond_with_bio',
                # 'data': {
                    # 'bio': bio
                # }
            # }}
        # else:
          # response_body = {
            # 'followupEvent': {
                # 'name': 'respond_with_bio',
                # 'data': {}
            # }}

      # elif action == 'get_bio_response':
        # bio = _get_bio()
        # if bio:
          # response = 'Here is the bio: ' + bio
        # else:
          # response = 'I have no matching bio.'
        # response_body = {'speech': response, 'displayText': response}

      else:
        raise BadRequestError('Request action unrecognized: "' + action + '"')

      return jsonify(response_body)

    except BadRequestError as error:
      response = jsonify(status=400, message=error.message)
      response.status_code = 400
      return response

# Register the featuresearch endpoint to be handled by the FeatureSearch class.
api.add_resource(FeatureSearch, '/featuresearch')

if __name__ == '__main__':
  app.run()
