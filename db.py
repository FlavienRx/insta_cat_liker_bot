import os
import random
import sqlite3


class DbWrapper:
    def __init__(self, base_path, db_name):
        # Init database
        self.db = sqlite3.connect(os.path.join(base_path, db_name))
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()

        # Create url_sended table if not exists
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS like (user_name text NOT NULL, liked BOOLEAN DEFAULT 0, url text NOT NULL UNIQUE)"
        )
        # Create forbidden_words table if not exists
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS forbidden_words (value text NOT NULL UNIQUE)"
        )
        # Create ignoring_words table if not exists
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS ignoring_words (value text NOT NULL UNIQUE)"
        )
        # Create wanted_words table if not exists
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS wanted_words (value text NOT NULL UNIQUE)"
        )
        # Create user_name_banned table if not exists
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS user_name_banned (value text NOT NULL UNIQUE)"
        )
        # Create forbidden_words_in_user_name table if not exists
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS forbidden_words_in_user_name (value text NOT NULL UNIQUE)"
        )
        # Create locations table if not exists
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS locations (value text NOT NULL UNIQUE)"
        )

    def close(self):
        self.db.close()

    def load(self):
        table_list = [
            "forbidden_words",
            "ignoring_words",
            "wanted_words",
            "user_name_banned",
            "forbidden_words_in_user_name",
            "locations",
        ]

        for table in table_list:
            with open(table + ".txt", "r") as words_file:
                words = words_file.read().splitlines()

                sql_str = "INSERT INTO {} (value) VALUES(?)".format(table)

                for word in words:
                    try:
                        self.cursor.execute(sql_str, (word,))
                        self.db.commit()
                    except sqlite3.IntegrityError:
                        pass

    def get_random_locations(self, min, max):

        self.cursor.execute(
            "SELECT * FROM locations ORDER BY RANDOM() LIMIT {}".format(
                random.randint(min, max)
            )
        )

        return [row["value"] for row in self.cursor.fetchall()]

    def exist_in_table(self, table_name, words_list):
        if len(words_list) == 0:
            return False

        elif len(words_list) == 1:
            sql = "SELECT EXISTS(SELECT * FROM {} WHERE value IN {})".format(
                table_name, "('" + words_list[0] + "')"
            )

        elif len(words_list) > 1:
            sql = "SELECT EXISTS(SELECT * FROM {} WHERE value IN {})".format(
                table_name, tuple(words_list)
            )

        self.cursor.execute(sql)
        res = self.cursor.fetchone()

        return bool(res[0])

    def contains_value_in_table(self, table_name, string):
        sql = "SELECT * FROM {}".format(table_name)

        self.cursor.execute(sql)
        res = self.cursor.fetchall()

        if any(forbidden_word["value"] in string.lower() for forbidden_word in res):
            return True
        else:
            return False

    def add_like(self, user_name, liked, url):
        # Check if already send by insert url into database
        try:
            self.cursor.execute(
                "INSERT INTO like (user_name, liked, url) VALUES(?,?,?)",
                (user_name, liked, url),
            )
            self.db.commit()
            return True

        except sqlite3.IntegrityError:
            return False

    def count_like(self, user_name):
        self.cursor.execute(
            "SELECT COUNT(*) FROM like WHERE user_name=? AND liked=1", (user_name,)
        )
        res = self.cursor.fetchone()

        return res[0]

    def already_send(self, url):
        # Check if already send by insert url into database
        self.cursor.execute("SELECT EXISTS(SELECT * FROM like WHERE url=?)", (url,))
        res = self.cursor.fetchone()

        return bool(res[0])
