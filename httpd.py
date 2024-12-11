from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
import time
from urllib.parse import urlparse, parse_qs
from cgi import parse_header, parse_multipart
import json
import base64
import hashlib
import os
from task import Task
from io import BytesIO
import logging
import traceback
from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from kafka.errors import NoBrokersAvailable
from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
import threading

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
download_url_prefix = ''
# download_url_prefix = 'http://localhost:8080/download/' 
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

hostName = "0.0.0.0"
serverPort = 8080
db_conn = None

KAFKA_CONFIG = {
    'topic_pptx': os.getenv('KAFKA_TOPIC_PPTX', 'pptx-translate'),
    'topic_status': os.getenv('KAFKA_TOPIC_STATUS_UPDATE', 'status-update'),
    'servers': os.getenv('KAFKA_SERVERS', 'localhost:9092').split(',')
}

# class MyServer(SimpleHTTPRequestHandler):
#     def __init__(self, *args, **kwargs):
#         self.protocol_version = 'HTTP/1.0'
#         logger.info(f"self.directory: {done_repo_dir}")
#         super().__init__(*args, directory=done_repo_dir, **kwargs)

#     def do_GET(self):
#         logger.info(f"do_GET: {self.command}, {self.path}, headers: \n{self.headers}")
#         parsed = urlparse(self.path)
#         p = self.path.split("?")[0]
#         p = p.split("/")
#         pp = p[1]
#         if pp == 'query':
#             query_params = parse_qs(parsed.query)
#             logger.info(query_params)
#             task_id = query_params.get('task_id', [''])[0]
#             md5 = query_params.get('md5', [''])[0]
#             source_language = query_params.get('source_language', [''])[0]
#             target_language = query_params.get('target_language', [''])[0]
#             if task_id or md5:
#                 task_obj = Task(id=task_id, md5=md5, source_language=source_language, target_language=target_language)
#                 logger.info(f"task_obj: {task_obj}")
#                 ret = task_obj.query()
#                 if ret is True:
#                     self.send_response(200)
#                     self.send_header("Content-type", "application/json")
#                     self.end_headers()
#                     download_file_path = ''
#                     if task_obj.status == 2:
#                         download_file_path = download_url_prefix + task_obj.output_file_path
#                         msg = 'finished'
#                     elif task_obj.status == 1:
#                         msg = 'processing'
#                     elif task_obj.status == 0:
#                         msg = 'pending'
#                     elif task_obj.status == 3:
#                         msg = task_obj.error_msg
#                     else:
#                         msg = 'unknown'
#                     response = json.dumps({
#                         'code': 0,
#                         'status': task_obj.status,
#                         'task_id': task_obj.id,
#                         'message': msg,
#                         'download_file_path': download_file_path
#                     })
#                     logger.info(f"response: {response}")
#                     self.wfile.write(response.encode())
#                 else:
#                     self.send_error(404, "task not found")
#             else:
#                 self.send_error(403, "request params error")
#         elif pp == 'download':
#             filename = p[-1]
#             logger.info(f"download file: {filename}")
#             self.path = filename
#             super().do_GET()
#         else:
#             self.send_response(404)
#             self.send_header("Content-type", "text/plain")
#             self.end_headers()
#             self.wfile.write(b'Not Found')

