import json
import os
from typing import Dict, List, Tuple
import psycopg2


class Db:
    GET_ALL_DOC_SQL = """
SELECT uuid, file_name, sha512, content_type
FROM uploaded_documents
ORDER BY file_name
OFFSET %s LIMIT %s
"""
    GET_DOC_COUNT_SQL = """
SELECT COUNT(1) AS COUNT
FROM uploaded_documents
"""

    GET_DOC_EXISTS_WITH_HASH_SQL = """
SELECT COUNT(1) AS COUNT
FROM uploaded_documents
WHERE sha512 = %s
"""

    INSERT_DOC_SQL = """
INSERT INTO uploaded_documents
(uuid, file_name, sha512, content_type)
VALUES (%s, %s, %s, %s)
"""

    UPSERT_CHAT_HISTORIES_SQL = """
INSERT INTO chat_history
(uuid, user_id, title, histories)
VALUES (%s, %s, %s, %s)
ON CONFLICT(uuid)
DO UPDATE SET title=EXCLUDED.title, histories=EXCLUDED.histories
"""
    GET_CHAT_TITLES_SQL = """
SELECT uuid, title
FROM chat_history
WHERE user_id=%s
"""

    GET_CHAT_HISTORIES_SQL = """
SELECT uuid, histories
FROM chat_history
WHERE uuid=%s AND user_id=%s
"""

    def __init__(self):
        self._host = os.environ.get("POSTGRES_DB_HOST", "db")
        self._port = int(os.environ.get("POSTGRES_DB_PORT", "5432"))
        self._database = os.environ.get("POSTGRES_DB", "postgres")
        self._user = os.environ.get("POSTGRES_USER", "postgres")
        self._password = os.environ.get("POSTGRES_PASSWORD", "password")

    def __enter__(self):
        self._get_connection()
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        if not self._con is None and not self._con.closed:
            self._con.close()

    def _get_connection(self):
        self._con = psycopg2.connect(
            host=self._host,
            port=self._port,
            database=self._database,
            user=self._user,
            password=self._password,
        )
        return self._con

    def upsert_chat_history(
        self, uuid: str, user_id: str, title: str, histories: List[Dict]
    ):
        cur = self._con.cursor()
        cur.execute(
            self.UPSERT_CHAT_HISTORIES_SQL,
            (uuid, user_id, title, json.dumps(histories)),
        )
        self._con.commit()
        cur.close()

    def get_chat_titles(self, user_id: str) -> Dict:
        cur = self._con.cursor()
        cur.execute(self.GET_CHAT_TITLES_SQL, [user_id])
        return dict(cur.fetchall())

    def get_chat_histories(self, uuid: str, user_id: str) -> List[Dict]:
        cur = self._con.cursor()
        cur.execute(self.GET_CHAT_HISTORIES_SQL, (uuid, user_id))
        data = cur.fetchone()
        if data is None:
            return []
        uuid, histories = data
        return histories

    def doc_exists(self, hash: str) -> bool:
        cur = self._con.cursor()
        cur.execute(self.GET_DOC_EXISTS_WITH_HASH_SQL, [hash])
        (count,) = cur.fetchone()
        cur.close()
        return int(count) > 0

    def insert_doc(
        self, uuid: str, file_name: str, sha512: str, content_type: str
    ) -> None:
        cur = self._con.cursor()
        cur.execute(self.INSERT_DOC_SQL, (uuid, file_name, sha512, content_type))
        self._con.commit()
        cur.close()

    def get_docs(self, pageNo: int = 1, pageSize: int = 20) -> Tuple[int, List[Dict]]:
        cur = self._con.cursor()
        cur.execute(self.GET_DOC_COUNT_SQL)
        (count,) = cur.fetchone()
        cur.execute(self.GET_ALL_DOC_SQL, [(pageNo - 1) * pageSize, pageSize])
        data = [
            {
                "uuid": uuid,
                "file_name": file_name,
                "file_hash": sha512,
                "file_type": content_type,
            }
            for uuid, file_name, sha512, content_type in cur.fetchall()
        ]

        cur.close()
        return (int(count), data)
