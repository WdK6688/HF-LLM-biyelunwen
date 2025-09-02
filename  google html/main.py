import pandas as pd
from google_play_scraper import app
import time
import random


# 读取 appid.csv 文件 使用panda
def read_app_ids(input_file="appid.csv"):
    try:
        df = pd.read_csv(input_file)
        return df["App ID"].tolist()
    except Exception as e:
        print(f"Error reading {input_file}: {e}")
        return []


# 获取隐私政策链接
def get_privacy_policy_url(app_id, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            result = app(app_id)
            return result.get("privacyPolicy")  # 获取隐私政策链接
        except Exception as e:
            retries += 1
            if retries < max_retries:
                print(f"Error fetching {app_id} (attempt {retries}): {e}. Retrying...")
                # 等待一段时间后重试
                time.sleep(random.uniform(2, 5))
            else:
                print(f"Failed to fetch {app_id} after {max_retries} attempts: {e}")
    return None


# 批量获取隐私政策链接并保存到 CSV 文件
def batch_get_policy_links(app_ids, output_file="policy_links.csv"):
    data = []
    for app_id in app_ids:
        print(f"Processing {app_id}...")
        policy_url = get_privacy_policy_url(app_id)
        data.append({"app_id": app_id, "policy_url": policy_url})

        # 添加随机延迟，避免触发反爬虫机制
        time.sleep(random.uniform(1, 5))

    # 保存到 CSV 文件
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    print(f"Saved {len(data)} policy links to {output_file}")


# 主函数
def main():
    # 读取 appid.csv 文件
    app_ids = read_app_ids("appid.csv")
    if not app_ids:
        print("No app IDs found in the input file.")
        return

    # 批量获取隐私政策链接并保存
    batch_get_policy_links(app_ids, "policy_links.csv")


if __name__ == "__main__":
    main()