#     def do_POST(self):
#         logger.info(f"do_POST: {self.command}, {self.path}, headers: \n{self.headers}")
#         parsed = urlparse(self.path)
#         # logger.info(f"parsed = {parsed}")
#         if parsed.path == '/ppt-translate':
#             # query_params = parse_qs(urlparse(self.path).query)
#             # data = query_params.get('data', [''])[0]
#             # source_lang
#             # target_lang
#             # dont_translate_word_list
#             # input_file
#             content_type, pdict = parse_header(self.headers.get('content-type'))
#             if content_type == 'multipart/form-data':
#                 pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
#                 post_vars = parse_multipart(self.rfile, pdict)
#                 # print(f"postvars: {post_vars}")
#                 source_lang = post_vars['source_lang'][0]
#                 target_lang = post_vars['target_lang'][0]
#                 input_file_content = post_vars['file'][0]
#                 input_filename = post_vars.get('filename', [''])[0]
#                 force = post_vars['force'][0]
#                 if not input_filename.endswith('.pptx'):
#                     logger.error(f"input_filename must end with .pptx")
#                     self.send_response(400)
#                     self.send_header("Content-type", "application/json")
#                     self.end_headers()
#                     response = json.dumps({'code': 400, 'message': 'input_filename must end with .pptx'})
#                     self.wfile.write(response.encode())
#                     return 0
#                 dont_translate_word_list = post_vars['dont_translate_word_list'][0]
#                 res = submit_translate_task(source_lang, target_lang, input_file_content, dont_translate_word_list, input_filename, force)
#                 self.send_response(200)
#                 self.send_header("Content-type", "application/json")
#                 self.end_headers()
#                 response = json.dumps(res)
#                 self.wfile.write(response.encode())
#                 return 0
#             elif content_type == 'application/json':
#                 req_datas = self.rfile.read(int(self.headers['content-length'])) 
#                 post_data = json.loads(req_datas.decode())
#                 # 昂贵的操作
#                 tmp = post_data.copy()
#                 del tmp['input_file_content']
#                 logger.info(f"post_data: {tmp}")
#                 dont_translate_word_list = ''
#                 input_filename = "default.pptx"
#                 if 'source_lang' in post_data and 'target_lang' in post_data and 'input_file_content' in post_data:
#                     source_lang = post_data['source_lang']
#                     target_lang = post_data['target_lang']
#                     input_file_content = base64.b64decode(post_data['input_file_content']) 
#                     if 'dont_translate_words' in post_data:
#                         dont_translate_word_list = post_data['dont_translate_words']
#                     if 'input_filename' in post_data:
#                         input_filename = post_data['input_filename']
#                     if 'force' in post_data:
#                         force = post_data['force']
#                     else:
#                         force = False
#                     res = submit_translate_task(source_lang, target_lang, input_file_content, dont_translate_word_list, input_filename, force)
#                     self.send_response(200)
#                     self.send_header("Content-type", "application/json")
#                     self.end_headers()
#                     response = json.dumps(res)
#                     self.wfile.write(response.encode())
#                     return 0
#             self.send_response(504)  # 504
#             self.send_header('Content-type', 'text/plain')
#             self.end_headers()
#             self.wfile.write(b'Bad Request')
#             return 0
#         else:
#             self.send_response(404)
#             self.send_header('Content-type', 'text/plain')
#             self.end_headers()
#             self.wfile.write(b'Not Found')
    
def submit_translate_task(source_lang, target_lang, input_file_content, dont_translate_word_list, input_filename, force=False):
    '''
    提交翻译任务。通过md5判断文件是否重复翻译过，是的话，返回历史文件；
    否则，提交翻译任务，返回task信息
    '''
    logger.info(f"submit_translate_task: source_lang={source_lang}, target_lang={target_lang}, dont_translate_word_list={dont_translate_word_list}, input_filename={input_filename}")
    os.makedirs(file_repo_dir, exist_ok=True)
    file_md5 = hashlib.md5(input_file_content).hexdigest()
    task_obj = Task(md5=file_md5, 
                    source_language=source_lang, 
                    target_language=target_lang, 
                    )
    ret = task_obj.query()
    if ret is True and task_obj.status != 3:  #任务存在且未失败
        download_file_path = ''
        logger.info(f"task already exists: {task_obj}")
        msg = "task already exists"
        if task_obj.status == 0:
            msg = f"{msg}, and is pending"
        elif task_obj.status == 1:
            msg = f"{msg}, and is processing"
        elif task_obj.status == 2:
            if not force:
                msg = f"{msg}, and is completed"
                download_file_path = download_url_prefix + task_obj.output_file_path
            else:   # 任务虽然已完成，但强制重新翻译
                # 更新老task的属性
                task_obj.file_name = input_filename
                task_obj.dont_translate_list = dont_translate_word_list
                task_obj.input_file_content = input_file_content
                res = insert_update_task(task_obj)
                return res['code'], res
        else:
            logger.error(f"unknown task status: {task_obj.status}")
            msg = f"{msg}, and is invalid"
        res = {
            'code': 0,
            'status': task_obj.status,
            'task_id': task_obj.id,
            'message': msg,
            'download_file_path': download_file_path,
        }
        return res['code'], res
    else: # 任务不存在或已失败
        task_obj.file_name = input_filename
        task_obj.dont_translate_list = dont_translate_word_list
        task_obj.input_file_content = input_file_content
        if ret is True and task_obj.status == 3:   #任务存在且已失败, 自动重新翻译
            logger.info(f"restart task which failed: {task_obj}")
            res = insert_update_task(task_obj)
        else: # 任务不存在，翻译
            logger.info(f"task not found, submit new task")
            res = insert_update_task(task_obj)
        
        return res['code'], res

