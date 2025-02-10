import subprocess
import os
import platform
import codecs
import uuid
import asyncio
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


from ai_generate import GeminiGenerator


def find_mmdc_path():
    """
    找到 mmdc 執行檔的完整路徑
    """
    if platform.system() == "Windows":
        # Windows 系統下的預設路徑
        user_profile = os.environ.get("USERPROFILE")
        mmdc_path = os.path.join(user_profile, "AppData", "Roaming", "npm", "mmdc.cmd")
        if os.path.exists(mmdc_path):
            return mmdc_path
    
    # 如果找不到預設路徑，嘗試使用 where/which 命令
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["where", "mmdc"], capture_output=True, text=True)
        else:
            result = subprocess.run(["which", "mmdc"], capture_output=True, text=True)
        
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except:
        pass
    
    return "mmdc"  # 如果都找不到，返回預設命令


def mermaid_to_image(mermaid_code, output_file="output.png", format="png"):
    """
    將 Mermaid 語法轉換成圖片。

    Args:
        mermaid_code: 字串，Mermaid 語法。
        output_file: 字串，輸出圖片檔案名稱 (包含副檔名)。預設為 "output.png"。
        format: 字串，圖片格式，可以是 "png" 或 "svg"。預設為 "png"。
    """
    # 獲取 mmdc 的完整路徑
    mmdc_path = find_mmdc_path()

    # 創建一個臨時檔案來存放 Mermaid 語法，使用 UTF-8 編碼
    with codecs.open(os.path.join(os.getcwd(), "temp.mmd"), 'w', encoding='utf-8') as tmp_file:
        tmp_file.write(mermaid_code)
        temp_mmd_filename = tmp_file.name

    # 構建 Mermaid CLI 命令
    command = [
        mmdc_path,  # 使用完整路徑
        "-i", temp_mmd_filename,
        "-o", output_file
    ]

    if format == "svg":
        command.append("-s")

    try:
        # 執行 Mermaid CLI 命令
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        # 輸出 Mermaid CLI 的標準輸出 (如果有)
        print("Mermaid CLI Output:")
        print(result.stdout)

        print(f"Mermaid 圖片已儲存為: {output_file}")

    except subprocess.CalledProcessError as e:
        # 捕獲 Mermaid CLI 執行錯誤
        print(f"執行 Mermaid CLI 時發生錯誤:")
        print(e.stderr)
        print("請檢查你的 Mermaid 語法是否正確，以及 Mermaid CLI 是否正確安裝並在 PATH 環境變數中。")
        # 拋出錯誤
        # raise e

    except FileNotFoundError:
        print("找不到 Mermaid CLI 命令 'mmdc'。請確認你已經正確安裝 Mermaid CLI 並且 'mmdc' 命令可以在你的環境中執行 (例如已加入 PATH 環境變數)。")

    finally:
        # 清理臨時檔案 (無論成功或失敗都刪除)
        os.remove(temp_mmd_filename)



async def main():

    ESG_Criteria_Assessment = GeminiGenerator(api_keys, model_name, config, base_url, max_retry)

    llm_input = "本報告書旨在全面揭露綠色金控於2024年度在環境（Environmental）、社會（Social）與公司治理（Governance）三大面向的永續發展績效、策略規劃與未來展望。我們秉持公開透明的原則，向所有利益關係人展現綠色金控在永續發展方面的承諾、努力與具體成果。 報告期間： 本報告書涵蓋期間為2024年1月1日至2024年12月31日。部分內容為反映持續性作為，可能涵蓋至報告發布日前之最新資訊。 範疇與邊界： 本報告書涵蓋範圍包括綠色金融控股公司及其所有子公司之營運活動。報告書中提及之「綠色金控」、「本公司」或「我們」皆指綠色金融控股公司及其所有子公司整體。若個別章節涉及特定子公司或業務範疇，將於該章節中另行說明。 編制原則： 本報告書之編制遵循下列國際準則與框架，以確保資訊揭露之完整性、可靠性、可比較性與透明度： 全球報告倡議組織（GRI）永續性報導準則（GRI Standards） 永續會計準則委員會（SASB）準則 氣候相關財務揭露工作小組（TCFD）建議 我們致力於確保報告內容的準確性、實質性、平衡性與及時性，並透過內部查核程序驗證資料的可靠性。 聯絡資訊： 公司名稱： 綠色金融控股公司 (Green Financial Holding Co., Ltd.) (請自行填入貴公司地址) (請自行填入貴公司電話) (請自行填入貴公司傳真) (請自行填入貴公司ESG相關事務聯絡信箱) (請自行填入貴公司網址)"
    reference_data = await ESG_Criteria_Assessment.llm_to_mermaid(llm_input)
    choice = reference_data.choices[0]
    message = choice.message
    content = message.content
    content = content.replace("```mermaid", "").replace("```", "")
    content = content.replace("(", "").replace(")", "")
    print("content: \n```\n", content, "\n```")

    # 生成圖片唯一碼
    unique_id = str(uuid.uuid4())
    output_filename = f"./images/{unique_id}.png"
    mermaid_to_image(content, output_filename, format="png")
    # http://localhost:8001/images/{unique_id}.png


if __name__ == "__main__":
    asyncio.run(main())
    pass