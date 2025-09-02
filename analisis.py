import websocket
import json
import threading
import base64
import hmac
import hashlib
import time
import urllib.parse
from email.utils import formatdate

import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

import spacy
import re
import html
from email.utils import formatdate
from langdetect import detect_langs
import logging
from pathlib import Path

from volcenginesdkarkruntime import Ark


from itertools import product


def analisis(local_path,app_id):
    action = ["share", "provide", "give", "submit", "transfer", "transmit", "relay", "disclose", "release", "offer",
              "present", "deliver"
        , "hand over", "pass on", "communicate", "forward", "Limit", "Restrict", "Protect"]
    user = ["you", "your", "yourself", "yourselves", "user", "customer", "client", "consumer"]
    developer = ["we", "us", "our", "ourselves", "company", "organization", "firm", "corporation", "provider"]
    data_keywords = [
        "information", "payment data", "prohibited data", "restricted information", "services data", "user information",
        "prohibited information", "personal data", "account information", "device identifier",
        "personal identifier", "government identifier", "software identifier", "hardware identifier",
        "contact information", "personal information", "biometric information",
        "user information", "phone number", "passport number", "license number", "serial number", "ip address",
        "email address", "postal address",
        "mac address", "person name", "android id", "gsf id", "advertising id", "router ssid", "imei", "gender", "race",
        "ethnicity", "geolocation",
        "voiceprint", "fingerprint", "search history", "browsing history",
        "cookie", "login credential", "token", "information from social network", "sensitive personal information",
        "user data","data","number"
    ]

    history = [
        {
            "role":
                "user",
            "content":
                "你是语言助手，你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。你将使用纯英语进行回复"
        },
    ]

    # 预先定义的几个元组
    data_collect = ('collect', 'gather', 'acquire', 'obtain', 'receive', 'solicit', 'capture')
    data_share = ('share', 'distribute', 'disseminate', 'disclose', 'exchange', 'give', 'lease', 'provide',
                  'rent', 'release', 'report', 'sell', 'send', 'trade', 'transfer',
                  'transmit')
    data_use = ('use', 'utilize', 'employ', 'access', 'analyze', 'check', 'combine', 'connect', 'know',
                'process', 'utilize', 'derive')
    data_save = ('save', 'store', 'archive', 'keep', 'record', 'cache', 'store', 'storage')
    data_change = ('change', 'modify', 'alter', 'adjust', 'update', 'adapt')
    data_track = ('track', 'monitor', 'trace', 'log')

    # 定义一个字典，用于存储元组及其对应的替换值

    mapping = {
        data_collect: 'collect',
        data_share: 'share',
        data_use: 'use',
        data_save: 'save',
        data_change: 'change',
        data_track: 'track'
    }

    # 调用豆包大语言模型
    def call_llm(prompt):
        api_key = '00c354cc-0f82-4d26-aa94-a6c0bf9ceca8'
        # 替换 <Model> 为模型的 Model ID
        model = "doubao-1.5-lite-32k-250115"

        # 初始化 Ark 客户端
        client = Ark(api_key=api_key)

        try:
            # 创建一个对话请求
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"调用大语言模型时出现错误: {e}")
            return None

    # 利用history列表来构建prompt
    def send_prompt_and_get_response(prompt):
        global response_content
        response_content = ""

        # 将 history 中的字典元素转换为字符串
        history_strings = []
        for entry in history:
            history_strings.append(f"{entry['role']}: {entry['content']}")

        full_prompt = "\n".join(history_strings + [prompt])

        response_content = call_llm(full_prompt)

        return response_content

    # 文本预处理类
    class pre_text:

        # 数据清洗
        def convert_text_to_lowercase(self, text):  # 将输入文本转化为小写

            return text.lower()

        # 对输入的文本进行处理，移除 Unicode 符号、表情、HTML 实体。
        def clean_text(self, text):

            # 移除 HTML 实体
            text = html.unescape(text)

            # 移除表情符号
            emoji_pattern = re.compile("["
                                       u"\U0001F600-\U0001F64F"  # 表情符号
                                       u"\U0001F300-\U0001F5FF"  # 符号与图形
                                       u"\U0001F680-\U0001F6FF"  # 运输与地图符号
                                       u"\U0001F1E0-\U0001F1FF"  # 国旗与地区标志
                                       u"\U00002702-\U000027B0"
                                       u"\U000024C2-\U0001F251"
                                       "]+", flags=re.UNICODE)
            text = emoji_pattern.sub(r'', text)

            # 移除其他 Unicode 符号
            text = re.sub(r'[^\x00-\x7F]+', '', text)

            return text

        # 确保标点前后的空格统一
        def unify_english_punctuation_spaces(self, text):
            # 去除标点符号前的所有空格
            text = re.sub(r'\s+([.,;?!:])', r'\1', text)
            # 确保标点符号后有一个空格
            text = re.sub(r'([.,;?!:])(?!\s|$)', r'\1 ', text)
            return text

        # 过滤空行并且移除列表项编号和罗马数字
        def process_text(self, text):
            # 过滤掉空行
            non_empty_lines = [line for line in text.splitlines() if line.strip()]
            non_empty_text = '\n'.join(non_empty_lines)

            # 移除列表项编号和罗马数字
            # 移除罗马数字编号（如 I., II., III. 等）
            text_without_roman = re.sub(r'\b[IVXLCDM]+\.\s*', '', non_empty_text)
            # 移除数字编号（如 1., 2., 3. 等）
            text_without_numbers = re.sub(r'\b\d+\.\s*', '', text_without_roman)
            # 移除括号编号（如 (1), (2), (a), (b) 等）
            text_without_parentheses = re.sub(r'\([a-zA-Z0-9]+\)\s*', '', text_without_numbers)

            # 移除 URL
            url_pattern = re.compile(
                r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
            text_without_url = url_pattern.sub('', text_without_parentheses)

            # 替换复数形式
            words = text_without_url.split()
            new_words = []
            for word in words:
                if word.endswith('s') and len(word) > 1:
                    # 简单处理，去除单词末尾的 s
                    new_word = word[:-1]
                    new_words.append(new_word)
                else:
                    new_words.append(word)
            processed_text = ' '.join(new_words)

            return processed_text

        # 判断文本的语言
        def is_english_text_langdetect(self, text):
            try:
                detections = detect_langs(text)
                for detection in detections:
                    if detection.lang == 'en' and detection.prob > 0.5:
                        print("该文本语言是英语")
                        return 0
                print("该文本语言不是英语")
                return 1
            except:
                print("无法判断该文本的语言")
                return 1

        # 修改 pre_text 类中的 filter_paragraphs 方法
        def filter_paragraphs(self, text, developer, user, action, data_keywords):
            paragraphs = text.split('\n\n')
            valid_paragraphs = []

            # 放宽条件：只要包含任意类别的一个关键词即可
            all_keywords = developer + user + action + data_keywords
            for paragraph in paragraphs:
                # 检查是否包含任意关键词
                if any(re.search(rf'\b{kw}\b', paragraph, flags=re.IGNORECASE) for kw in all_keywords):
                    valid_paragraphs.append(paragraph)

            return '\n\n'.join(valid_paragraphs)

        def preper_text(self, text):
            c_text = self.convert_text_to_lowercase(text)
            c1_text = self.clean_text(c_text)
            c2_text = self.unify_english_punctuation_spaces(c1_text)
            c3_text = self.process_text(c2_text)
            c4_text = self.filter_paragraphs(c3_text, developer, user, action, data_keywords)

            return c4_text

    class ppfilter:
        # 对隐私政策进行模式匹配
        def save_paragraphs_with_patterns(self, text, app_id, action, user, data_keywords, developer):
            # 确保 paragraphs 文件夹存在
            if not os.path.exists('paragraphs'):
                os.makedirs('paragraphs')

            # 按段落分割文本
            paragraphs = text.split('\n')

            # 定义规则模式相关的关键词列表
            developers = developer  # 使用传入的 developer 列表
            actions = action  # 使用传入的 action 列表
            users = user  # 使用传入的 user 列表
            data_keywords = data_keywords  # 使用传入的 data_keywords 列表

            # 构建正则表达式模式
            developer_pattern = r'\b(' + '|'.join(developers) + r')\b'
            action_pattern = r'\b(' + '|'.join(actions) + r')\b'
            user_pattern = r'\b(' + '|'.join(users) + r')\b'
            data_pattern = r'\b(' + '|'.join(data_keywords) + r')\b'

            # 定义多种模式
            # 模式 1: 开发者 + 动作 + 数据关键词
            pattern1 = re.compile(fr'{developer_pattern}\s+{action_pattern}\s+{data_pattern}', re.IGNORECASE)
            # 模式 2: 用户 + 动作 + 数据关键词
            pattern2 = re.compile(fr'{user_pattern}\s+{action_pattern}\s+{data_pattern}', re.IGNORECASE)
            # 模式 3: 数据关键词 + 被动语态
            pattern3 = re.compile(fr'{data_pattern}\s+(?:is|are)\s+{action_pattern}\s+by\s+{developer_pattern}',
                                  re.IGNORECASE)
            # 模式 4: 开发者 + 动作 + 用户 + 数据关键词
            pattern4 = re.compile(fr'{developer_pattern}\s+{action_pattern}\s+{user_pattern}\s+{data_pattern}',
                                  re.IGNORECASE)
            # 模式 5: 动作 + 数据关键词
            pattern5 = re.compile(
                fr'\b(?:Limit|Restrict|Protect)\b\s+\b(?:Use|Disclosure|Collection)\b\s+of\s+{data_pattern}',
                re.IGNORECASE)

            # 生成模式 6 :数据关键词 + 开发者/用户 + 动作所有组合
            all_patterns_6 = []
            for act, data in product(action, data_keywords):
                pattern_str = fr'\b{act}\b.*?\b{data}\b'
                all_patterns_6.append(re.compile(pattern_str, re.IGNORECASE))

            # 过滤出包含规则模式的段落
            relevant_paragraphs = []
            num = 0
            for paragraph in paragraphs:
                num += 1
                # 检查段落是否匹配任意一种模式
                if (pattern1.search(paragraph) or
                        pattern2.search(paragraph) or
                        pattern3.search(paragraph) or
                        pattern4.search(paragraph) or
                        pattern5.search(paragraph)):
                    relevant_paragraphs.append(paragraph)
                    continue
                for pattern in all_patterns_6:
                    if pattern.search(paragraph):
                        relevant_paragraphs.append(paragraph)
                        break

            # 去重处理
            unique_paragraphs = list(set(relevant_paragraphs))  # 使用 set 去重

            # 将相关段落写入文件
            file_path = os.path.join('paragraphs', f'{app_id}.txt')
            with open(file_path, 'w', encoding='utf-8') as file:
                for paragraph in unique_paragraphs:
                    file.write(paragraph + '\n')

            print(f"包含规则模式的段落已保存到 {file_path}")
            print("段落数", num)

        # 去除文本中多余的空格
        def preprocess_sentences(self, text):
            # 使用正则表达式将连续的两个空格替换为一个空格
            result = re.sub(r'  ', ' ', text)
            return result

        # 对文本进行预处理
        def process_file(self, app_id):
            # 构建文件路径
            file_path = os.path.join('sentence', f'{app_id}.txt')
            try:
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()

                # 对内容进行预处理
                processed_content = self.preprocess_sentences(content)

                # 将处理后的内容写回文件
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(processed_content)
            except FileNotFoundError:
                print(f"未找到文件 {file_path}。")
            except Exception as e:
                print(f"处理文件时发生错误: {e}")

        # 对拆解后的句子进行过滤
        def save_sentences_with_patterns(self, app_id, action, developer, user, data_keywords):
            file_path = os.path.join('sentence', f'{app_id}.txt')

            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            paragraphs = content.split('\n')

            # 定义规则模式相关的关键词列表
            developers = developer  # 使用传入的 developer 列表
            actions = action  # 使用传入的 action 列表
            users = user  # 使用传入的 user 列表
            data_keywords = data_keywords  # 使用传入的 data_keywords 列表

            # 将所有关键词合并为一个大的正则表达式
            all_keywords = developers + actions + users + data_keywords
            keyword_pattern = r'\b(' + '|'.join(all_keywords) + r')\b'

            # 编译正则表达式
            pattern = re.compile(keyword_pattern, re.IGNORECASE)

            # 过滤出包含至少两个关键词的段落
            relevant_paragraphs = []
            for paragraph in paragraphs:
                matches = pattern.findall(paragraph)  # 查找所有匹配的关键词
                if len(matches) >= 1:  # 至少匹配两个关键词
                    relevant_paragraphs.append(paragraph)

            # 去重处理
            unique_paragraphs = list(set(relevant_paragraphs))  # 使用 set 去重

            # 将结果写回文件
            with open(file_path, 'w', encoding='utf-8') as file:
                for paragraph in unique_paragraphs:
                    file.write(paragraph + '\n')
            print("已对句子进行预处理")

        # 过滤元组，检验返回元组的正确性并且进行归一化
        def filter_tuples(self, app_id):
            # 构建文件路径
            file_path = os.path.join('tuple', f'{app_id}_tuple.txt')
            tuple_link = []

            try:
                # 打开文件并逐行读取
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line in file:
                        # 去除首尾空格
                        line = line.strip()
                        # 检查是否为有效的元组格式
                        if line.startswith('<') and line.endswith('>'):
                            # 提取元组元素
                            elements = line[1:-1].split(';')
                            # 将元素全部转换为小写
                            elements = [element.strip().lower() for element in elements]

                            # 过滤全为 None 的元组
                            if all(element == 'none' for element in elements):
                                continue

                            # 过滤主语为 None 的元组
                            if elements and elements[0] == 'none':
                                continue

                            # 过滤包含中文的元组
                            chinese_pattern = re.compile(r'[\u4e00-\u9fa5]')
                            if any(chinese_pattern.search(element) for element in elements):
                                continue

                            # 将符合条件的元组添加到列表中
                            tuple_link.append(tuple(elements))

            except FileNotFoundError:
                print(f"未找到文件: {file_path}")
            except Exception as e:
                print(f"读取文件时出现错误: {e}")

            self.filter_and_replace_tuples(app_id, tuple_link)

        # 对元组的动词进行归一化处理
        def filter_and_replace_tuples(self, app_id, input_tuple_list):
            filtered_tuples = []
            for tup in input_tuple_list:
                if len(tup) < 2:
                    continue
                second_element = tup[1].lower()  # 转换为小写，方便统一匹配
                found = False
                # 检查第二个元素中是否存在 'no' 或者 'not'
                has_no_or_not = 'no' in second_element or 'not' in second_element
                for key, value in mapping.items():
                    for keyword in key:
                        if keyword in second_element:
                            new_value = f"no {value}" if has_no_or_not else value
                            new_tup = (tup[0], new_value) + tup[2:]
                            filtered_tuples.append(new_tup)
                            found = True
                            break
                    if found:
                        break
                if not found:
                    continue

            # 构建输出文件路径
            output_file_path = os.path.join('tuple', f'{app_id}_tuple_filter')
            try:
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    for tup in filtered_tuples:
                        line = "<" + "; ".join(map(str, tup)) + ">\n"
                        f.write(line)
                print(f"处理后的元组已成功写入 {output_file_path}")
            except Exception as e:
                print(f"写入文件时出现错误: {e}")

    def read_text_file(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            print(f"文件 {file_path} 未找到。")
            return None
        except Exception as e:
            print(f"读取文件时发生错误: {e}")
            return None

    # 拆句子
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def split_paragraph_into_sentences(paragraph):

        prompt = f"请将以下隐私政策的一部分拆解为单个的句子，请使用纯英语回答：{paragraph}"
        try:
            result = send_prompt_and_get_response(prompt)
            sentences = result.split('\n')
            return [sentence.strip() for sentence in sentences if sentence.strip()]
        except Exception as e:
            logging.error(f"模型调用失败: {e}")
            return []

    def split_paragraphs_into_sentences(app_id):
        # 确保 sentence 文件夹存在
        sentence_dir = Path('sentence')
        sentence_dir.mkdir(exist_ok=True)

        # 读取 paragraphs 文件夹下的对应文件
        paragraph_file_path = Path('paragraphs') / f'{app_id}.txt'
        try:
            content = paragraph_file_path.read_text(encoding='utf-8')
        except FileNotFoundError:
            logging.error(f"未找到 {paragraph_file_path} 文件。")
            return

        # 按段落分割内容
        paragraphs = content.split('\n')

        all_sentences = []
        for paragraph in paragraphs:
            if paragraph.strip():  # 忽略空段落
                sentences = split_paragraph_into_sentences(paragraph)
                all_sentences.extend(sentences)

        # 将拆解后的句子保存到 sentence 文件夹下的对应文件
        sentence_file_path = sentence_dir / f'{app_id}.txt'
        sentence_file_path.write_text('\n'.join(all_sentences), encoding='utf-8')

        logging.info(f"句子已保存到 {sentence_file_path}")

    # 调用大语言模型将句子中的关键成分提取
    def extract_tuple_from_sentence(sentence):
        # 【主体识别规则】
        # 开发者实体条件：
        #    - 显示为应用/服务提供商（如"Google LLC"）
        #    - 使用"我们"/"我们的"/"本服务"
        # 用户实体条件：
        #    - 使用"您"/"用户"/"您的"
        #    - 涉及用户设备/账户（如"您的移动设备"）
        # 仅当数据是动作接收者时识别为数据实体（如"数据将被共享"）
        #
        # 【数据提取协议】
        # 保持原始数据粒度：
        #    完整并列结构："姓名、年龄和地址" → "name,age,address"
        #    拆分嵌套结构："元数据（通话记录，短信）" → "metadata,call logs,SMS"
        # 数据优先级（最具体→最不具体）：
        #    1. 技术字段：IMEI、GPS坐标、WiFi SSID
        #    2. 法律类别：PII、敏感财务数据
        #    3. 通用术语：用户内容、诊断数据
        #
        # 【复合条款处理】
        # 使用AND/OR拆分复杂句子：
        # 示例输入："我们收集设备型号用于分析 AND 在获得同意时与合作伙伴分享广告ID"
        #
        # <developer;collect;device model;none;analytics>
        # <developer;share;advertising ID;consent given;advertising>
        #
        # 【验证与格式化】
        # ! 标记️的情况：
        #    - 模糊术语："某些信息"、"其他数据"
        #    - 交叉引用："上述数据"
        # 格式：<主体;动作;数据;条件;目的>
        # 空字段：none
        # 数据分隔符：仅用逗号
        #
        # 【英文输出规则】
        # 1. 所有中文术语翻译为英文
        # 2. 保留技术术语：Cookie、UUID
        # 3. 标准翻译：
        #    - 位置权限 → location permission
        #    - 通讯录 → contacts
        #    - 账户信息 → account information
        #
        # 【完整示例】
        # 输入: "当您启用位置服务时，我们会获取GPS坐标以提供导航功能"
        # 翻译: "When you enable location services, we obtain GPS coordinates to provide navigation"
        # 输出: <user;enable;location services;none;none>
        #       <developer;obtain;GPS coordinates;location services enabled;navigation>
        #
        # 待处理文本:
        # {sentence}"""
        #

        prompt = f"""Extract structured data from privacy policy text (Chinese input allowed) with FULL ENGLISH OUTPUT following these rules:

            【Subject Identification】
            ■ Developer entity when:
               - Appears as app/service provider (e.g. "Google LLC", "Facebook Inc.")
               - Uses "we"/"our"/"this service" 
            ■ User entity when:
               - Uses "you"/"user"/"your"
               - Involves user devices/accounts (e.g. "your mobile device", "your Google account")
            ■ Data entity only when data is action receiver (e.g. "data will be shared")

            【Data Extraction Protocol】
            ◆ Preserve original data granularity:
               ✓ Full parallel structures: "name, age and address" → "name,age,address"
               ✓ Split nested structures: "metadata (call logs, SMS)" → "metadata,call logs,SMS"
            ◆ Data priority (most→least specific):
               1. Technical fields: IMEI, GPS coordinates, WiFi SSID
               2. Legal categories: PII, sensitive financial data
               3. General terms: user content, diagnostic data

            【Multi-Clause Processing】 
            Split complex sentences with AND/OR connectors:
            Example input: "We collect device model for analytics AND share advertising ID with partners when consent is given"
            → 
            <developer;collect;device model;none;analytics>
            <developer;share;advertising ID;consent given;advertising>

            【Validation & Formatting】
            ! FLAG with ⚠️ if: 
               - Ambiguous terms: "certain information", "other data"
               - Cross-reference: "the aforementioned data"
            ■ Format: <subject;action;data;condition;purpose>
            ■ Empty fields: [none]
            ■ Data separators: use commas ONLY

            【English Output Rules】
            1. Translate ALL Chinese terms to English
            2. Keep technical terms in English: Cookie, UUID
            3. Standard translations:
               - 位置权限 → location permission
               - 通讯录 → contacts
               - 账户信息 → account information

            【Complete Examples】
            Input: "TikTok collects SIM card ID and call history for risk assessment"
            Output: <developer;collect;SIM card ID,call history;none;risk assessment>

            Input: "当您启用位置服务时，我们会获取GPS坐标以提供导航功能"
            Translated: "When you enable location services, we obtain GPS coordinates to provide navigation"
            Output: <user;enable;location services;none;none>
                    <developer;obtain;GPS coordinates;location services enabled;navigation>

            Input: "Data including device info (IP address, MAC) will be encrypted"
            Output: <data;encrypt;device info,IP address,MAC;none;none>

            Text to process: 
            {sentence}"""

        try:
            # 假设 send_prompt_and_get_response 是调用大语言模型的函数
            result = send_prompt_and_get_response(prompt)
            # formatted_result = parse_and_format_response(result)
            print("返回结果：", result)
            # print("修改后结果：",formatted_result)
            # 解析模型返回的结果
            if result.startswith("<") and result.endswith(">"):
                return result.strip()
            else:
                logging.warning(f"模型返回格式不正确: {result}")
                return "(null, null, null, null, null)"
        except Exception as e:
            logging.error(f"模型调用失败: {e}")
            return "(null, null, null, null, null)"

    def split_sentences_into_tuples(app_id):
        """将句子拆解为元组并保存"""
        # 确保 tuple 文件夹存在
        tuple_dir = Path('tuple')
        tuple_dir.mkdir(exist_ok=True)

        # 读取 sentence 文件夹下的对应文件
        sentence_file_path = Path('sentence') / f'{app_id}.txt'
        try:
            content = sentence_file_path.read_text(encoding='utf-8')
        except FileNotFoundError:
            logging.error(f"未找到 {sentence_file_path} 文件。")
            return

        # 按换行符分割内容为句子
        sentences = content.split('\n')

        all_tuples = []
        for sentence in sentences:
            if sentence.strip():  # 忽略空句子
                sentence_tuple = extract_tuple_from_sentence(sentence)
                all_tuples.append(sentence_tuple)

        # 将提取的元组保存到 tuple 文件夹下的对应文件
        tuple_file_path = tuple_dir / f'{app_id}_tuple.txt'
        tuple_file_path.write_text('\n'.join(all_tuples), encoding='utf-8')

    def remove_numbered_list_items(app_id):
        # 构建文件路径
        file_path = os.path.join('sentence', f'{app_id}.txt')

        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # 使用正则表达式移除数字编号
            pattern = r'\d+\.\s*'
            new_content = re.sub(pattern, '', content)

            # 将处理后的内容写回文件
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)

            print(f"文件 {file_path} 中的数字编号已成功移除。")
        except FileNotFoundError:
            print(f"未找到文件 {file_path}。")
        except Exception as e:
            print(f"处理文件时发生错误: {e}")

    # 示例使用
    file_name = local_path
    text = read_text_file(file_name)

    # pretext是一个预处理类
    pretext = pre_text()

    new_text = pretext.preper_text(text)
    if (pretext.is_english_text_langdetect(new_text) == 1):
        print("隐私政策非英文")
        os._exit(0)

    # filtertext是一个对返回结果过滤的类
    filtertext = ppfilter()

    filtertext.save_paragraphs_with_patterns(text, app_id, action, developer, user, data_keywords)  # 对隐私政策进行模式匹配筛选

    split_paragraphs_into_sentences(app_id)  # 调用大语言模型进行拆句

    filtertext.process_file(app_id)  # 对拆句的结果进行过滤，去除多余空格和换行符

    filtertext.save_sentences_with_patterns(app_id, action, developer, user, data_keywords)  # 对拆句后的结果再进行一次过滤

    remove_numbered_list_items(app_id)  # 把句子中的数字编号去除

    split_sentences_into_tuples(app_id)  # 提取句子中的关键成分成元组

    filtertext.filter_tuples(app_id)  # 过滤元组，并对动词进行归一化处理

    return 0
