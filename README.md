# Office Translator办公翻译助手
利用开源LLM，打造离线翻译的小助手。

支持以下特性：
- 一键输出：输入一个PPT文件，按照原格式输出翻译好的文件；
- 支持中英互译
- 离线翻译：利用LLM私有化部署，可以离线翻译，从而防止信息泄漏；
- 自定义免翻译词汇：一些专有名词免翻译

不支持：
- 不支持图片翻译；
- 不支持SmartAr翻译：如果ppt中出现SmartArt，会保留不变输出到目标文件中；
- 不支持文本框大小自动调整：大多数情况下，中文翻译成英文后，文本长度会变长，反之则会变短，翻译后会保留字体及大小，需要再手动调整字体大小，以适配PPT的布局；

## 安装
这里介绍如何本地单机命令行运行，但同时也提供了WEB界面并扩展到集群服务，请跳到docker services.
```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

## 启动命令行翻译本地pptx文件
```
$ python pptx_translator.py -s --source_language_code=zh --target_language_code=en --input_file_path=./input.pptx
```
更详细用法请参考：
```
$ python pptx_translator.py -h
```

## docker services
本项目同时提供了WEB界面，以及构建了一套微服务架构：
![架构图](/images/architecture.jpg "Architecture")
总共包含以下几个服务：
1. WEB服务。采用Streamlit构建了一个表单，以供用户提交任务；
2. Controller。生产者角色，负责提交/更新用户的任务信息；
3. DB。采用Mysql，用于保存任务信息；
4. MQ。消息队列，用于任务信息的发布和订阅；
5. worker。消费者角色，负责对任务做翻译。worker需要运行Ollama，因此建议运行在有GPU的机器上。
### build镜像
```
cd scripts/docker
bash ./build.sh
```
### run
建议采用docker-compose做容器编排。首次运行，需要进行数据库等初始化：
```
cd scripts/docker
bash ./run.sh
```
之后，可以用docker-compose up/down/start/stop services来管理，比如：
```
docker-compose up web-app -d
docker-compose down web-app -d
```

## License