def insert_update_task(task_obj):
    input_file_path = os.path.join(file_repo_dir, task_obj.md5 + '-' + task_obj.file_name)
    print(f"input_file_path: {input_file_path}")
    # 写入完整的文件内容
    with open(input_file_path, 'wb') as f:    
        f.write(task_obj.input_file_content)
    # 再提交数据库
    task_obj.id = None
    task_obj.status = 0
    task_obj.input_file_path = input_file_path
    task_obj.output_file_path = task_obj.file_name.replace(
        '.pptx', 
        "-{target_lang}-{timestr}.pptx".
        format(target_lang=task_obj.target_language, timestr=time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))))
    ret, task_id, msg = task_obj.insert_update()
    if ret == 0:
        # task_obj.input_file_content = input_file_content
        publish_translate_task(task_obj)
    res = {
        'code': ret,
        'status': task_obj.status,
        'message': msg,
        'task_id': task_id,
    }
    return res

def publish_translate_task(task: Task):
    logger.info(f"[publish_translate_task] id={task.id}, file_name={task.file_name}, source_language={task.source_language}, target_language={task.target_language} ")
    topic_name = KAFKA_CONFIG['topic_pptx']
    kafka_servers = KAFKA_CONFIG['servers']
    producer = KafkaProducer(bootstrap_servers=kafka_servers,
                             max_request_size=1024*1024*1024)
    # Asynchronous by default
    # task.input_file_content = base64.b64encode(task.input_file_content).decode('utf-8')
    # future = producer.send(topic_name, key=b'foo', value=json.dumps(task).encode('utf-8'))
    future = producer.send(topic_name, key=bytes(str(task.id), encoding='ascii'), value=task.to_json().encode('utf-8'))
    try:
        record_metadata = future.get(timeout=30)
        # Successful result returns assigned partition and offset
        logger.info(f"record_metadata.topic: {record_metadata.topic}, partition: {record_metadata.partition}, offset: {record_metadata.offset}")
        return True
    except KafkaError as err:
        logger.info(f'KafkaError: {err}')
        pass

def subscribe_status_update():
    logger.info(f"[subscribe_status_update] start...")
    topic_name = KAFKA_CONFIG['topic_status'] #'status-update'
    group_name = 'group2'
    kafka_servers = KAFKA_CONFIG['servers'] #['localhost:9092']
    while True:
        try:
            # To consume latest messages and auto-commit offsets
            consumer = KafkaConsumer(topic_name,
                                    group_id=group_name,
                                    bootstrap_servers=kafka_servers,
                                    enable_auto_commit=True,
                                    max_poll_records=1)
            logger.info(f"Waiting for task update...")
            for message in consumer:
                # message value and key are raw bytes -- decode if necessary!
                # e.g., for unicode: `message.value.decode('utf-8')`
                # print("%s:%d:%d: key=%s" % (message.topic, message.partition, message.offset, message.key))
                # logger.info("%s:%d:%d: key=%s" % (message.topic, message.partition, message.offset, message.key))
                task = json.loads(message.value.decode('utf-8'))
                logger.info(f"task update: id={task['id']}, status={task['status']}")
                break
            consumer.close()
            
            # update task status in database and file
            ret = 1
            # task_obj = Task(id=task['task_id'], status=task['status'], md5=task['md5'], source_language=task['source_language'], target_language=task['target_language'])
            task_obj = Task.from_dict(task)
            # if 'md5' in task and 'source_language' in task and 'target_language' in task:
            if task_obj.md5 is not None and task_obj.source_language is not None and task_obj.target_language is not None:
                # task_status = task['status']
                if task_obj.status == 1:
                    logger.info(f'task starts to be processing, id= {task_obj.id}')
                    ret = task_obj.update()
                elif task_obj.status == 2: # 成功
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
                        ret = task_obj.fail('output_file_path or output_file_content not found in task')
                elif task_obj.status == 3: # 失败
                    logger.error(f'task failed: status={task_obj.status}, error_msg={task_obj.error_msg}')
                    ret = task_obj.fail()
                else: # 未知状态
                    logger.error(f"unknown task status: {task_obj.status}")
                    ret = 1
            if ret != 0:
                logger.error(f"update task status failed")
            else:
                logger.info(f"update task status success")
        except NoBrokersAvailable as err:
            sec = 5
            logger.error(f"Unexpected {err}, retry in {sec} seconds")
            time.sleep(sec)
        except Exception as err:
            logger.error(f"Unexpected {err}, {type(err)}")
            logger.info(traceback.format_exc())
    # end of while

