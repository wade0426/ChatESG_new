import json
import os
import time
import shutil
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from opencc import OpenCC

os.environ['KMP_DUPLICATE_LIB_OK']='TRUE'

# ... 其餘原有的 import ...

cc = OpenCC('t2s')
ccs2t = OpenCC('s2t')

model_name = "chuxin-llm/Chuxin-Embedding"
model_kwargs = {'device': 'cuda'}
embedding = HuggingFaceEmbeddings(model_name=model_name,model_kwargs=model_kwargs)

# 定義 Document 類型
class Document:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata

    def __repr__(self):
        return f"Document(page_content={self.page_content}, metadata={self.metadata})"

def find_most_relevant_answer(question, vectordb=None):
    """
    輸入問題和向量資料庫，輸出最相關的解答
    
    Args:
        question (str): 輸入的問題
        vectordb: 向量資料庫實例，如果為None則自動載入預設路徑的資料庫
    
    Returns:
        tuple: (最相關文檔內容, 文檔來源, 相似度分數)
    """
    if vectordb is None:
        # 指定預設的資料庫路徑
        db_path = r"D:\\NTCUST\\Project\\ChatESG_new\\ChatESG\\API\\rag_file\\db"
        vectordb = Chroma(persist_directory=db_path, embedding_function=embedding)
    
    # 使用繁轉簡進行搜尋
    docs = vectordb.similarity_search_with_score(query=cc.convert(question), k=1)
    
    # 取得第一個最相關的文檔
    most_relevant_doc = docs[0][0]
    score = docs[0][1]
    source = most_relevant_doc.metadata["source"]
    content = ccs2t.convert(most_relevant_doc.page_content)
    
    return content, source, score


if __name__ == "__main__":

    # 如果向量資料庫不存在，則建庫
    if not os.path.exists(f"./db"):
        print("資料庫不存在，開始建庫")

        file_path = "./Standards/Standards.txt"
        result = []

        with open(f"{file_path}", 'r', encoding='utf-8') as open_file:
            content = open_file.read()

        # 進行分割
        sections = content.split("\n\n\n")

        # 將每個段落嵌入並存入result列表
        for i, section in enumerate(sections, start=1):
            if section:
                    # 包含文檔來源和頁碼信息
                result.append(Document(page_content=cc.convert(section), metadata={"source": file_path, "page": i}))
        
            # 如果資料夾存在，則刪除
            if os.path.exists(f"./db"):shutil.rmtree(f"./db")
            #灌库
        try:
            vectordb = Chroma.from_documents(documents=result, embedding=embedding, persist_directory=f"./db")#若要重複罐 檔名需不一樣
        except Exception as e:
            print(f"灌庫失敗{e}")
            time.sleep(10000)
    else:
        print("資料庫已存在")
    
    question = "GRI 201 組織所產生及分配的直接經濟價值"
    content, source, score = find_most_relevant_answer(question)
    print(f"最相關的解答: {content}")

    print("完成")