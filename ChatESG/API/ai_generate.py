from openai import OpenAI
import requests

class GeminiGenerator:
    def __init__(self, api_keys, model_name, generation_config, base_url):
        self.api_keys = api_keys
        self.api_count = len(api_keys)
        self.current_api_key = api_keys[0]
        self.model_name = model_name
        self.generation_config = generation_config
        # 設定當前章節 為了發生錯誤切換 API 不重新生成
        self.active_chapter = ""
        self.base_url = base_url
        # 設定最大重試次數
        self.max_retry = 3
        
        self.client = OpenAI(
            api_key=self.current_api_key,
            base_url=self.base_url
        )


    def switch_api_key(self):
        current_key_index = self.api_keys.index(self.current_api_key)
        next_key_index = (current_key_index + 1) % self.api_count
        self.current_api_key = self.api_keys[next_key_index]
        self.client = OpenAI(
            api_key=self.current_api_key,
            base_url=self.base_url
        )
        print(f"切換到新的API密鑰: {next_key_index + 1}")


    def get_messages(self, category: str, chapter_title: str, sub_chapter_title: str, url: str):
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


    async def generate_text(self, messages, prompt, retry_count=0):
        try:
            response = self.client.chat.completions.create(
                model = self.model_name,
                messages = messages + [{"role": "user", "content": prompt}],
                **self.generation_config
            )
            return response.choices[0].message
        except Exception as e:
            print(f"生成文本時發生錯誤: {e}")
            if retry_count < self.max_retry:
                self.switch_api_key()
                return await self.generate_text(messages, prompt, retry_count + 1)
            else:
                print(f"已達到最大重試次數 {self.max_retry}，無法生成回應")
                return None


async def main():
    # 測試資料
    api_keys = ["AI"]
    model_name = "gemini-2.0-pro-exp-02-05"
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
    chapter_title = "長官的話"
    sub_chapter_title = "長官的話"
    url = "http://localhost:8001/api/報告書範例.json"
    messages = generator.get_messages(category, chapter_title, sub_chapter_title, url)
    # print(messages)
    # 生成文本
    prompt = "公司名稱：綠色金控\n\n報告期間：2024年\n\n報告書範疇：本報告書涵蓋的範疇包括 綠色金融控股公司及其全資子公司（綠色銀行、綠色證券、綠色人壽、綠色 投信、綠色 投顧）之企業永續發展實踐與成果。報告書中提到的「綠色金控」、或「本公司」皆指包含以上所有營運個體之整體。\n\n報告書撰寫原則：依據GRI，SASB，TCFD\n\n聯絡資訊：Green Financial Holding Co., Ltd. 地址：106台北市大安區敦化南路一段233號10樓 電話：(02)2709-2888 傳真：(02)2709-2899 信箱：green@greenfinancial.com.tw 網站\n：www.greenfinancial.com.tw"
    response = await generator.generate_text(messages, prompt)
    print(response.content)


if __name__ == "__main__":
    # 運行異步函數
    import asyncio
    asyncio.run(main())
