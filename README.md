# Office Translator办公翻译助手
利用开源LLM，打造离线翻译的小助手。

支持以下特性：
- 一键输出：输入一个PPT文件，按照原格式输出翻译好的文件；
- 支持中英互译
- 离线翻译：利用LLM私有化部署，可以离线翻译，从而防止信息泄漏；
- 自定义免翻译词汇：一些专有名词免翻译

不支持：
- 不支持SmartAr翻译：如果ppt中出现SmartArt，会保留不变输出到目标文件中；
- 不支持文本框大小自动调整：大多数情况下，中文翻译成英文后，文本长度会变长，反之会变短，翻译后会保留字体及大小，需要手动视情况做二次调整

## 安装

```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

## 用法
```
$ python pptx-translator.py --help
usage: Translates pptx files from source language to target language using Amazon Translate service
       [-h] 
       source_language_code target_language_code input_file_path

positional arguments:
  source_language_code  The language code for the language of the source text.
                        Example: en
  target_language_code  The language code requested for the language of the
                        target text. Example: zh
  input_file_path       The path of the pptx file that should be translated

optional arguments:
  -h, --help            show this help message and exit
```

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