def check_mysql():
    conn = Task().get_connection()
    if conn is None:
        logger.error(f"Failed to connect to MySQL")
        return False
    else:
        logger.info(f"Connected to MySQL")
        return True
    
def check_kafka():
    logger.info(f"KAFKA_CONFIG: {KAFKA_CONFIG}")
    return True

def init_check():
    if not check_mysql():
        exit(1)

    if not check_kafka():
        exit(2)

# if __name__ == "__main__":
#     init_check()
    
#     # 线程，订阅状态更新，也可以用多进程或独立进程
#     t = threading.Thread(target=subscribe_status_update)
#     t.start()
#     # ThreadingHTTPServer
#     webServer = HTTPServer((hostName, serverPort), MyServer)
#     logger.info("Server started http://%s:%s" % (hostName, serverPort))

#     try:
#         webServer.serve_forever()
#     except KeyboardInterrupt:
#         pass

#     webServer.server_close()
#     logger.info("Server stopped.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting...")
    init_check()
    # 线程，订阅状态更新，也可以用多进程或独立进程
    t = threading.Thread(target=subscribe_status_update)
    t.start()
    yield
    logger.info("stopping...")

app = FastAPI(lifespan=lifespan)

class TaskForm(BaseModel):
    source_lang: str
    target_lang: str
    input_file_content: str
    input_filename: str
    dont_translate_words: str

@app.get("/api/query/{task_id}")
def query_task(task_id: int):
    task_obj = Task(id=task_id)
    logger.info(f"task_obj: {task_obj}")
    ret = task_obj.query()
    if ret is True:
        download_file_path = ''
        if task_obj.status == 2:
            download_file_path = download_url_prefix + task_obj.output_file_path
            msg = 'finished'
        elif task_obj.status == 1:
            msg = 'processing'
        elif task_obj.status == 0:
            msg = 'pending'
        elif task_obj.status == 3:
            msg = task_obj.error_msg
        else:
            msg = 'unknown'
        response = {
            'code': 0,
            'status': task_obj.status,
            'task_id': task_obj.id,
            'message': msg,
            'download_file_path': download_file_path
        }
        logger.info(f"response: {response}") 
    else:
        response = {
            'code': 404,
            'msg': 'task not found'
        }

    return response

class TaskData(BaseModel):
    source_lang: str
    target_lang: str
    input_file_content: str
    input_filename: str
    dont_translate_words: Union[str, None] = None
    force: Union[bool, None] = None

@app.post("/api/ppt-translate")
def ppt_translate(task: TaskData):
    logger.info(f"new task: {task.input_filename}, {task.source_lang}, {task.target_lang}, {task.dont_translate_words}, {task.force}")
    source_lang = task.source_lang
    target_lang = task.target_lang
    input_file_content = base64.b64decode(task.input_file_content)
    input_filename = task.input_filename
    if not task.dont_translate_words:
        dont_translate_words = ''
    else:
        dont_translate_words = task.dont_translate_words
    if not task.force:
        force = False
    else:
        force = task.force
    res = submit_translate_task(source_lang, target_lang, input_file_content, dont_translate_words, input_filename, force)
    return res
