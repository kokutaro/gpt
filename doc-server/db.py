import os
from typing import Dict, List, Self, Tuple
from psycopg import Connection

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

    def __init__(self):
        self._host = os.environ.get("POSTGRES_DB_HOST", "host.docker.internal")
        self._port = int(os.environ.get("POSTGRES_DB_PORT", "5432"))
        self._database = os.environ.get("POSTGRES_DB", "postgres")
        self._user = os.environ.get("POSTGRES_USER", "postgres")
        self._password = os.environ.get("POSTGRES_PASSWORD", "password")

    def __enter__(self) -> Self:
        self._get_connection()
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        if not self._con is None and not self._con.closed:
            self._con.close()

    def _get_connection(self) -> Connection:
        self._con = psycopg2.connect(
            host=self._host,
            port=self._port,
            database=self._database,
            user=self._user,
            password=self._password,
        )
        return self._con

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
