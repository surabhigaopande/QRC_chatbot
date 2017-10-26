# This app serves quotes from famous women in STEM by author and topic, and
# serves bios by author.
# Created for the "Building a Conversational Agent" workshop at the 2017
# Grace Hopper Conference.

import csv
import logging
import random
import unicodedata

from flask import Flask, jsonify, request
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)

# List of (quote, author, (topic1, topic2, ...)) tuples.
quotes = []

# Map from author string to list of quote objects.
quotes_by_author = {}

# Map from topic string to list of quote objects.
quotes_by_topic = {}


# Read in quotes and bios.
with open('features.csv', 'rb') as quotes_file:
  quotes_reader = csv.reader(quotes_file)

  # Skip the header line.
  next(quotes_reader, None)

  # Each line of the csv has the format
  # "quote, author, year_born, year_died, bio, date_spoken, source, topics,
  # comments".
  for row in quotes_reader:
    quote = row[0]
    author = row[1]
    quote_object = (quote, author)
    quotes.append(quote_object)
    normalized_author = author.lower()
    if normalized_author not in quotes_by_author:
      quotes_by_author[normalized_author] = []
    quotes_by_author[normalized_author].append(quote_object)
   

# Exception for a bad request from the client.
class BadRequestError(ValueError):
  pass

# Returns a quote object matching the parameters of the request, or None if
# there are no matching quotes.
def _get_quote():
  # Extract the author and topic parameters. For robustness, the parameter
  # names can be capitalized in any way.
  author = None
  topic = None
  parameters = request.json['result']['parameters']
  if parameters:
    for key, value in parameters.items():
      if key.lower() == 'author':
        author = unicodedata.normalize('NFKC', value).lower()
      else:
        raise BadRequestError('Unrecognized parameter in request: ' + key)

  # Find the set of quotes by the given author (all quotes if not specified).
  applicable_author_quotes = set()
  if author:
    if author in quotes_by_author:
      applicable_author_quotes = set(quotes_by_author[author])
  else:
    applicable_author_quotes = set(quotes)

  # Find the set of quotes on the given topic (all quotes if not given).
  applicable_topic_quotes = set()
  
  
  # Return None if there are no matching quotes.
  if len(applicable_quotes) == 0:
    return None

  # Return one of the matching quotes randomly.
  quote_to_return = random.choice(tuple(applicable_quotes))

  return quote_to_return

class QuoteSearch(Resource):
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

      if action == 'get_quote_event':
        quote = _get_quote()
        if quote:
          response_body = {
            'followupEvent': {
                'name': 'respond_with_quote',
                'data': {
                    'quote': quote[0],
                    'author': quote[1]
                }
            }}
        else:
          response_body = {
            'followupEvent': {
                'name': 'respond_with_quote',
                'data': {}
            }}

      elif action == 'get_quote_response':
        quote = _get_quote()
        if quote:
          response = 'Here is a quote by ' + quote[1] + ': ' + quote[0]
        else:
          response = 'I have no matching quote.'
        response_body = {'speech': response, 'displayText': response}


      else:
        raise BadRequestError('Request action unrecognized: "' + action + '"')

      return jsonify(response_body)

    except BadRequestError as error:
      response = jsonify(status=400, message=error.message)
      response.status_code = 400
      return response

# Register the quotesearch endpoint to be handled by the QuoteSerch class.
api.add_resource(QuoteSearch, '/quotesearch')

if __name__ == '__main__':
  app.run()

