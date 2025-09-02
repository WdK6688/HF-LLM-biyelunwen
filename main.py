import streamlit as st
from db_manager import DBManager
import sqlite3
import json
from datetime import datetime
import pandas as pd
from analisis import analisis
import os
import tempfile


def display_categorized_results(results):
    if not results:
        st.warning("没有可展示的分析结果")
        return

    # 初始化分类字典（使用集合自动去重）
    categories = {
        'collect': set(),
        'share': set(),
        'use': set(),
        'save': set(),
        'change': set(),
        'track': set(),
        'no collect': set(),
        'no share': set(),
        'no use': set(),
        'no save': set(),
        'no change': set(),
        'no track': set()
    }

    # 分类收集数据
    for result in results:
        if len(result) >= 3:  # 确保有足够元素
            action = result[1].lower()
            data = result[2].strip().lower()  # 清理数据

            # 先检查是否存在no_前缀的类别
            matched = False
            for category in [c for c in categories if c.startswith('no ')]:
                if category == action:  # 精确匹配no category
                    if data != 'none':
                        categories[category].add(data)
                    matched = True
                    break

            # 如果没有匹配到no_前缀的类别，再检查普通类别
            if not matched:
                for category in [c for c in categories if not c.startswith('no ')]:
                    if category == action:  # 精确匹配category
                        if data != 'none':
                            categories[category].add(data)
                        break

    # 展示结果（只显示有数据的分类）
    st.markdown("### 4. Categorized Data Display")

    # 按原始类别顺序展示，每对先显示no_再显示普通
    original_categories = ['collect', 'share', 'use', 'save', 'change', 'track']
    for cat in original_categories:
        no_cat = f'no {cat}'
        has_no = bool(categories[no_cat])
        has_normal = bool(categories[cat])

        # 如果同时有no_和普通分类，都显示
        if has_no and has_normal:
            st.markdown(f"**Data {no_cat}:** {', '.join(sorted(categories[no_cat]))}")
            st.markdown(f"**Data {cat}:** {', '.join(sorted(categories[cat]))}")
        # 如果只有no_分类，只显示no_分类
        elif has_no:
            st.markdown(f"**Data {no_cat}:** {', '.join(sorted(categories[no_cat]))}")
        # 如果只有普通分类，只显示普通分类
        elif has_normal:
            st.markdown(f"**Data {cat}:** {', '.join(sorted(categories[cat]))}")

