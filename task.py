import mysql.connector
import json
import os
from dotenv import load_dotenv

load_dotenv()
import logging
import time
import base64

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'a'),
    'database': os.getenv('DB_NAME', 'office_translator')
}
# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s")

# Log to console
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info(f"DB_CONFIG: {DB_CONFIG}")

class Task:
    def __init__(self, id=None, md5=None, status=None, file_name=None, source_language=None, target_language=None, 
                 dont_translate_list=None, input_file_path=None, output_file_path=None, callback_url=None, 
                 user_id=None, created_at=None, updated_at=None, input_file_content = None, output_file_content=None, error_msg='', auto_resize_text=True):
        self.id = id
        self.md5 = md5
        self.status = status
        self.file_name = file_name
        self.source_language = source_language
        self.target_language = target_language
        self.dont_translate_list = dont_translate_list
        self.input_file_path = input_file_path
        self.output_file_path = output_file_path
        self.callback_url = callback_url
        self.user_id = user_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.db_conn = None
        self.input_file_content = input_file_content
        self.output_file_content = output_file_content
        self.error_msg = error_msg
        self.auto_resize_text = auto_resize_text

    def __del__(self):
        if self.db_conn is not None and self.db_conn.is_connected():
            logger.info("Closing database connection")
            self.db_conn.close()

    def __str__(self):
        return (f"Task(id={self.id}, md5={self.md5}, status={self.status}, file_name={self.file_name}, "
            f"source_language={self.source_language}, target_language={self.target_language}, "
            f"dont_translate_list={self.dont_translate_list}, input_file_path={self.input_file_path}, "
            f"output_file_path={self.output_file_path}, callback_url={self.callback_url}, user_id={self.user_id}, "
            f"error_msg={self.error_msg}, auto_resize_text={self.auto_resize_text}, "
            f"created_at={self.created_at}, updated_at={self.updated_at})")

    def connect_to_mysql(self,config, attempts=3, delay=2):
        attempt = 1
        # Implement a reconnection routine
        while attempt < attempts + 1:
            try:
                return mysql.connector.connect(**config)
            except (mysql.connector.Error, IOError) as err:
                if (attempts is attempt):
                    # Attempts to reconnect failed; returning None
                    logger.info("Failed to connect, exiting without a connection: %s", err)
                    return None
                logger.info(
                    "Connection failed: %s. Retrying (%d/%d)...",
                    err,
                    attempt,
                    attempts-1,
                )
                # progressive reconnect delay
                time.sleep(delay ** attempt)
                attempt += 1
        return None
    
    def get_connection(self):
        if self.db_conn is None or not self.db_conn.is_connected():
            # db_config = {
            #     'host': os.getenv('DB_HOST', '127.0.0.1'),
            #     'user': os.getenv('DB_USER', 'root'),
            #     'password': os.getenv('DB_PASSWORD', 'a'),
            #     'database': os.getenv('DB_NAME', 'office_translator')
            # }
            self.db_conn = self.connect_to_mysql(DB_CONFIG)
            if self.db_conn is None:
                logger.error("Failed to connect to MySQL")
                return None
        
        return self.db_conn

    def __db_query(self, sql):
        rows = []
        cnx = self.get_connection()
        with cnx.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            cursor.close()
        
        cnx.close()
        return rows
    
    def query(self):
        if self.id is not None:
            sql = f"SELECT id, md5, status, file_name, source_language, target_language, dont_translate_list, input_file_path, output_file_path, callback_url, user_id, error_msg, auto_resize_text, created_at, updated_at FROM tasks WHERE id = {self.id}"
        elif self.md5 is not None and self.source_language is not None and self.target_language is not None:
            sql = f"SELECT id, md5, status, file_name, source_language, target_language, dont_translate_list, input_file_path, output_file_path, callback_url, user_id, error_msg, auto_resize_text, created_at, updated_at FROM tasks WHERE md5 = '{self.md5}' AND source_language = '{self.source_language}' AND target_language='{self.target_language}'"
        else:
            logger.error("query error")
            return False
        rows = self.__db_query(sql)
        logger.info(f"rows: {rows}")
        if len(rows) == 0:
            return False
        else:
            self.id, self.md5, self.status, self.file_name, self.source_language, self.target_language, \
                self.dont_translate_list, self.input_file_path, self.output_file_path, self.callback_url, \
                self.user_id, self.error_msg, self.auto_resize_text, self.created_at, self.updated_at = rows[0]
            return True
    
    def insert_update(self):
        cnx = self.get_connection()
        sql_str = ("INSERT INTO tasks "
            "(md5, status, file_name, source_language, target_language, dont_translate_list, input_file_path, output_file_path, error_msg, auto_resize_text) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            " ON DUPLICATE KEY UPDATE status=%s, file_name=%s, dont_translate_list=%s,input_file_path=%s, output_file_path=%s, error_msg=%s, auto_resize_text=%s")
        data = (self.md5, self.status, self.file_name, self.source_language, self.target_language, 
            self.dont_translate_list, self.input_file_path, self.output_file_path, self.error_msg, self.auto_resize_text,
            self.status, self.file_name, self.dont_translate_list, self.input_file_path, self.output_file_path, self.error_msg, self.auto_resize_text)
        logger.info(sql_str % data)
        with cnx.cursor() as cursor:
            cursor.execute(sql_str, data)
            task_id = cursor.lastrowid
            self.id = cursor.lastrowid
            logger.info(f"new task id: {task_id}")
            cnx.commit()
            return 0, task_id, "success"
        
        return 1, None, "failed"

    def finish(self):
        self.status = 2
        return self.update()
        
    def fail(self):
        self.status = 3
        return self.update()

    # def reset(self):
    #     ret = 0
    #     cnx = self.get_connection()
    #     with cnx.cursor() as cursor:
    #         if self.md5 is not None and self.source_language is not None and self.target_language is not None:
    #             result = cursor.execute(f"UPDATE tasks SET status = 0 WHERE md5 = '{self.md5}'"
    #                                 f" and source_language = '{self.source_language}'"
    #                                 f" and target_language = '{self.target_language}'")
    #         elif self.id is not None:
    #             result = cursor.execute(f"UPDATE tasks SET status = {self.status} WHERE id = {self.id}")
    #         else:
    #             logger.error(f"id or md5, source_language, target_language not found in task")
    #             ret = 1
    #     cnx.commit()
    #     return ret
    
    def update(self):
        cnx = self.get_connection()
        if self.id is not None:
            sql_str = (f"UPDATE tasks SET status=%s, error_msg=%s WHERE id=%s")
            data = (self.status, self.error_msg, self.id)
        elif self.md5 is not None and self.source_language is not None and self.target_language is not None:
            sql_str = (f"UPDATE tasks SET status=%s, error_msg=%s WHERE md5=%s and source_language=%s and target_language=%s")
            data = (self.status, self.error_msg, self.md5, self.source_language, self.target_language)
        else:
            return 1
        logger.info(sql_str % data)
        with cnx.cursor() as cursor:
            cursor.execute(sql_str, data)
            cnx.commit()
            return 0

    def to_json(self):
        return json.dumps({
            'id': self.id,
            'md5': self.md5,
            'status': self.status,
            'file_name': self.file_name,
            'source_language': self.source_language,
            'target_language': self.target_language,
            'dont_translate_list': self.dont_translate_list,
            'input_file_path': self.input_file_path,
            'output_file_path': self.output_file_path,
            'callback_url': self.callback_url,
            'user_id': self.user_id,
            'auto_resize_text': self.auto_resize_text
            # 'input_file_content': None if self.input_file_content is None else base64.b64encode(self.input_file_content).decode('utf-8'),
            # 'created_at': self.created_at,
            # 'updated_at': self.updated_at
        })

    def from_dict(arr: dict): 
        obj = Task()
        if 'id' in arr:
            obj.id = arr['id']
        if 'md5' in arr:
            obj.md5 = arr['md5']
        if 'status' in arr:
            obj.status = arr['status']
        if 'file_name' in arr:
            obj.file_name = arr['file_name']
        if 'source_language' in arr:
            obj.source_language = arr['source_language']
        if 'target_language' in arr:
            obj.target_language = arr['target_language']
        if 'dont_translate_list' in arr:
            obj.dont_translate_list = arr['dont_translate_list']
        if 'input_file_path' in arr:
            obj.input_file_path = arr['input_file_path']
        if 'output_file_path' in arr:
            obj.output_file_path = arr['output_file_path']
        if 'callback_url' in arr:
            obj.callback_url = arr['callback_url']
        if 'user_id' in arr:
            obj.user_id = arr['user_id']
        if 'created_at' in arr:
            obj.created_at = arr['created_at']
        if 'updated_at' in arr:
            obj.updated_at = arr['updated_at']
        if 'input_file_content' in arr:
            obj.input_file_content = arr['input_file_content']
        if 'output_file_content' in arr:
            obj.output_file_content = arr['output_file_content']
        if 'error_msg' in arr:
            obj.error_msg = arr['error_msg']
        if 'auto_resize_text' in arr:
            obj.auto_resize_text = arr['auto_resize_text']
        return obj
