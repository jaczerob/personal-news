from collections import defaultdict
from typing import Optional, NoReturn, List

import pandas
from surprise import SVD, Dataset, Reader
from surprise.model_selection import train_test_split

from database import database

_RATING_SCALE = (1, 5)
_DEFAULT_PREDICTIONS_AMOUNT = 5
_TEST_SIZE = 0.25

_DATAFRAME: Optional[pandas.DataFrame] = None

_DATASET: Optional[Dataset] = None

# Use the SVD algorithm to make our predictions
_ALGO = SVD()


async def init_dataset() -> NoReturn:
    if _DATASET is None:
        ratings = await database.get_ratings()
        ratings_dict = defaultdict(list)

        for rating in ratings:
            ratings_dict['user_id'].append(rating['user_id'])
            ratings_dict['keyword_id'].append(rating['keyword_id'])
            ratings_dict['rating'].append(rating['rating'])

        _create_dataset(ratings_dict)


async def add_row(user_id: int, keyword_id: int, rating: int) -> NoReturn:
    # I don't really know how to add a row into the Dataset so just remake it
    ratings_dict = _DATAFRAME.to_dict()

    ratings_dict['user_id'].append(user_id)
    ratings_dict['keyword_id'].append(keyword_id)
    ratings_dict['rating'].append(rating)

    _create_dataset(ratings_dict)


def _create_dataset(input_dict: dict) -> NoReturn:
    global _DATAFRAME
    global _DATASET

    _DATAFRAME = pandas.DataFrame(input_dict)
    reader = Reader(rating_scale=_RATING_SCALE)
    _DATASET = Dataset.load_from_df(_DATAFRAME[['user_id', 'keyword_id', 'rating']], reader)


async def get_predictions_for_user(user_id: int, amount: int = _DEFAULT_PREDICTIONS_AMOUNT) -> List[str]:
    """Returns a list of the highest estimated rated keywords for the given `user_id` of length `amount`"""

    predictions = _get_predictions()

    # Get predictions only for the user we want
    get_our_user_ratings = lambda user_rating: user_rating[0] == user_id

    # Get only the keyword ID and estimation
    unpack_ratings = lambda user_rating: (user_rating[1], user_rating[3])

    # Filter and unpack all the ratings using the above lambda functions
    filtered_ratings = map(unpack_ratings, filter(get_our_user_ratings, predictions))

    # Sort user ratings by their estimated value
    filtered_ratings = sorted(filtered_ratings, key=lambda x: x[1], reverse=True)

    keywords = list([await database.get_keyword(keyword) for keyword, _ in filtered_ratings])

    return keywords[:amount]


def _get_predictions() -> List:
    # Split the dataset into a training set and a testing set
    # The training set trains, or fits, the model
    # The test set evaluates the train set after fitting the model to get estimates for predictions
    trainset, testset = train_test_split(_DATASET, test_size=0.25)

    # Train the model (SVD) with the trainset
    algo = SVD()
    algo.fit(trainset)

    # Make predictions based off the trained model
    # The main data needed from the predictions is user ID, keyword ID, and user's estimated rating
    predictions = algo.test(testset)
    return predictions
