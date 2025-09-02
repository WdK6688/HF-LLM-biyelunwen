import sqlite3

def deduplicate_by_app_id(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 创建临时表存储唯一记录（按app_id分组，保留最小id）
        cursor.execute('''
            CREATE TEMP TABLE temp AS
            SELECT MIN(id) AS min_id
            FROM privacy_policy_result
            GROUP BY app_id;
        ''')

        # 删除非唯一记录（id不在临时表的min_id中）
        cursor.execute('''
            DELETE FROM privacy_policy_result
            WHERE id NOT IN (SELECT min_id FROM temp);
        ''')

        # 提交事务并清理临时表
        conn.commit()
        cursor.execute('DROP TABLE IF EXISTS temp;')
        print("去重完成，已删除重复记录。")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"错误：{e}")
    finally:
        conn.close()

# 调用函数（替换为你的数据库路径）
deduplicate_by_app_id("privacy_policy_metadata.db")