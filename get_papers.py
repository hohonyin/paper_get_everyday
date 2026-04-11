import arxiv
import google.generativeai as genai
import datetime
import os
import time

# 1. 配置
# 优先从环境变量读取 API Key
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") 
genai.configure(api_key=GOOGLE_API_KEY)

# 设置话题列表
TOPICS = ["SSM", "In-context Learning"]
# 每个话题获取的数量
MAX_RESULTS_PER_TOPIC = 10
# 每次请求 Gemini 后的暂停时间（秒）
PAUSE_SECONDS = 5

# 初始化模型 (建议使用 1.5-flash，兼容性最广)
model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

def get_latest_papers(topic, max_results):
    """
    从 ArXiv 获取指定主题的最新论文
    """
    print(f"\n🔍 正在检索关于 '{topic}' 的最新论文...")

    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    papers_data = []
    # 增加尝试机制防止接口变动报错
    try:
        for result in search.results():
            papers_data.append({
                "title": result.title,
                "abstract": result.summary,
                "url": result.entry_id,
                "published": result.published
            })
    except Exception as e:
        print(f"检索 ArXiv 出错: {e}")
    
    return papers_data

def generate_summary(paper):
    """
    调用 Gemini API 生成中文解读
    """
    print(f"📝 正在研读论文：{paper['title'][:50]}...")

    prompt = f"""
    You are an expert academic researcher. Please analyze the following paper.

    Input Data:
    Title: {paper['title']}
    Abstract: {paper['abstract']}

    Requirements:
    1. Translate title to Simplified Chinese.
    2. Summarize core content (100-150 words) in Chinese.
    3. List exactly 3 key innovation points in Chinese.
    4. Provide 2-3 tags in Chinese.
    5. Output strictly in Markdown format.
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"### 解读失败\n**标题**: {paper['title']}\n**错误信息**: {e}"

def main():
    daily_report = f"# 📅 AI 前沿论文日报 ({datetime.date.today()})\n\n"
    
    all_papers_to_process = []

    # 1. 汇总所有话题的论文
    for topic in TOPICS:
        papers = get_latest_papers(topic=topic, max_results=MAX_RESULTS_PER_TOPIC)
        all_papers_to_process.extend(papers)

    print(f"\n✅ 汇总完成，共计 {len(all_papers_to_process)} 篇论文待处理。")

    # 2. 逐篇处理并添加暂停逻辑
    for index, paper in enumerate(all_papers_to_process):
        summary = generate_summary(paper)

        # 拼接内容
        daily_report += f"{summary}\n"
        daily_report += f"🔗 **原文链接**: {paper['url']}\n"
        daily_report += "\n---\n\n"

        # 3. 设置请求暂停（最后一篇处理完后不需要暂停）
        if index < len(all_papers_to_process) - 1:
            print(f"⏳ 等待 {PAUSE_SECONDS} 秒以遵守 API 频率限制...")
            time.sleep(PAUSE_SECONDS)

    # 4. 输出结果并保存到文件
    print("\n" + "="*20 + " 任务完成 " + "="*20 + "\n")

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(daily_report)
    
    print(f"报告已生成至 report.md，共处理 {len(all_papers_to_process)} 篇论文。")

if __name__ == "__main__":
    main()
