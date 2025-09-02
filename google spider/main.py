from google_play_scraper import search
import time
import csv


def get_app_ids(query, num_apps=500, max_retries=5):
    app_ids = []  # 存放爬取的 appid
    retries = 0  # 重试次数

    while len(app_ids) < num_apps and retries < max_retries:  # 实现循环爬取
        try:
            # 调用 search 函数并配置
            result = search(
                query,  # 搜索的范围
                lang="en",  # 语言
                country="us",  # 国家
            )

            # 提取应用 ID
            for app in result:
                app_ids.append(app['appId'])
                print(app['appId'])

            # 防止请求过于频繁
            time.sleep(5)  # 增加等待时间

            # 如果已经抓取到足够的应用 ID，退出循环
            if len(app_ids) >= num_apps:
                break

        except Exception as e:
            print(f"请求失败: {e}")
            retries += 1
            time.sleep(10)  # 等待更长时间后重试

    return app_ids[:num_apps]


# 定义多个搜索关键词
queries = ["game", "hot", "Leaderboard", "app", "diary", "free", "children's place", "18+app", "all", "china", "japan",
           "England", "american", "user", "numer", "pc"]

all_app_ids = []
# 遍历每个关键词进行搜索
for query in queries:
    app_ids = get_app_ids(query)
    all_app_ids.extend(app_ids)

# 去重
unique_app_ids = list(set(all_app_ids))

# 统计去重后的数量
total_count = len(unique_app_ids)

# 打印结果
print(f"Total unique app IDs fetched: {total_count}")
print(unique_app_ids)

# 将应用 ID 保存到 CSV 文件
csv_file = "appid.csv"
with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    # 写入表头
    writer.writerow(["App ID"])
    # 写入应用 ID
    for app_id in unique_app_ids:
        writer.writerow([app_id])

print(f"应用 ID 已保存到 {csv_file}")
