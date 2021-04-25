import asyncio
import itertools
import re
from dataclasses import dataclass
from typing import List, Iterator, NoReturn

from newspaper import Article

import news
from fakenews import batch_detect_fake_news

__all__ = ['get_top_headlines']


@dataclass
class Headline:
    url: str
    title: str
    author: str
    published_at: str
    image_url: str
    description: str
    keywords: List[str]
    truth_score: str

    def as_dict(self) -> dict:
        """Return object as a dictionary representation of itself to be JSON serializable"""
        return {'url': self.url, 'title': self.title, 'author': self.author, 'publishedAt': self.published_at,
                'image': self.image_url, 'description': self.description, 'keywords': self.keywords,
                'truthScore': self.truth_score}


clean_string_regex = re.compile('<.*?>')
datetime_regex = re.compile('[TZ]')


def clean_keywords(article: Article) -> List[str]:
    """Make all keywords Titles and verify if the word is not an empty string"""

    # Sometimes the keywords are just '', so these need to be filtered out
    verify = lambda word: word  # Checks if word is not None
    clean = lambda word: word.title()  # Makes sure words are only made of letters in title form
    meta_keywords = map(clean, filter(verify, article.meta_keywords))
    keywords = map(clean, filter(verify, article.keywords))

    all_keywords = list(itertools.chain.from_iterable([meta_keywords, keywords]))
    return all_keywords


def clean_string(string: str) -> str:
    """Remove everything in <> and remove all end lines"""
    string = str(string)  # Sometimes the string isn't a string object (?)
    cleaned_string = clean_string_regex.sub('', string)
    cleaned_string = cleaned_string.replace('\n', '')
    return cleaned_string


def get_clean_article_keywords(article: Article, amount: int = 5) -> List[str]:
    """Clean all keywords and return only the given amount"""
    keywords = clean_keywords(article)
    return keywords[:amount]


def parse_article(parsed_article, newspaper_article, truth_score, amount_keywords: int = 5) -> dict:
    url = clean_string(parsed_article['url'])
    title = clean_string(parsed_article['title'])
    author = clean_string(parsed_article['author'])

    # Remove the T and Z from the string
    published_at = datetime_regex.sub(' ', clean_string(parsed_article['publishedAt'])).strip()

    image_url = parsed_article['urlToImage']
    description = clean_string(parsed_article['description'])
    keywords = get_clean_article_keywords(newspaper_article, amount_keywords)

    truth_score = f'{truth_score*100:.2f}%'

    return {'url': url, 'title': title, 'author': author, 'published_at': published_at, 'image_url': image_url,
            'description': description, 'keywords': keywords, 'truth_score': truth_score}


def build_article(article: Article):
    """Building an article gives the information about the description, keywords, author, publish date, etc."""
    article.build()


async def _batch_build(articles: List[Article]) -> NoReturn:
    """Build all articles at once"""
    loop = asyncio.get_running_loop()
    tasks = [loop.run_in_executor(None, build_article, article) for article in articles]
    _ = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)


async def get_newspaper_articles(urls: Iterator[str]) -> List[Article]:
    """Makes Article objects from the news URLs and builds them (parses them for information)"""
    articles = list(map(Article, urls))
    await _batch_build(articles)
    return articles


async def get_top_headlines(keyword: str, length: int = 5):
    """Return all top headlines from various sources from the given keyword"""
    response = await news.get_everything(keyword)
    parsed_articles = response['articles'][:length]

    url = lambda x: x['url']
    article_urls = map(url, parsed_articles)
    newspaper_articles = await get_newspaper_articles(article_urls)
    truth_scores = [await batch_detect_fake_news(newspaper_article) for newspaper_article in newspaper_articles]

    headlines = [Headline(**parsed_article) for parsed_article in
                 map(parse_article, parsed_articles, newspaper_articles, truth_scores)]
    return headlines