def analyze_uploaded_file(uploaded_file):
    """分析上传的文件"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    # 使用一个虚拟的app_id
    dummy_app_id = "uploaded_file_" + str(hash(uploaded_file.name))

    # 调用分析函数
    result = analisis(tmp_path, dummy_app_id)

    # 读取分析结果
    tuple_file_path = os.path.join('tuple', f'{dummy_app_id}_tuple_filter')
    llm_results = []
    if os.path.exists(tuple_file_path):
        try:
            with open(tuple_file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line.startswith('<') and line.endswith('>'):
                        elements = line[1:-1].split('; ')
                        llm_results.append(tuple(elements))

            # 删除临时生成的分析文件
            try:
                os.remove(tuple_file_path)
                os.remove(tmp_path)
            except:
                pass

            return llm_results
        except Exception as e:
            st.error(f"读取元组文件错误：{str(e)}")
            return None
    else:
        st.warning(f"未找到分析结果文件：{tuple_file_path}")
        return None


def analyze_existing_app(db, app_id, app_name):
    """分析数据库中已有的应用"""
    # 展示所选app_name对应的本地文件内容
    st.markdown("### 2. Privacy Policy Content")
    local_path = db.get_local_path(app_name)
    if local_path:
        try:
            with open(local_path, 'r', encoding='utf-8') as file:
                file_content = file.read()
            st.write(f"文件路径：{local_path}")
            st.text_area("文件内容", file_content, height=300)
        except Exception as e:
            st.error(f"读取文件出错：{str(e)}")
    else:
        st.warning(f"未找到 {app_name} 对应的本地文件路径")

    # LLM分析
    if not local_path:
        st.error("无法分析：没有找到有效的文件路径")
        return

    try:
        result = analisis(local_path, app_id)
    except Exception as e:
        st.error(f"分析过程出错：{str(e)}")
        return

    # 读取分析结果
    tuple_file_path = os.path.join('tuple', f'{app_id}_tuple_filter')
    llm_results = []
    if os.path.exists(tuple_file_path):
        try:
            with open(tuple_file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line.startswith('<') and line.endswith('>'):
                        elements = line[1:-1].split('; ')
                        llm_results.append(tuple(elements))

            # 存储结果到数据库
            try:
                result_json = json.dumps(llm_results, ensure_ascii=False)

                # 修改为 UPDATE 语句
                db.cursor.execute("""
                    UPDATE privacy_policy_result 
                    SET result = ?, last_updated = ? 
                    WHERE app_id = ?
                """, (result_json, datetime.now(), app_id))

                if db.cursor.rowcount == 0:
                    # 如果没有匹配的 app_id 记录，则插入新记录
                    db.cursor.execute("""
                        INSERT INTO privacy_policy_result 
                        (app_id, app_name, result, last_updated) 
                        VALUES (?, ?, ?, ?)
                    """, (app_id, app_name, result_json, datetime.now()))

                db.conn.commit()
                st.success(f"分析完成，存储了{len(llm_results)}个五元组")
                print("已保存至数据库")
            except Exception as e:
                db.conn.rollback()
                st.error(f"数据库错误无法存储：{str(e)}")

        except Exception as e:
            st.error(f"读取元组文件错误：{str(e)}")
    else:
        st.warning(f"未找到分析结果文件：{tuple_file_path}")

    # 展示分析结果
    st.markdown("### 3. Analysis Results")
    if not llm_results:
        st.warning("NULL")
    else:
        df = pd.DataFrame(
            llm_results,
            columns=["Subject", "Action", "Data", "Purpose", "Condition"]
        )

        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True
        )

        # 调用展示模块
        display_categorized_results(llm_results)


def main():
    st.set_page_config(page_title="基于大语言模型的移动应用隐私政策分析", layout="wide")
    db = DBManager()

    st.title("Analysis of Mobile App Privacy Policies Based on Large Language Models")

    # 添加文件上传选项
    analysis_option = st.radio(
        "选择分析方式",
        ("从已有应用中选择", "上传隐私政策文件")
    )

    if analysis_option == "上传隐私政策文件":
        st.markdown("### 1. 上传隐私政策文件")
        uploaded_file = st.file_uploader(
            "上传隐私政策文本文件",
            type=['txt'],
            help="请上传.txt格式的隐私政策文件"
        )

        if uploaded_file is not None:
            if st.button("分析上传的文件"):
                with st.spinner("正在分析文件..."):
                    # 显示文件内容
                    st.markdown("### 2. 隐私政策内容")
                    file_content = uploaded_file.getvalue().decode("utf-8")
                    st.text_area("文件内容", file_content, height=300)

                    # 分析文件
                    llm_results = analyze_uploaded_file(uploaded_file)

                    # 展示分析结果
                    st.markdown("### 3. 分析结果")
                    if not llm_results:
                        st.warning("NULL")
                    else:
                        df = pd.DataFrame(
                            llm_results,
                            columns=["Subject", "Action", "Data", "Purpose", "Condition"]
                        )

                        st.dataframe(
                            df,
                            hide_index=True,
                            use_container_width=True
                        )

                        # 调用展示模块
                        display_categorized_results(llm_results)

                        st.success("分析完成！注意：此结果不会保存到数据库")

    else:  # 原有从数据库选择的功能
        st.markdown("### 1. Privacy Policy Options")
        app_list = db.get_app_names()
        app_list = [name for name in app_list if name.strip()]

        if not app_list:
            st.warning("数据库中没有找到应用记录")
            return

        app_name = st.selectbox(
            "Options",
            options=app_list,
            format_func=lambda x: x
        )

        # 获取对应的app_id
        db.cursor.execute("SELECT app_id FROM privacy_policy_metadata WHERE app_name =?", (app_name,))
        app_id_result = db.cursor.fetchone()

        if not app_id_result:
            st.error(f"未找到 {app_name} 对应的 app_id")
            return
        app_id = app_id_result[0]

        # 确认按钮
        if st.button("Analyze"):
            analyze_existing_app(db, app_id, app_name)


if __name__ == "__main__":
    main()

