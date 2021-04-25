import itertools
import random
import traceback

from sanic import Sanic, Request
from sanic.response import json

from database import dataset, database
from news import get_top_headlines

app = Sanic('personal-news')


@app.listener('before_server_start')
async def setup_db(_, __):
    await database.init_db()
    await dataset.init_dataset()


def parse_id(request_ip: str) -> int:
    # Make IDs IP based to save hassle on logins which aren't really in the scope of the project
    # return int(''.join(request_ip.split('.')))
    return random.randint(1, 10)  # For easy user_id generation


@app.route('/api/news')
async def news_handler(request: Request):
    error = None
    user_id = parse_id(request.ip)

    try:

        # If user is new, give them some new keywords to set them up in the database
        if new_keywords := await database.check_first_time(user_id):
            all_headlines = [await get_top_headlines(keyword) for keyword in new_keywords]
        else:
            predicted_keywords = await dataset.get_predictions_for_user(user_id)
            all_headlines = [await get_top_headlines(keyword) for keyword in predicted_keywords]

        all_headlines = list(itertools.chain.from_iterable(all_headlines))

        # Convert all headlines to a dict so they are JSON serializable
        all_headlines = list(map(lambda headline: headline.as_dict(), all_headlines))
    except Exception as e:
        all_headlines = []
        error = str(e)
        traceback.print_exc()

    return json({'headlines': all_headlines, 'error': error, 'user_id': user_id})


@app.route('/api/rating/<keyword:string>/<rating:int>')
async def rating_handler(request: Request, keyword: str, rating: int):
    error = None
    user_id = parse_id(request.ip)

    try:
        if not 1 <= rating <= 5:
            error = 'Rating must be between 1 and 5 inclusive.'
        else:
            await database.add_rating(user_id, keyword, rating)
    except Exception as e:
        error = str(e)

    return json({'error': error, 'user_id': user_id})
