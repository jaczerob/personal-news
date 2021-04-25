import asyncio
import statistics

from newspaper import Article
from fakenews.prediction import detecting_fake_news
from typing import List


def split_article_text(newspaper_article: Article) -> List[str]:
    text = newspaper_article.text
    title = newspaper_article.title
    split_text = [t.strip() for t in text.split('.')] + [title]
    return split_text


async def batch_detect_fake_news(newspaper_article: Article) -> float:
    split_text = split_article_text(newspaper_article)
    loop = asyncio.get_running_loop()
    tasks = [loop.run_in_executor(None, detecting_fake_news, text) for text in split_text]
    done, _ = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
    results = [task.result() for task in done]
    return statistics.mean(results)
