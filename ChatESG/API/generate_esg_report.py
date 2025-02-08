from ai_generate import GeminiGenerator
import asyncio
import json
import requests

def get_messages(category: str, chapter_title: str, sub_chapter_title: str, url: str):
    """
    獲取特定類別、章節和子章節的訓練數據

    參數:
    category (str): 產業類別，例如：金融業
    chapter_title (str): 章節標題，例如：關於本報告書
    sub_chapter_title (str): 子章節標題，例如：關於本報告書

    返回:
    list: 包含 system prompt 和訓練數據的消息列表
    """
    try:
        # 從 URL 獲取資料
        url = url
        response = requests.get(url)
        response.raise_for_status()  # 檢查請求是否成功
        json_messages = response.json()
        
        # 獲取指定類別的數據
        category_data = json_messages.get(category, {})
        chapters = category_data.get("chapters", [])
        
        # 查找指定章節
        for chapter in chapters:
            if chapter["chapterTitle"] == chapter_title:
                # 搜尋指定子章節
                for sub_chapter in chapter["subChapters"]:
                    if sub_chapter["subChapterTitle"] == sub_chapter_title:
                        messages = []
                        # 添加 system prompt
                        messages.append({
                            "role": "system",
                            "content": sub_chapter["system_prompt"]
                        })
                        # 添加訓練數據
                        for training_data in sub_chapter["data"]:
                            messages.append({
                                "role": "user",
                                "content": training_data["input"]
                            })
                            messages.append({
                                "role": "assistant",
                                "content": training_data["output"]
                            })
                        return messages
        
        # 如果沒有找到匹配的資料，返回空列表
        return []
    except Exception as e:
        print(f"獲取訓練數據時出現錯誤: {e}")
        return []



async def main():
    # 測試資料
    api_keys = ["key1", "key2", "key3"]
    model_name = "gemini-1.5-flash"
    config = {
        "n": 1,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    # 建立物件
    generator = GeminiGenerator(api_keys, model_name, config, base_url)
    # 獲取訓練數據
    category = "金融業"
    chapter_title = "關於本報告書"
    sub_chapter_title = "關於本報告書"
    url = "http://localhost:8001/api/報告書範例.json"
    messages = get_messages(category, chapter_title, sub_chapter_title, url)
    # 生成文本
    prompt = "公司名稱：綠色金控"
    response = await generator.generate_text(messages, prompt)
    print(response.content)

if __name__ == "__main__":
    asyncio.run(main())

