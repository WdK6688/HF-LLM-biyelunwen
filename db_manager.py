import sqlite3
import json
from datetime import datetime


class DBManager:
    def __init__(self):
        self.conn = sqlite3.connect('privacy_policy_metadata.db')
        self.conn.execute("PRAGMA foreign_keys = ON")  # 启用外键约束
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        """创建表（含外键约束）"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS privacy_policy_result (
                id INTEGER PRIMARY KEY,
                app_id TEXT NOT NULL,
                result TEXT,  -- 存储JSON数组
                FOREIGN KEY(app_id) REFERENCES privacy_policy_metadata(app_id)
            )
        ''')
        self.conn.commit()

    def save_results(self, app_id, tuples_set):
        """
        存储五元组集合（自动校验格式）
        tuples_set示例：[("主语","操作","数据","目的","条件"), ...]
        """
        # 校验：必须是列表 of 元组，每个元组长度为5
        if not isinstance(tuples_set, list):
            raise ValueError("结果必须是列表")
        for t in tuples_set:
            if not isinstance(t, tuple) or len(t) != 5:
                raise ValueError(f"无效元组：{t}，必须是5元素元组")

        # 转换为JSON（元组转列表以支持JSON序列化）
        json_result = json.dumps([list(t) for t in tuples_set], ensure_ascii=False)

        # 插入数据库（带外键校验）
        try:
            self.cursor.execute('''
                INSERT INTO privacy_policy_result (app_id, result)
                VALUES (?, ?)
            ''', (app_id, json_result))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            raise ValueError(f"app_id={app_id}不存在于metadata表中")

    def get_results(self, app_id, limit=10):
        """获取指定APP的最新分析结果（反序列化JSON）"""
        self.cursor.execute('''
            SELECT result, analysis_time 
            FROM privacy_policy_result 
            WHERE app_id=? 
            ORDER BY analysis_time DESC 
            LIMIT ?
        ''', (app_id, limit))
        results = []
        for json_str, time in self.cursor.fetchall():
            try:
                tuples = [tuple(t) for t in json.loads(json_str)]  # 转回元组
                results.append({
                    "analysis_time": time,
                    "tuples": tuples
                })
            except json.JSONDecodeError:
                results.append({
                    "analysis_time": time,
                    "tuples": [],
                    "error": "JSON解析失败"
                })
        return results

    def get_app_names(self):
        """从 privacy_policy_metadata 表中获取 app_name 字段的值"""
        self.cursor.execute("SELECT app_name FROM privacy_policy_metadata")
        app_names = self.cursor.fetchall()
        return [app_name[0] for app_name in app_names]

    def get_local_path(self, app_name):
        """根据 app_name 获取对应的 local_path"""
        self.cursor.execute("SELECT local_path FROM privacy_policy_metadata WHERE app_name =?", (app_name,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None