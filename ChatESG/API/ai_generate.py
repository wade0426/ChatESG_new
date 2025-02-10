from openai import OpenAI
import requests
from dotenv import load_dotenv
import os
import json

# 載入 .env 檔案
load_dotenv()

api_keys = list(json.loads(os.getenv("api_keys")))
model_name = os.getenv("model_name")
config = os.getenv("config")
config = dict(json.loads(config))
base_url = os.getenv("base_url")
max_retry = int(os.getenv("max_retry"))

class GeminiGenerator:
    def __init__(self, api_keys, model_name, generation_config, base_url, max_retry):
        self.api_keys = api_keys
        self.api_count = len(api_keys)
        self.current_api_key = api_keys[0]
        self.model_name = model_name
        self.generation_config = generation_config
        # 設定當前章節 為了發生錯誤切換 API 不重新生成
        self.active_chapter = ""
        self.base_url = base_url
        # 設定最大重試次數
        self.max_retry = max_retry
        
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


    # 透過 LLM 將輸入的文字轉換成 Mermaid 語法
    async def llm_to_mermaid(self, llm_input, reference_data=None, retry_count=0):
        """
        透過 LLM 將輸入的文字轉換成 Mermaid 語法
        輸入: 文字, 參考資料
        輸出: Mermaid 語法
        """
        try:
            if reference_data is None:
                reference_data = "flowchart TD\n    %% 定義顏色和樣式\n    classDef topLevel fill:#008080, color:#fff, stroke:#005050, stroke-width:1px, rx:5px, ry:5px\n    classDef committee fill:#004080, color:#fff, stroke:#002060, stroke-width:1px, rx:5px, ry:5px\n    classDef subgroup fill:#a8e0a8, color:#000, stroke:#70c070, stroke-width:1px, rx:5px, ry:5px\n    classDef socialGroup fill:#ffbb33, color:#000, stroke:#e09b20, stroke-width:1px, rx:5px, ry:5px\n    classDef governanceGroup fill:#66b3ff, color:#000, stroke:#3399ff, stroke-width:1px, rx:5px, ry:5px\n    classDef item fill:#f0f0f0, color:#000, stroke:#ccc, stroke-width:1px, rx:3px, ry:3px\n\n    %% 節點定義與連接\n    A[董事會]:::topLevel --> B[總經理室]:::topLevel\n    B --> C[金寶永續發展委員會]:::committee\n    C --> D[金寶 ESG 工作小組]\n\n    D --> E[fa:fa-leaf 環境永續 小組]:::subgroup\n    D --> F[fa:fa-handshake 社會共融 小組]:::socialGroup\n    D --> G[fa:fa-bullseye 永續治理 小組]:::governanceGroup\n\n    E --> E1[供應鏈管理]:::item\n    E --> E2[責任礦產管理]:::item\n    E --> E3[限禁用物質管理]:::item\n    E --> E4[供應鏈永續管理]:::item\n    E --> E5[綠色採購]:::item\n    E --> E6[在地採購]:::item\n    E --> E7[永續生產]:::item\n    E --> E8[溫室氣體管理]:::item\n    E --> E9[能源管理]:::item\n    E --> E10[綠色產品設計]:::item\n    E --> E11[水資源管理]:::item\n    E --> E12[廢棄物管理]:::item\n\n    F --> F1[員工照顧]:::item\n    F --> F2[友善工作環境]:::item\n    F --> F3[薪酬與福利]:::item\n    F --> F4[勞資關係]:::item\n    F --> F5[教育訓練]:::item\n    F --> F6[社會參與]:::item\n    F --> F7[弱勢關懷]:::item\n    F --> F8[公益活動]:::item\n    F --> F9[社區參與]:::item\n\n    G --> G1[公司治理]:::item\n    G --> G2[經濟績效]:::item\n    G --> G3[誠信經營]:::item\n    G --> G4[法規遵循]:::item\n    G --> G5[資訊安全]:::item\n    G --> G6[智慧財產權]:::item"
            prompt_input_content = f"文字描述: ```{llm_input}```\n\nMermaid 語法參考範例: ```{reference_data}```"
            response = self.client.chat.completions.create(
                model = self.model_name,
                messages = [
                    {"role": "system", "content": "你是一位擁有極高美感與藝術修養的視覺設計師。我將提供文字描述以及 Mermaid 語法的參考範例。請根據我提供的文字內容中描述的設計元素、佈局和層次結構，生成與文字對應的 Mermaid 語法。請遵循以下要求：\n\n1. 仔細理解文字描述：請詳細閱讀並理解我提供的文字內容，抓住其中的設計思路、主要元素、佈局安排和層次關係。\n2. 參考 Mermaid 範例：參照提供的 Mermaid 語法範例，確保輸出語法格式正確，並根據情境選擇合適的圖表類型（例如：flowchart、sequence diagram、class diagram 等）。\n3. 生成對應語法：根據文字描述中的內容，生成能夠完整反映設計元素、佈局和層次結構的 Mermaid 語法。\n4. 保持語法精確與清晰：確保生成的 Mermaid 語法邏輯清晰、易讀，並正確展現設計意圖。\n\n請開始根據我後續提供的文字描述和參考範例生成對應的 Mermaid 語法。"},
                    {"role": "user", "content": f"input: {prompt_input_content}"},
                ],
                **self.generation_config
            )
            # 每次請求後，切換 API 密鑰
            self.switch_api_key()
            return response
        
        except Exception as e:
            print(f"生成對應的 GRI 準則時發生錯誤: {e}")
            if retry_count < self.max_retry:
                self.switch_api_key()
                return await self.llm_to_mermaid(prompt_input_content, reference_data, retry_count + 1)
            else:
                print(f"已達到最大重試次數 {self.max_retry}，無法生成回應，請聯絡客服")
                return None


async def main():

    # 建立物件
    generator = GeminiGenerator(api_keys, model_name, config, base_url, max_retry)
    # 獲取訓練數據
    category = "金融業"
    chapter_title = "長官的話"
    sub_chapter_title = "長官的話"
    url = "http://localhost:8001/api/Sample_Report.json"
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
