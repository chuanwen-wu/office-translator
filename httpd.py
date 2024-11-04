from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
import time
from urllib.parse import urlparse, parse_qs
from cgi import parse_header, parse_multipart
import json
import base64
import hashlib
import os
from pptx_translator import subscribe_translate_task
from task import Task
from io import BytesIO
import mysql.connector
import logging
# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s")

# Log to console
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

# Also log to a file
# file_handler = logging.FileHandler("cpy-errors.log")
# file_handler.setFormatter(formatter)
# logger.addHandler(file_handler) 

file_repo_dir = './file_repo'
done_repo_dir = os.path.join(file_repo_dir, 'done')
download_url_prefix = 'http://localhost:8080/download/'
task = {
    'md5': '',
    'status': 0,
    'file_name': '',
    'source_language': '',
    'target_language': '',
    'dont_translate_list': '',
    'input_file_path': '',
    'output_file_path': '',
    'callback_url': '',
}

"""
POST  /v1/ppt-translate
Parameters:
	source_lang
	target_lang
	dont_translate_word_list
	input_file

"""
hostName = "localhost"
serverPort = 8080
db_conn = None

class MyServer(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.protocol_version = 'HTTP/1.0'
        logger.info(f"self.directory: {done_repo_dir}")
        super().__init__(*args, directory=done_repo_dir, **kwargs)

    def do_GET(self):
        logger.info(f"do_GET: {self.command}, {self.path}, headers: \n{self.headers}")
        parsed = urlparse(self.path)
        p = self.path.split("?")[0]
        p = p.split("/")
        pp = p[1]
        if pp == 'query':
            query_params = parse_qs(parsed.query)
            logger.info(query_params)
            task_id = query_params.get('task_id', [''])[0]
            md5 = query_params.get('md5', [''])[0]
            source_language = query_params.get('source_language', [''])[0]
            target_language = query_params.get('target_language', [''])[0]
            if task_id or md5:
                task_obj = Task(id=task_id, md5=md5, source_language=source_language, target_language=target_language)
                logger.info(f"task_obj: {task_obj}")
                # task = get_task(task_obj)
                ret = task_obj.query()
                if ret is True:
                    self.send_header("Content-type", "application/json")
                    self.send_response(200)
                    self.end_headers()
                    # response = json.dumps(task)
                    # response = task_obj.to_json()
                    download_file_path = ''
                    if task_obj.status == 2:
                        download_file_path = download_url_prefix + task_obj.output_file_path
                        msg = 'finished'
                    elif task_obj.status == 1:
                        msg = 'processing'
                    elif task_obj.status == 0:
                        msg = 'pending'
                    elif task_obj.status == 3:
                        msg = 'failed'
                    else:
                        msg = 'unknown'
                    response = json.dumps({
                        'code': 0,
                        'status': task_obj.status,
                        'message': msg,
                        'download_file_path': download_file_path
                    })
                    logger.info(f"response: {response}")
                    self.wfile.write(response.encode())
                else:
                    self.send_error(404, "task not found")
            else:
                self.send_error(403, "request params error")
        elif pp == 'download':
            filename = p[-1]
            # output_file_path = query_params.get('filename', [''])[0]
            # # output_file_path = os.path.join("./", output_file_path)
            logger.info(f"download file: {filename}")
            # if os.path.exists(output_file_path):
                # logger.info(f"file exists: {filename}")
                # self.send_header("Content-type", "application/octet-stream")
                # self.send_header("Content-length", os.path.getsize(output_file_path))
                # self.send_response(200)
                # self.end_headers()
                # # with open(output_file_path, 'rb') as f:
                # #     self.wfile.write(f.read())
         
                # f = open(output_file_path, 'rb')
                # if f:
                #     try:
                #         self.copyfile(f, self.wfile)
                #         logger.info(f"copy file: {output_file_path} to wfile")
                #     finally:
                #         f.close()
                # """Serve a GET request."""
            self.path = filename
            super().do_GET()
                # f = self.send_head()
                # if f:
                #     try:
                #         self.copyfile(f, self.wfile)
                #     finally:
                #         f.close()
            # else:
            #     self.send_response(404)
            #     self.send_header("Content-type", "text/plain")
            #     self.end_headers()
            #     self.wfile.write(b'Not Found')
        else:
            # super().do_GET()
            # self.send_response(200)
            # self.send_header("Content-type", "text/html")
            # self.end_headers()
            # self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
            # self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
            # self.wfile.write(bytes("<body>", "utf-8"))
            # self.wfile.write(bytes("<p>This is an example web server.</p>", "utf-8"))
            # self.wfile.write(bytes("</body></html>", "utf-8"))
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b'Not Found')

    def do_POST(self):
        logger.info(f"do_POST: {self.command}, {self.path}, headers: \n{self.headers}")
        parsed = urlparse(self.path)
        # logger.info(f"parsed = {parsed}")
        if parsed.path == '/ppt-translate':
            # query_params = parse_qs(urlparse(self.path).query)
            # data = query_params.get('data', [''])[0]
            # source_lang
            # target_lang
            # dont_translate_word_list
            # input_file
            content_type, pdict = parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            if content_type == 'multipart/form-data':
                post_vars = parse_multipart(self.rfile, pdict)
                # print(f"postvars: {post_vars}")
                source_lang = post_vars['source_lang'][0]
                target_lang = post_vars['target_lang'][0]
                input_file_content = post_vars['file'][0]
                input_filename = post_vars.get('filename', [''])[0]
                dont_translate_word_list = post_vars['dont_translate_word_list'][0]
                res = submit_translate_task(source_lang, target_lang, input_file_content, dont_translate_word_list, input_filename)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = json.dumps(res)
                self.wfile.write(response.encode())
                return 0
            elif content_type == 'application/json': # todo 未测试
                req_datas = self.rfile.read(int(self.headers['content-length'])) 
                post_data = json.loads(req_datas.decode())
                logger.info(f"post_data: {post_data}")
                dont_translate_word_list = ''
                input_filename = "default.pptx"
                if 'source_lang' in post_data and 'target_lang' in post_data and 'input_file_content' in post_data:
                    source_lang = post_data['source_lang']
                    target_lang = post_data['target_lang']
                    input_file_content = post_data['input_file_content']
                    if 'dont_translate_word_list' in post_data:
                        dont_translate_word_list = post_data['dont_translate_word_list']
                    if 'input_filename' in post_data:
                        input_filename = post_data['input_filename']
                    res = submit_translate_task(source_lang, target_lang, input_file_content, dont_translate_word_list, input_filename)
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = json.dumps(res)
                    self.wfile.write(response.encode())
                    return 0
            self.send_response(504)  # todo 504 未测试
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Bad Request')
            return 0
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
def submit_translate_task(source_lang, target_lang, input_file_content, dont_translate_word_list, input_filename):
    '''
    提交翻译任务。通过md5判断文件是否重复翻译过，是的话，返回历史文件；
    否则，提交翻译任务，返回task信息
    '''
    logger.info(f"submit_translate_task: source_lang={source_lang}, target_lang={target_lang}, dont_translate_word_list={dont_translate_word_list}, input_filename={input_filename}")
    os.makedirs(file_repo_dir, exist_ok=True)
    file_md5 = hashlib.md5(input_file_content).hexdigest()
    # task_info = {   #todo change to struct
    #     'md5': file_md5,
    #     # 'status': 0,
    #     'file_name': input_filename,
    #     'source_language': source_lang,
    #     'target_language': target_lang,
    #     'dont_translate_list': dont_translate_word_list,
    #     'input_file_path': '',
    #     'output_file_path': '',
    # }
    task_obj = Task(md5=file_md5, 
                    file_name=input_filename, 
                    source_language=source_lang, 
                    target_language=target_lang, 
                    dont_translate_list=dont_translate_word_list,
                    )
    # task_old = get_task(task_obj)
    ret = task_obj.query()
    if ret is True and task_obj.status != 3:  #任务存在且未失败
        logger.info(f"task already exists: {task_obj}")
        msg = "task already exists"
        download_file_path = ''
        if task_obj.status == 0:
            msg = f"{msg}, and is pending"
        elif task_obj.status == 1:
            msg = f"{msg}, and is processing"
        elif task_obj.status == 2:
            msg = f"{msg}, and is completed"
            download_file_path = download_url_prefix + task_obj.output_file_path
        else:
            logger.error(f"unknown task status: {task_obj.status}")
            msg = f"{msg}, and is invalid"
        res = {
            'code': 0,
            'status': task_obj.status,
            'message': msg,
            'download_file_path': download_file_path,
        }
        return res['code'], res
        # task_status = task_old[2]
        # task_id = task_old[0]
        # output_file_path = task_old[8]
        # if task_status != 3:
        #     logger.info(f"task already exists: {task_old}")
        #     msg = "task already exists"
        #     if task_status == 0:
        #         msg = f"{msg}, and is pending"
        #     elif task_status == 1:
        #         msg = f"{msg}, and is processing"
        #     elif task_status == 2:
        #         msg = f"{msg}, and is completed"
        #     res = {
        #         'code': 0,
        #         'status': task_status,
        #         'message': msg,
        #         'task_id': task_id,
        #         'file_path': output_file_path
        #     }
        #    return res['code'], res
    else: # 任务不存在或已失败
        if ret is True and task_obj.status == 3:   #任务存在且已失败
            logger.info(f"task already failed: {task_obj}")
        else: # 任务不存在
            logger.info(f"task not found, submit new task")

        input_file_path = os.path.join(file_repo_dir, file_md5 + '-' + input_filename)
        print(f"input_file_path: {input_file_path}")
        # 写入完整的文件内容
        with open(input_file_path, 'wb') as f:    
            f.write(input_file_content)
        # 再提交数据库
        task_obj.id = None
        task_obj.status = 0
        task_obj.input_file_path = input_file_path
        task_obj.output_file_path = os.path.join(time.strftime('%Y%m%d-%H%M%S',time.localtime(time.time())) + '-' + target_lang + "-" + input_filename)
        # task_info['status'] = 0
        # task_info['input_file_path'] = input_filename
        # task_info['output_file_path'] = os.path.join(time.strftime('%Y%m%d-%H%M%S',time.localtime(time.time())) + '-' + target_lang + "-" + input_filename)
        
        ret, task_id, msg = task_obj.insert()
        # ret, task_id, msg = new_task(task_info)
        if ret == 0:
            # task_info['input_file_content'] = input_file_content
            # task_info['task_id'] = task_id
            task_obj.input_file_content = input_file_content
            publish_translate_task(task_obj)
        res = {
            'code': ret,
            'status': task_obj.status,
            'message': msg,
            'task_id': task_id,
        }

        return res['code'], res


