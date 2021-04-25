from typing import List, Iterable, NoReturn, Optional

import aiosqlite

_DB_FILE = 'personal-news.sqlite'
_DB: Optional[aiosqlite.Connection] = None

# Default keywords for if the user has no keywords rated yet
_DEFAULT_KEYWORDS = ['apple', 'google', 'covid19', 'usa', 'cats']


async def init_db(file_name: str = _DB_FILE) -> NoReturn:
    global _DB

    if _DB is None:
        _DB = await aiosqlite.connect(file_name)
        _DB.row_factory = aiosqlite.Row

        # Keyword_id and keyword are stored in a separate table so keyword_id can easily be generated
        # and that it's easier to create a dataframe from the users table if its just the uid, kid, and rating
        await _DB.execute(
            '''CREATE TABLE IF NOT EXISTS keywords (
                keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                UNIQUE(keyword)
            );''')

        # Make sure there can only be one instance of a user rating a certain keyword
        await _DB.execute(
            '''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER,
                keyword_id INTEGER,
                rating INTEGER,
                UNIQUE(user_id, keyword_id) ON CONFLICT REPLACE 
            );''')

        await _DB.commit()


async def check_first_time(user_id: int) -> Optional[List[str]]:
    async with _DB.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
        if not await cursor.fetchone():
            return _DEFAULT_KEYWORDS
        else:
            return None


async def add_rating(user_id: int, keyword: str, rating) -> NoReturn:
    keyword_id = await _get_keyword_id(keyword)
    await _DB.execute('INSERT INTO users (user_id, keyword_id, rating) VALUES (?, ?, ?);',
                      (user_id, keyword_id, rating))
    await _DB.commit()


async def get_keyword(keyword_id: int) -> Optional[str]:
    async with _DB.execute('SELECT * FROM keywords WHERE keyword_id = ?', (keyword_id,)) as cursor:
        if row := await cursor.fetchone():
            return row['keyword']
        else:
            return None


async def _get_keyword_id(keyword: str) -> int:
    async with _DB.execute('SELECT * FROM keywords WHERE keyword = ?', (keyword,)) as cursor:
        if row := await cursor.fetchone():
            return row['keyword_id']

        async with _DB.execute('INSERT INTO keywords (keyword) VALUES (?);', (keyword,)) as cursor_:
            await _DB.commit()
            return cursor_.lastrowid  # lastrowid returns the keyword_id granted the insert works


async def get_ratings() -> Iterable[aiosqlite.Row]:
    async with _DB.execute('SELECT * FROM users') as cursor:
        users = await cursor.fetchall()
        return users
