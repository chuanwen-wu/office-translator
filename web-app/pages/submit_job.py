import base64
import streamlit as st
import logging
import json
import requests
import os

if 'logger' not in st.session_state:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s")

    # Log to console
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    st.session_state['logger'] = logger
logger = st.session_state['logger']

CONTROLLER_ENDPOINT = os.getenv('CONTROLLER_ENDPOINT', 'http://localhost:8080')
MAX_LEN_DONT_TRANSLATE_WORDS = 1024

def get_lang_code(lang_name: str) -> str:
    lang_map = {
        '中文': 'zh',
        '英文': 'en'
    }
    if lang_name not in lang_map:
        return ''
    else:
        return lang_map[lang_name]

def check_form(uploaded_file, source_lang: str, target_lang: str, dont_translate_words: str):
    passed = True
    msg = ''
    # if not st.session_state.uploaded_file:
    if uploaded_file is None:
        # st.write(f"源文件不能为空")
        msg = "源文件不能为空"
        passed = False
    else:
        logger.debug(f"uploaded file: {uploaded_file.name}")
        # if .pptx file
        if not uploaded_file.name.endswith(".pptx"):
            msg = "上传文件异常：必须是.pptx文件"
            passed = False 
    if source_lang == target_lang:
        msg = "源语言和目标语言不能相同"
        passed = False
    
    if get_lang_code(source_lang) == '':
        passed = False
        msg = f"源语言不支持{source_lang}"

    if get_lang_code(target_lang) == '':
        passed = False
        msg = f"目标语言不支持{target_lang}"

    if len(dont_translate_words) > MAX_LEN_DONT_TRANSLATE_WORDS:
        passed = False
        msg = f"累计最大长度不能超过1024个字符, 当前已输入字符数{len(dont_translate_words)}"

    return passed, msg

def submit_task(filename, file_content, source_name, target_name, dont_translate_words, force=False):
    data = {
        'source_lang': get_lang_code(source_name),
        'target_lang': get_lang_code(target_name),
        'input_file_content': base64.b64encode(file_content).decode('utf-8'),
        'input_filename': filename,
        'dont_translate_words': dont_translate_words,
        'force': force
    }
    logger.debug(f"request: {filename} from {source_name} to {target_name}, dont_translate_words={data['dont_translate_words']}, force={force} ")
    headers = {'Content-type': 'application/json'}
    resp = requests.post(f"{CONTROLLER_ENDPOINT}/ppt-translate", json = data, headers=headers)
    return resp

# http://localhost:8080/download/input-zh-20241206194605.pptx  ---> input-zh-20241206194605.pptx
def get_output_filename(download_file_path):
    return download_file_path.split('/')[-1]

def try_submit_task(force:bool = False):
    logger.debug("[try_submit_task]")
    st.session_state['task'] = {}

    uploaded_file = st.session_state.get('uploaded_file')
    source_lang = st.session_state.get('source_lang')
    target_lang = st.session_state.get('target_lang')
    dont_translate_words = st.session_state.get('dont_translate_words')
    if dont_translate_words:
        dont_translate_words = dont_translate_words.strip()
    passed, msg = check_form(uploaded_file, source_lang, target_lang, dont_translate_words)
    if not passed:
        logger.debug("[try_submit_task] not passed")
        st.session_state['task'] = {
            'status': -1, #not passed checking
            'msg': msg
        }
    else:
        # To read file as bytes:
        bytes_data = uploaded_file.getvalue()
        # logger.debug(f"file content: {bytes_data}")
        resp = submit_task(uploaded_file.name, bytes_data, source_lang, target_lang, dont_translate_words, force=force)
        logger.debug(f"status_code: {resp.status_code}")
        logger.debug(f"text: {resp.text}")
        # logger.debug(f"content: {resp.content}")
        # logger.debug(f"json: {resp.json()[1]}")
        # logger.debug(f"header: {resp.headers}")
        if resp.status_code == 200:
            #     'code': 0, 
            #     'status': 2, 
            #     'task_id': 126, 
            #     'message': 'task already exists, and is completed', 
            #     'download_file_path': 'http://localhost:8080/download/input-zh-20241203183612.pptx'}
            data = resp.json()[1] 
            if data['code'] == 0:
                if data['status'] == 2:
                    st.session_state['task'] = {
                        'status': 2,
                        'msg': "该PPT已被翻译过，立即下载，或重新翻译",
                        'task_id': data['task_id'],
                        'download_file_path': data['download_file_path'],
                        'output_filename': get_output_filename(data['download_file_path'])
                    }
                elif data['status'] == 0:
                    st.session_state['task'] = {
                        'status': 0,
                        'msg': f"翻译任务提交成功, 等待被翻译 id={data['task_id']}",
                        'task_id': data['task_id']
                    }
                elif data['status'] == 1:
                    st.session_state['task'] = {
                        'status': 1, 
                        'msg': f"正在翻译中，id={data['task_id']}",
                        'task_id': data['task_id']
                    }
                elif data['status'] == 3:
                    st.session_state['task'] = {
                        'status': 3, 
                        'msg': f"任务失败：id={data['task_id']}, ErrorMsg={data['message']}",
                        'task_id': data['task_id']
                    }
                else:
                    logger.exception(f"unknown msg: {data}")
            else: # code != 0
                st.warning(f"系统异常, code=${data['code']}")
        else: # http code != 200
            st.warning(f"系统异常, status_code=${resp.status_code}")