def connect_to_mysql(config, attempts=3, delay=2):
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

def get_connection():
    global db_conn
    if db_conn is None or not db_conn.is_connected():
        db_config = {
            'host': os.getenv('DB_HOST', '127.0.0.1'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', 'a'),
            'database': os.getenv('DB_NAME', 'office_translator')
        }
        db_conn = connect_to_mysql(db_config)
    return db_conn


# def get_task_by_id(task_id):
#     sql = f"SELECT * FROM tasks WHERE task_id = {task_id}"
#     rows = query_task(sql)
#     if len(rows) == 0:
#         return None
#     else:
#         return rows[0]


# def get_task(task): #todo 复用query_tas
#     cnx = get_connection()
#     with cnx.cursor() as cursor:
#         sql = (f"SELECT * FROM tasks WHERE "
#                f"md5 = '{task['md5']}' and "
#                f"source_language = '{task['source_language']}' and "
#                f"target_language = '{task['target_language']}'")
#         logger.info(f"get task sql: {sql}")
#         cursor.execute(sql)
#         rows = cursor.fetchall()
#         cursor.close()
#         cnx.close()
#         if len(rows) == 0:
#             return None
#         else:
#             logger.info(f"get task: {rows[0]}")
#             return rows[0]

# def query_task(sql):
#     rows = []
#     cnx = get_connection()
#     with cnx.cursor() as cursor:
#         cursor.execute(sql)
#         rows = cursor.fetchall()
#         cursor.close()
    
#     cnx.close()
#     return rows

# def new_task(task):
#     cnx = get_connection()
#     sql_str = ("INSERT INTO tasks "
#         "(md5, status, file_name, source_language, target_language, dont_translate_list, input_file_path, output_file_path) "
#         "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
#         " ON DUPLICATE KEY UPDATE status=%s, file_name=%s, dont_translate_list=%s,input_file_path=%s, output_file_path=%s")
#     data = (task['md5'], task['status'], task['file_name'], task['source_language'], task['target_language'], 
#         task['dont_translate_list'], task['input_file_path'], task['output_file_path'],
#         task['status'], task['file_name'], task['dont_translate_list'], task['input_file_path'], task['output_file_path'])
#     logger.info(sql_str % data)
#     with cnx.cursor() as cursor:
#         cursor.execute(sql_str, data)
#         task_id = cursor.lastrowid
#         logger.info(f"new task id: {task_id}")
#         cnx.commit()
#         return 0, task_id, "success"
    
#     return 1, None, "failed"


from kafka import KafkaProducer
from kafka.errors import KafkaError
def publish_translate_task(task: Task):
    # logger.info(f"[publish_translate_task] id={task['task_id']}, md5={task['md5']}, file_name={task['file_name']}, source_language={task['source_language']}, target_language={task['target_language']} ")
    logger.info(f"[publish_translate_task] id={task.id}, md5={task.md5}, file_name={task.file_name}, source_language={task.source_language}, target_language={task.target_language} ")
    topic_name = 'pptx-translate'
    kafka_servers = ['localhost:9092']
    producer = KafkaProducer(bootstrap_servers=kafka_servers)
    # Asynchronous by default
    # task.input_file_content = base64.b64encode(task.input_file_content).decode('utf-8')
    # future = producer.send(topic_name, key=b'foo', value=json.dumps(task).encode('utf-8'))
    future = producer.send(topic_name, key=bytes(str(task.id), encoding='ascii'), value=task.to_json().encode('utf-8'))
    try:
        record_metadata = future.get(timeout=10)
        # Successful result returns assigned partition and offset
        logger.info(f"record_metadata.topic: {record_metadata.topic}, partition: {record_metadata.partition}, offset: {record_metadata.offset}")
        return True
    except KafkaError:
        # Decide what to do if produce request failed...
        # log.exception()
        logger.info('KafkaError')
        pass

from kafka import KafkaConsumer
def subscribe_status_update():
    logger.info(f"[subscribe_status_update] start...")
    topic_name = 'status-update'
    group_name = 'group2'
    kafka_servers = ['localhost:9092']
    while True:
        # To consume latest messages and auto-commit offsets
        consumer = KafkaConsumer(topic_name,
                                 group_id=group_name,
                                 bootstrap_servers=kafka_servers,
                                 enable_auto_commit=True,
                                 max_poll_records=1)
        for message in consumer:
            # message value and key are raw bytes -- decode if necessary!
            # e.g., for unicode: `message.value.decode('utf-8')`
            # print("%s:%d:%d: key=%s" % (message.topic, message.partition, message.offset, message.key))
            # logger.info("%s:%d:%d: key=%s" % (message.topic, message.partition, message.offset, message.key))
            task = json.loads(message.value.decode('utf-8'))
            logger.info(f"task update: id={task['id']}, status={task['status']}, md5={task['md5']}, source_language={task['source_language']}, target_language={task['target_language']}")
            break
        consumer.close()
        
        # update task status in database and file
        ret = 1
        # task_obj = Task(id=task['task_id'], status=task['status'], md5=task['md5'], source_language=task['source_language'], target_language=task['target_language'])
        task_obj = Task.from_dict(task)
        # if 'md5' in task and 'source_language' in task and 'target_language' in task:
        if task_obj.md5 is not None and task_obj.source_language is not None and task_obj.target_language is not None:
            # task_status = task['status']
            if task_obj.status == 2: # 成功
                # 写输出文件
                # if 'output_file_path' in task and 'output_file_content' in task: # 有输出文件
                if task_obj.output_file_path is not None and task_obj.output_file_content is not None:
                    file_path = os.path.join(done_repo_dir, task_obj.output_file_path)
                    logger.info(f"write output file to: {file_path}")
                    with open(file_path, 'wb') as f:
                        f.write(base64.b64decode(task_obj.output_file_content))
                    # ret = finish_task(task_obj)
                    ret = task_obj.finish()
                else: # 没有输出文件
                    logger.error(f"output_file_path or output_file_content not found in task")
                    # ret = fail_task(task)
                    ret = task_obj.fail()
            elif task_obj.status == 3: # 失败
                # ret = fail_task(task)
                ret = task_obj.fail()
            else: # 未知状态
                logger.error(f"unknown task status: {task_obj.status}")
                ret = 1
        if ret != 0:
            logger.error(f"update task status failed")
        else:
            logger.info(f"update task status success")
                

# def processing_task(task):
#     cnx = get_connection()
#     with cnx.cursor() as cursor:
#         result = cursor.execute(f"UPDATE tasks SET status = 1 WHERE md5 = '{task['md5']}' "
#                                 f" and source_language = '{task['source_language']}'"
#                                 f" and target_language = '{task['target_language']}'")
#         cnx.commit()

# def finish_task(task):
#     ret = 0
#     cnx = get_connection()
#     with cnx.cursor() as cursor:
#         if 'md5' in task and 'source_language' in task and 'target_language' in task:
#             result = cursor.execute(f"UPDATE tasks SET status = 2 WHERE md5 = '{task['md5']}'"
#                                     f" and source_language = '{task['source_language']}'"
#                                     f" and target_language = '{task['target_language']}'")
#         elif 'task_id' in task:
#             result = cursor.execute(f"UPDATE tasks SET status = 2 WHERE task_id = {task['task_id']}")
#         else:
#             logger.error(f"task_id or md5, source_language, target_language not found in task")
#             ret = 1
#         cnx.commit()
#         return ret

# def fail_task(task):
#     ret = 0
#     cnx = get_connection()
#     with cnx.cursor() as cursor:
#         if 'md5' in task and 'source_language' in task and 'target_language' in task:
#             result = cursor.execute(f"UPDATE tasks SET status = 3 WHERE md5 = '{task['md5']}'"
#                                     f" and source_language = '{task['source_language']}'"
#                                     f" and target_language = '{task['target_language']}'")
#         elif 'task_id' in task:
#             result = cursor.execute(f"UPDATE tasks SET status = 3 WHERE task_id = {task['task_id']}")
#         else:
#             logger.error(f"task_id or md5, source_language, target_language not found in task")
#             ret = 1
#         cnx.commit()
#     return ret

import threading, multiprocessing
if __name__ == "__main__":
    # 线程，订阅状态更新，也可以用多进程或独立进程
    t = threading.Thread(target=subscribe_status_update)
    t.start()
    # ThreadingHTTPServer
    webServer = HTTPServer((hostName, serverPort), MyServer)
    logger.info("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    get_connection().close()
    # t.join()
    logger.info("Server stopped.")
