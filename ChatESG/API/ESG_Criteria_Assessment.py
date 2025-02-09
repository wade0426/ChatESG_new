from openai import OpenAI
import json

class Gemini_ESG_Criteria_Assessment:
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
        
        try:
            self.client = OpenAI(
                api_key=self.current_api_key,
                base_url=self.base_url
            )
        except Exception as e:
            print(f"取得Gemini API Key發生錯誤: {e}")


    def switch_api_key(self):
        current_key_index = self.api_keys.index(self.current_api_key)
        next_key_index = (current_key_index + 1) % self.api_count
        self.current_api_key = self.api_keys[next_key_index]
        self.client = OpenAI(
            api_key=self.current_api_key,
            base_url=self.base_url
        )
        print(f"切換到新的API密鑰: {next_key_index + 1}")


    # 輸入 一篇 ESG 報告，輸出 對應的 GRI 準則 (json)
    async def generate_gri_criteria(self, esg_report, retry_count=0):
        """
        輸入一篇 ESG 報告，輸出對應的 GRI 準則

        參數:
        esg_report (str): ESG 報告

        返回:
        json: 對應的 GRI 準則
        """
        try:
            response = self.client.chat.completions.create(
                model = self.model_name,
                messages = [
                    {"role": "system", "content": "你是一位 ESG 報告與 GRI 準則的專家分析師。請分析使用者輸入的 ESG 報告內容,並找出相關的 GRI 準則對應項目，使用中文。\n\n輸入:[報告內容]\n\n請依照以下格式輸出分析結果，使用json格式:\n\n1. 相關的 GRI 準則:\n- GRI_Indicators[indicator]：編號\n- GRI_Indicators[description]：章節標題\n\n2. 如果使用者的輸入沒有相關的 GRI 準則，則輸出 沒有相關的 GRI 準則。\n注意：輸出JSON不需要換行空白或其他符號，請輸出壓縮後的JSON。"},
                    {"role": "user", "content": "環境 (Environmental):\n1.參與國際再生能源證書 (I-REC) 買賣，達成 2024 年內使用 25% 綠電目標。\n2.於公司主要營運據點實施廢水回收系統，2023 年總回收水量達 15 百萬公升。\n3.推動淨零碳排策略，2023 年公司碳排放量較 2022 年減少 12%。\n\n社會 (Social):\n1.提供新進員工育兒補助，2023 年補助金額達新臺幣 1,500 萬元，受惠員工人數增加 40%。\n2.開設多元化員工訓練計畫，全年平均每位員工接受訓練時數達 30 小時。\n3.針對弱勢群體，推出專門金融產品及服務，2023 年幫助超過 2,000 位低收入戶改善其金融健康。\n\n治理 (Governance):\n1.董事會中女性比例達 40%，積極推動性別平等政策。\n2.持續進行公司治理評鑑，2023 年被評為全球最佳公司治理之一。\n3.企業風險管理強化措施，2023 年整體風險指數下降 15%。\n\n榮耀與肯定：\n1.連續五年入選 MSCI ESG Ratings，2023 年持續保持 AA 級評等。\n2.2023 年再度入選「道瓊永續世界指數」和「道瓊永續新興市場指數」成分股，成為全球永續發展領先企業之一。\n3.獲得 2023 年「亞太區域最佳永續金融機構」獎項，並被評為該區域最佳創新銀行之一。\n4.連續七年榮獲「台灣企業永續獎」，2023 年榮獲「金融及保險業類白金獎」。"},
                    {"role": "assistant", "content": "{\"GRI_Indicators\":[{\"indicator\":\"GRI 302-1\",\"description\":\"組織內部的能源消耗量\"},{\"indicator\":\"GRI 303-4\",\"description\":\"排水量\"},{\"indicator\":\"GRI 305-1\",\"description\":\"直接（範疇一）溫室氣體排放\"},{\"indicator\":\"GRI 401-1\",\"description\":\"每名員工每年接受訓練的平均時數\"},{\"indicator\":\"GRI 404-2\",\"description\":\"提升員工職能及過渡協助方案\"},{\"indicator\":\"GRI 405-2\",\"description\":\"女性對男性基本薪資與薪酬的比率\"},{\"indicator\":\"GRI 413-2\",\"description\":\"對當地社區具有顯著實際或潛在正面衝擊的營運活動\"}]}"},
                    {"role": "user", "content": "測試"},
                    {"role": "assistant", "content": "{\"GRI_Indicators\":[{\"indicator\":\"沒有相關的 GRI 準則\",\"description\":\"沒有相關的 GRI 準則\"}]}"},
                    {"role": "user", "content": f"input: {esg_report}"},
                ],
                response_format={"type":"json_schema","json_schema":{"name":"gri_indicators_response","strict":True,"schema":{"type":"object","properties":{"GRI_Indicators":{"type":"array","items":{"type":"object","properties":{"indicator":{"type":"string","description":"GRI 指標編號"},"description":{"type":"string","description":"GRI 指標描述"}},"required":["indicator","description"],"additionalProperties":False }}},"additionalProperties":False,"required":["GRI_Indicators"]}}},
                **self.generation_config
            )
            # 每次請求後，切換 API 密鑰
            self.switch_api_key()
            return response
        
        except Exception as e:
            print(f"生成對應的 GRI 準則時發生錯誤: {e}")
            if retry_count < self.max_retry:
                self.switch_api_key()
                return await self.generate_gri_criteria(esg_report, retry_count + 1)
            else:
                print(f"已達到最大重試次數 {self.max_retry}，無法生成回應，請聯絡客服")
                return None
    

    # 輸入 一篇 ESG 報告書的章節內容，輸出檢驗結果
    async def gri_verification_criteria_by_chapter(self, prompt_input_content, retry_count=0):
        try:
            response = self.client.chat.completions.create(
                model = self.model_name,
                messages = [
                    {"role": "system", "content": "你是一位頂尖的 ESG 報告書 GRI 準則檢測專家。你的主要任務是仔細地審查 ESG 報告書內容，精確評估其是否符合 GRI 準則的每一項要求，並提供詳盡、最可執行的改進建議。\n\n請依照以下架構進行分析：\n\n1. 對應 GRI 準則\n- 列出該段內容對應的所有相關 GRI 準則編號和名稱\n- 特別注意 GRI 2-22 等關鍵準則的要求\n\n2. 符合程度評估\n- 完全符合\n- 部分符合\n- 不符合\n並說明評估理由\n\n3. 待補充項目\n針對不完全符合的部分，請詳細列出：\n- 缺少的必要內容\n- 需要補充的具體項目\n- 建議的補充方向和範例\n\n4. 具體建議\n提供明確的改進建議，包括：\n- 內容架構的調整建議\n- 資訊揭露的完整性建議\n- 具體量化指標的建議\n- 策略說明的深度建議\n\n請以 JSON 格式輸出分析結果，確保建議具體可行，且符合 GRI 準則的要求。\n注意：輸出JSON不需要換行空白或其他符號，請輸出壓縮後的JSON。"},
                    {"role": "user", "content": "1.1 永續擘畫\n富邦證券依循 2021 年富邦金控擘劃嶄新永續願景藍圖,擬定「低碳、數位、激勵、影響」四大策略,並將聯合國永續發展目標\n(Sustainable Development Goals, SDGs)納入本業發展策略及核心業務決策,推動本公司 ESG 中長期目標及行動方案。\n本公司於 2023 年 12 月成立「永續發展委員會」,每季呈報董事會。永續發展委員會轄下設有六大永續經營執行小組(以下簡稱 ESG 執\n行小組),由總經理擔任執行長,統籌推動本公司所設定的永續承諾及永續目標,以及短中長期的重點工作計畫。透過設定、追蹤量\n化指標的達成情形,展現本公司實踐永續承諾之行動力。\n永續策略與主軸\n富邦證券秉持富邦金控之「誠信、親切、專業、創新」的企業核心價值,建構誠信經營之企業文化。為落實良好公司治理,本公司持\n續提升法令遵循效能,確保各項業務經營均正直合規;打造資訊安全防護體系,保障客戶權益及穩健營運;制定「風險管理政策」,\n以「辨識、衡量、管理、監督」作為風險管理之架構,有效發揮風險治理及促使永續金融轉型。本公司期望在良好公司治理及誠信經\n營下,能為投資人及所有利害關係人創造長期價值,並運用金融核心職能,推動各項永續行動方案,發揮永續影響力。"},
                    {"role": "assistant", "content": '{"待補充項目":[{"項目":"永續發展願景與策略的具體內容","說明":"目前僅提及四大策略方向，缺乏對永續發展願景的具體闡述，以及四大策略的詳細內容和預期成果。","GRI":"GRI 2-22 組織永續發展方法","建議":"明確說明富邦證券的永續發展願景，並詳細闡述「低碳、數位、激勵、影響」四大策略的具體內涵、目標、行動方案和預期成果。例如，在低碳策略下，可以說明具體的減碳目標、採取的措施等。"},{"項目":"永續發展委員會的運作機制","說明":"僅說明成立永續發展委員會及每季呈報董事會，但缺乏委員會的具體職責、運作方式、成員組成、如何監督和管理 ESG 議題等資訊。","GRI":"GRI 2-22 組織永續發展方法,GRI 2-9 治理結構與組成","建議":"詳細說明永續發展委員會的職責範圍、決策流程、向董事會報告的機制、以及如何確保其有效監督和管理 ESG 議題。補充委員會成員的多元背景和專業知識，以及其在永續發展中的角色。"},{"項目":"ESG 執行小組的職責與分工","說明":"僅提及成立六大 ESG 執行小組，但未說明各小組的具體職責、分工、如何協調運作，以及如何確保各小組有效執行永續發展目標。","GRI":"GRI 2-22 組織永續發展方法","建議":"詳細說明六大 ESG 執行小組的具體名稱、各自負責的永續發展範疇、以及彼此之間的協調機制。明確各小組如何將永續發展目標融入日常營運，並追蹤和評估績效。"},{"項目":"量化指標的具體範例","說明":"提及設定、追蹤量化指標，但未提供具體的量化指標範例，無法評估指標是否具體、可衡量、可達成、相關和時限性 (SMART)。","GRI":"GRI 2-22 組織永續發展方法","建議":"提供至少一到兩個具體的量化指標範例，例如在低碳策略下，可以設定「年度碳排放量減少百分比」作為指標，並說明基準年、目標值和追蹤頻率。"},{"項目":"利害關係人議合","說明":"提及為利害關係人創造長期價值，但未說明如何進行利害關係人議合，以了解其永續發展期望和關切事項，並將其納入永續策略和行動方案中。","GRI":"GRI 2-29 利害關係人議合","建議":"補充說明如何識別和選擇利害關係人，以及透過何種方式（例如問卷調查、訪談、座談會等）與利害關係人進行溝通和議合，以了解他們的永續發展期望和關切事項，並將議合結果納入永續策略和報告中。"}],"具體建議":["在「永續擘畫」章節中，建議更詳細地闡述公司的永續發展願景、策略和目標，使其更具體、可衡量和可追蹤。","針對 GRI 2-22 組織永續發展方法的要求，系統性地補充說明公司在永續發展治理結構、策略制定、目標設定、執行機制、績效評估等方面的具體做法。","建議在報告中加入永續發展委員會和 ESG 執行小組的組織架構圖，更清晰地呈現永續發展治理體系。","在描述量化指標時，提供具體的指標範例，並在後續章節中展示指標的達成情況，以體現公司在永續發展方面的實際行動和績效。","加強利害關係人議合的資訊揭露，說明議合過程、主要議題和回應，展現公司對利害關係人期望的重視。"],"對應_GRI_準則":["GRI 2-22 組織永續發展方法","GRI 2-6 價值觀、原則、標準和行為規範","GRI 2-9 治理結構與組成","GRI 2-29 利害關係人議合"],"符合程度評估":"部分符合"}'},
                    {"role": "user", "content": f"{prompt_input_content}"}
                ],
                response_format={"type":"json_schema","json_schema":{"name":"improvement_suggestions","strict":True,"schema":{"type":"object","properties":{"待補充項目":{"type":"array","items":{"type":"object","properties":{"項目":{"type":"string","description":"需要補充的項目名稱"},"說明":{"type":"string","description":"問題描述"},"GRI":{"type":"string","description":"對應的 GRI 指標編號"},"建議":{"type":"string","description":"針對該項目的具體建議"}},"required":["項目","說明","GRI","建議"],"additionalProperties":False }},"具體建議":{"type":"array","items":{"type":"string","description":"整體性的具體建議"}},"對應_GRI_準則":{"type":"array","items":{"type":"string","description":"所有相關的 GRI 準則"}},"符合程度評估":{"type":"string","description":"整體符合程度的評估結果"}},"required":["待補充項目","具體建議","對應_GRI_準則","符合程度評估"],"additionalProperties":False }}},
                **self.generation_config,
            )
            
            # 獲取響應內容
            choice = response.choices[0]
            message = choice.message
            content = message.content
            
            # 驗證 JSON 格式
            try:
                json_content = json.loads(content)
                # 確保所有必需的字段都存在
                required_fields = ["待補充項目", "具體建議", "對應_GRI_準則", "符合程度評估"]
                for field in required_fields:
                    if field not in json_content:
                        raise ValueError(f"缺少必要字段: {field}")
                        
                # 驗證每個待補充項目的格式
                for item in json_content["待補充項目"]:
                    required_item_fields = ["項目", "說明", "GRI", "建議"]
                    for field in required_item_fields:
                        if field not in item:
                            raise ValueError(f"待補充項目缺少必要字段: {field}")
                # 每次請求後，切換 API 密鑰
                self.switch_api_key()
                return response
                
            except json.JSONDecodeError as e:
                print(f"JSON 解析錯誤: {str(e)}")
                if retry_count < self.max_retry:
                    print("嘗試重新生成回應...")
                    return await self.gri_verification_criteria_by_chapter(prompt_input_content, retry_count + 1)
                else:
                    raise Exception("無法生成有效的 JSON 回應")
            except ValueError as e:
                print(f"JSON 格式錯誤: {str(e)}")
                if retry_count < self.max_retry:
                    print("嘗試重新生成回應...")
                    return await self.gri_verification_criteria_by_chapter(prompt_input_content, retry_count + 1)
                else:
                    raise Exception("生成的 JSON 回應格式不符合要求")
        
        except Exception as e:
            print(f"輸出檢驗結果時發生錯誤: {e}")
            if retry_count < self.max_retry:
                self.switch_api_key()
                return await self.gri_verification_criteria_by_chapter(prompt_input_content, retry_count + 1)
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
        "max_tokens": 1000,
        "top_p": 1,
    }
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    max_retry = 1
    
    # 建立物件
    ESG_Criteria_Assessment = Gemini_ESG_Criteria_Assessment(api_keys, model_name, config, base_url, max_retry)
    
    # 測試資料
    esg_report = "1.4 重大主題分析與管理方針 2023 年為富邦證券第一年編製永續報告書,本年度依內部衝擊度評估問卷及參 考富邦金外部利害關係人關注度結果,並經 ESG 執行小組代表及相關部門主管 討論,藉由此核心小組對公司業務發展、營運目標、永續策略及各項亮點績效 等面向的高度掌握,同時考量公司特性和特色,決定 2023 年永續報告書之重大 主題與一般主題。 重大主題評估流程 富邦證券依據 2021 年版的 GRI 永續報導準則,依據以下四步驟,篩選出本公司 2023 年 9 項重大主題。 鑑別重大主題程序 第一步:蒐集永續議題 本公司參考母公司富邦金控、國內外標竿金融證券同業之永續主題,以及主管 機關之關注焦點,並考量永續會計準則委員會(SASB)之投資銀行與經紀商準則 (Investment Banking & Brokerage)、氣候相關財務揭露建議(TCFD)等國際準則、聯 合國永續發展目標(UN SDGs)等國際趨勢與產業特性,篩選出 16 項永續議題。 第二步:評估衝擊性 由 ESG 執行小組代表及相關部門主管共 33 位,填寫內部衝擊性評估問卷。填寫 人員依據 16 項永續議題,從經濟、環境、社會/人群(含人權)、公司治理 (ESG) 等面向,評估對公司營運可能產生之正面效益和負面衝擊的發生機率和影響程 度,藉以了解各項議題對於公司營運衝擊情形。 第三步:排序、分析與鑑別 透過正面和負面之發生機率與衝擊程度的相乘並加總,計算出各永續議題的衝 擊程度平均分數後,依照分數高低進行永續主題的重要性排序,並交叉比對母 公司富邦金控利害關係人之關注議題,將正負面衝擊排名前 10 之永續主題初步 選為重大主題。 經 ESG 執行小組成員共同評估和討論後,考量氣候行動與永續金融不論在國內 外皆為重大關注焦點,亦為國內主管機關極為重視之議題,故將「氣候行動」 和「永續金融」列入重大主題,並將「永續金融」調整為更貼切其意的「綠色 金融」。排序第 1 和第 2「公司治理」和「誠信經營」因有強烈相關性,故將其 合併為「公司治理與誠信經營」。而排序第 7 的「營運績效」因非富邦金控利害 關係人之關注議題,故將其改列為一般主題。 第四步:確認 鑑別調整後,2023 年本公司 9 項重大主題,由 ESG 執行小組於 2023 年執行成 果會議報告後,提報永續發展委員會討論,並經董事會同意。"
    
    # 取得對應 GRI 準則
    # response = await ESG_Criteria_Assessment.generate_gri_criteria(esg_report)
    # choice = response.choices[0]
    # message = choice.message
    # content = message.content
    # print(content)

    # 取得檢驗結果
    # response = await ESG_Criteria_Assessment.gri_verification_criteria_by_chapter(esg_report)
    # choice = response.choices[0]
    # message = choice.message
    # content = message.content
    # print(content)


if __name__ == "__main__":
    # 運行異步函數
    import asyncio
    asyncio.run(main())