# curl -v http://localhost:8080/query?task_id=30
# curl -v http://localhost:8080/query/30  Todo
def query_task(task_id):
    logger.debug(f'query_task: {task_id}')
    # headers = {'Content-type': 'application/json'}
    resp = requests.get(f"{CONTROLLER_ENDPOINT}/query", params={'task_id': task_id})
    logger.debug(f"status_code: {resp.status_code}")
    logger.debug(f"text: {resp.text}")
    logger.debug(f"content: {resp.content}")
    logger.debug(f"json: {resp.json()}")
    logger.debug(f"header: {resp.headers}")
    if resp.status_code == 200:
        #     'code': 0, 
        #     'status': 2, 
        #     'task_id': 126, 
        #     'message': 'task already exists, and is completed', 
        #     'download_file_path': 'http://localhost:8080/download/input-zh-20241203183612.pptx'}
        data = resp.json()
        if data['code'] == 0:
            if data['status'] == 2:
                st.session_state['task'] = {
                    'status': 21,  # status 21跟2其实是一样数据库结果，但对应用户的操作不同
                    'msg': "翻译已完成",
                    'task_id': data['task_id'],
                    'download_file_path': data['download_file_path'],
                    'output_filename': get_output_filename(data['download_file_path'])
                }
            elif data['status'] == 0:
                st.session_state['task'] = {
                    'status': 0,
                    'msg': f"翻译任务已提交，排队中，id={data['task_id']}",
                    'task_id': data['task_id']
                }
            elif data['status'] == 1:
                st.session_state['task'] = {
                    'status': 1, 
                    'msg': f"正在翻译中，id={data['task_id']}",
                    'task_id': data['task_id']
                }
            elif data['status'] == 3:
                st.session_state['task'] = {
                    'status': 3, 
                    'msg': f"任务失败：id={data['task_id']}, ErrorMsg={data['message']}",
                    'task_id': data['task_id']
                } 
            else:
                logger.exception(f"unknown msg: {data}")
        else: # code != 0
            st.warning(f"系统异常, code=${data['code']}")
    else: # http code != 200
        st.warning(f"系统异常, status_code=${resp.status_code}")
    # return resp

task_form = st.form('task-form')
with task_form:
    uploaded_file = st.file_uploader("上传要翻译pptx文件", key='uploaded_file')
    left, middle, right = st.columns([10, 1, 10])
    left.selectbox('当前语言', ['中文', '英文'], key='source_lang')
    right.selectbox('目标语言', ['英文', '中文'], key='target_lang')
    txt = st.text_area(
        "[可选]保留词/免翻译词输入，以换行作为分割符：",
        "CTG\nCDN\nECS\nCT",
        key='dont_translate_words'
    )
    submit = st.form_submit_button('提交任务', on_click=try_submit_task)

resp_container = st.container()
with resp_container:
    task = st.session_state.get('task')
    if task:
        if task['status'] == -1: #checked not passed
            st.write(task['msg'])
        elif task['status'] == 0:
            left, right = st.columns([4, 2])
            left.write(f"翻译任务已提交，排队中，id={task['task_id']}")
            right.button("状态刷新", use_container_width=True, on_click=query_task, args=[task['task_id']])
        elif task['status'] == 1:
            left, right = st.columns([4, 2])
            left.write(f"正在翻译中，id={task['task_id']}")
            right.button("状态刷新", use_container_width=True, on_click=query_task, args=[task['task_id']])
        elif task['status'] == 2:
            left, middle, right = st.columns([4, 2, 2])
            left.write(f"该PPT已被翻译过， id={task['task_id']}")
            with open(f"file_repo/done/{task['output_filename']}", "rb") as f:
                middle.download_button(label='立即下载', data=f, mime='application/octet-stream', file_name=task['output_filename'])
            # middle.link_button("立即下载", task['download_file_path'], use_container_width=True)
            right.button("重新翻译", use_container_width=True, on_click=try_submit_task, kwargs={"force":True})
        elif task['status'] == 21:
            left, right = st.columns([6, 2])
            left.write(f"翻译已完成， id={task['task_id']}")
            # right.link_button("立即下载", task['download_file_path'], use_container_width=True)
            with open(f"file_repo/done/{task['output_filename']}", "rb") as f:
                right.download_button(label='立即下载', data=f, mime='application/octet-stream', file_name=task['output_filename'])
        elif task['status'] == 3: #query，且结果是失败
            st.write(task['msg'])
        