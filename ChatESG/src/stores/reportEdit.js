import { defineStore } from 'pinia'
import { v4 as uuidv4 } from 'uuid'

export const useReportEditStore = defineStore('reportEdit', {
  state: () => ({
    fileName: '未命名報告書',
    company_info_assetID: null,
    standard_template_id: null,
    asset_id: null,
    chapters: []
  }),

  getters: {
    // 獲取所有大章節標題
    chapterTitles: (state) => {
      return state.chapters.map(chapter => chapter.chapterTitle)
    },

    // 根據大章節標題獲取其所有中章節
    getSubChaptersByTitle: (state) => (chapterTitle) => {
      const chapter = state.chapters.find(c => c.chapterTitle === chapterTitle)
      return chapter ? chapter.subChapters : []
    },

    // 根據 BlockID 獲取中章節內容
    getSubChapterContent: (state) => (blockId) => {
      for (const chapter of state.chapters) {
        const subChapter = chapter.subChapters.find(sub => sub.BlockID === blockId)
        if (subChapter) {
          return {
            text_content: subChapter.text_content || '',
            img_content_url: subChapter.img_content_url || []
          }
        }
      }
      return { text_content: '', img_content_url: [] }
    },

    // 獲取檔案名稱
    getFileName: (state) => state.fileName
  },

  actions: {
    // 設定報告書的檔案名稱
    setFileName(fileName) {
      this.fileName = fileName || '未命名報告書'
    },

    setAssetId(assetId) {
      this.asset_id = assetId
    },

    // 設定完整的章節結構
    setChapters(chapters) {
      this.chapters = chapters
    },

    // 新增大章節
    addChapter(chapterTitle) {
      // 檢查是否已存在相同標題的大章節
      if (!this.chapters.some(chapter => chapter.chapterTitle === chapterTitle)) {
        this.chapters.push({
          chapterTitle,
          subChapters: []
        })
        return true
      }
      return false
    },

    // 在指定的大章節下新增中章節
    addSubChapter(chapterTitle, subChapterTitle, BlockID, access_permissions) {
      const chapter = this.chapters.find(c => c.chapterTitle === chapterTitle)
      if (chapter) {
        // 檢查是否已存在相同標題的中章節
        if (!chapter.subChapters.some(sub => sub.subChapterTitle === subChapterTitle)) {
          chapter.subChapters.push({
            subChapterTitle,
            BlockID: BlockID || uuidv4(),
            access_permissions: access_permissions || uuidv4(),
            text_content: '',
            img_content_url: []
          })
          return true
        }
        else {
          return false
        }
      }
    },

    // 更新中章節的文本內容
    updateSubChapterText(blockId, text) {
      for (const chapter of this.chapters) {
        const subChapter = chapter.subChapters.find(sub => sub.BlockID === blockId)
        if (subChapter) {
          subChapter.text_content = text
          break
        }
      }
    },

    // 新增：將 base64 轉換為 URL 的方法
    async convertBase64ToUrl(base64String) {
      try {
        const response = await fetch(`http://localhost:8000/api/base64_to_url`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            base64_string: base64String
          })
        })
        const data = await response.json()
        return data
      } catch (error) {
        console.error('轉換圖片格式時發生錯誤:', error)
        throw error
      }
    },

    // 更新中章節的圖片內容
    async updateSubChapterImages(blockId, images) {
      try {
        for (const chapter of this.chapters) {
          const subChapter = chapter.subChapters.find(sub => sub.BlockID === blockId)
          if (subChapter) {
            // 處理每張圖片
            const processedImages = await Promise.all(images.map(async image => {
              let imageUrl = image.url || image
              // 檢查是否為 base64 格式
              if (imageUrl.startsWith('data:image')) {
                imageUrl = await this.convertBase64ToUrl(imageUrl)
              }
              return {
                url: imageUrl,
                title: image.title || '',
                subtitle: image.subtitle || ''
              }
            }))
            
            subChapter.img_content_url = processedImages
            break
          }
        }
      } catch (error) {
        console.error('更新圖片時發生錯誤:', error)
        throw error
      }
    },

    // 刪除大章節及其所有中章節
    removeChapter(chapterTitle) {
      const index = this.chapters.findIndex(c => c.chapterTitle === chapterTitle)
      if (index !== -1) {
        this.chapters.splice(index, 1)
        this.deleteReportOutline(chapterTitle)
      }
    },

    // 刪除特定大章節下的中章節
    removeSubChapter(chapterTitle, subChapterTitle) {
      const chapter = this.chapters.find(c => c.chapterTitle === chapterTitle)
      this.removeSubChapter_api(chapterTitle, subChapterTitle)
      // console.log("removeSubChapter", chapterTitle, subChapterTitle)
      if (chapter) {
        const subIndex = chapter.subChapters.findIndex(
          sub => sub.subChapterTitle === subChapterTitle
        )
        if (subIndex !== -1) {
          chapter.subChapters.splice(subIndex, 1)
        }
      }
    },

    // 初始化示例數據
    async initializeDefaultChapters(data) {
      try {
        const response = await this.fetchReportData(data)
        if (response.status === 'success') {
          const reportData = response.data
          this.setFileName(reportData.assetName)
          this.company_info_assetID = reportData.company_info_assetID
          this.standard_template_id = reportData.standard_template_id
          
          // 設置章節結構
          if (reportData.content && reportData.content.chapters) {
            this.chapters = reportData.content.chapters.map(chapter => ({
              chapterTitle: chapter.chapterTitle,
              guidelines: chapter.guidelines || {},
              subChapters: chapter.subChapters.map(subChapter => ({
                subChapterTitle: subChapter.subChapterTitle,
                BlockID: subChapter.BlockID,
                access_permissions: subChapter.access_permissions,
                text_content: '',
                img_content_url: []
              }))
            }))

            // 獲取每個 block 的內容
            for (const chapter of this.chapters) {
              for (const subChapter of chapter.subChapters) {
                const blockData = await this.fetchReportBlockData({
                  block_id: subChapter.BlockID
                })
                if (blockData.status === 'success') {
                  const content = blockData.data.content.content
                  subChapter.text_content = content.text || ''
                  subChapter.img_content_url = content.images || []
                }
              }
            }
          }
        } else {
          console.error('獲取報告書數據失敗')
        }
      } catch (error) {
        console.error('初始化章節數據時發生錯誤:', error)
      }
    },

    // 使用API獲取報告書大綱
    async fetchReportData(data) {
      const response = await fetch(`http://localhost:8000/api/report/get_report_data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          organization_id: data.organization_id,
          asset_id: data.asset_id
        })
      })
      const responseData = await response.json()
      console.log("responseData_report", responseData) // 測試
      return responseData
    },


    // 使用API獲取報告書Block內容
    async fetchReportBlockData(data) {
      const response = await fetch(`http://localhost:8000/api/report/get_report_block_data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          block_id: data.block_id
        })
      })
      const responseData = await response.json()
      console.log("responseData_block", responseData) // 測試
      return responseData
    },

    // 使用API更新報告書Block內容
    async updateReportBlockData(BlockId, user_id) {
      try {
        const rawContent = this.getSubChapterContent(BlockId)
        
        let subChapterTitle = ''
        for (const chapter of this.chapters) {
          const subChapter = chapter.subChapters.find(sub => sub.BlockID === BlockId)
          if (subChapter) {
            subChapterTitle = subChapter.subChapterTitle
            break
          }
        }
    
        // 修改 content 格式以符合後端期望
        const content = {
          BlockID: BlockId,
          subChapterTitle: subChapterTitle,
          content: {
            text: rawContent.text_content || '',
            images: rawContent.img_content_url.map(img => {
              return {
                url: img.url || img,
                title: img.title || '',
                subtitle: img.subtitle || ''
              }
            }),
            guidelines: {},
            comments: []  // 保持空陣列
          }
        }
        
        console.log("formatted content", content)
        
        const response = await fetch(`http://localhost:8000/api/report/update_report_block_data`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            block_id: BlockId,
            content: content,
            user_id: user_id
          })
        })
        
        const responseData = await response.json()
        if (!response.ok) {
          throw new Error(responseData.detail || '更新失敗')
        }
        console.log("responseData_update", responseData)
        return responseData
      } catch (error) {
        console.error('更新報告書Block內容時發生錯誤:', error)
        throw error
      }
    },

    // 更新報告書大綱(拖移順序)
    async updateReportOutline() {
      try {
        // 準備要傳送的內容
        const content = {
          company_info_assetID: this.company_info_assetID,
          standard_template_id: this.standard_template_id,
          chapters: this.chapters
        }

        const response = await fetch(`http://localhost:8000/api/report/update_report_outline`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            asset_id: this.asset_id,
            content: content
          })
        })

        const responseData = await response.json()
        if (!response.ok) {
          throw new Error(responseData.detail || '更新失敗')
        }

        console.log("更新報告書大綱成功", responseData)
        return responseData
      } catch (error) {
        console.error('更新報告書大綱時發生錯誤:', error)
        throw error
      }
    },

    // 更新報告書大綱(新增章節標題)
    async updateReportOutlineAddChapterTitle(chapterTitle, asset_id) {
      try {
        const response = await fetch(`http://localhost:8000/api/report/update_report_outline_add_chapter_title`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            asset_id: asset_id,
            chapterTitle: chapterTitle
          })
        });

        const responseData = await response.json();
        if (!response.ok) {
          throw new Error(responseData.detail || '新增章節標題失敗');
        }

        // 如果後端更新成功，同步更新前端的狀態
        if (responseData.status === 'success') {
          // 只在後端更新成功時更新前端狀態
          this.addChapter(chapterTitle);
          console.log("新增章節標題成功", responseData);
        }

        return responseData;
      } catch (error) {
        console.error('新增章節標題時發生錯誤:', error);
        throw error;
      }
    },

    // 更新報告書_章節標題_大章節
    async updateReportOutlineRenameChapterTitle(chapterTitle, newChapterTitle) {
      const asset_id = this.asset_id
      try {
        const response = await fetch(`http://localhost:8000/api/report/rename_chapter_title`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            asset_id: asset_id,
            chapter_title: chapterTitle,
            new_chapter_title: newChapterTitle
          })
        });

        const responseData = await response.json();
        if (!response.ok) {
          throw new Error(responseData.detail || '更新章節標題失敗');
        }

        // 如果後端更新成功，同步更新前端的狀態
        if (responseData.status === 'success') {
          // 找到並更新對應章節的標題
          const chapter = this.chapters.find(c => c.chapterTitle === chapterTitle);
          if (chapter) {
            chapter.chapterTitle = newChapterTitle;
          }
          console.log("更新章節標題成功", responseData);
        }

        return responseData;
      } catch (error) {
        console.error('更新章節標題時發生錯誤:', error);
        throw error;
      }
    },

    // 刪除報告書大章節
    async deleteReportOutline(chapterTitle) {
      try {
        const asset_id = this.asset_id;
        const response = await fetch(`http://localhost:8000/api/report/delete_report_outline`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ asset_id: asset_id, chapterTitle: chapterTitle })
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || '刪除章節失敗');
        }

        const result = await response.json();
        
        // 如果刪除成功，重新獲取報告書內容
        // if (result.status === 'success') {
        //   await this.getReportData();
        // }

        return result;
      } catch (error) {
        console.error('刪除章節時發生錯誤:', error);
        throw error;
      }
    },

    // 新增報告書中章節
    async addSubChapter_api(chapterTitle, subChapterTitle, user_id, organization_id) {
      try {
        const asset_id = this.asset_id
        const response = await fetch(`http://localhost:8000/api/report/add_subchapter`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            asset_id: asset_id,
            chapter_title: chapterTitle,
            subchapter_title: subChapterTitle,
            user_id: user_id
          })
        })

        const responseData = await response.json()
        if (!response.ok) {
          throw new Error(responseData.detail || '新增子章節失敗')
        }

        // 如果後端更新成功，同步更新前端的狀態
        if (responseData.status === 'success') {
          const { block_id, access_permissions } = responseData.data
          // 使用現有的 addSubChapter action 更新前端狀態
          this.addSubChapter(chapterTitle, subChapterTitle, block_id, access_permissions)
          console.log("新增子章節成功", responseData)
          const data = {
            asset_id: this.asset_id,
            organization_id: organization_id
          }
          await this.initializeDefaultChapters(data)
        }

        return responseData
      } catch (error) {
        console.error('新增子章節時發生錯誤:', error)
        throw error
      }
    },

    // 更新報告書中章節名稱
    async updateReportOutlineRenameSubChapterTitle(chapterTitle, subChapterTitle, new_subChapterTitle) {
      const asset_id = this.asset_id
      try {
        const response = await fetch(`http://localhost:8000/api/report/rename_subchapter`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            AssetID: asset_id,
            chapterTitle: chapterTitle,
            subChapterTitle: subChapterTitle,
            new_subChapterTitle: new_subChapterTitle
          })
        })

        const responseData = await response.json()
        if (!response.ok) {
          throw new Error(responseData.detail || '更新子章節標題失敗')
        }

        // 如果後端更新成功，同步更新前端的狀態
        if (responseData.status === 'success') {
          // 找到並更新對應子章節的標題
          const chapter = this.chapters.find(c => c.chapterTitle === chapterTitle)
          if (chapter) {
            const subChapter = chapter.subChapters.find(s => s.subChapterTitle === subChapterTitle)
            if (subChapter) {
              subChapter.subChapterTitle = new_subChapterTitle
            }
          }
          console.log("更新子章節標題成功", responseData)
        }

        return responseData
      } catch (error) {
        console.error('更新子章節標題時發生錯誤:', error)
        throw error
      }
    },

    // 刪除報告書中章節
    async removeSubChapter_api(chapterTitle, subChapterTitle) {
      try {
        const asset_id = this.asset_id
        const response = await fetch(`http://localhost:8000/api/report/delete_subchapter`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            AssetID: asset_id,  // 修正參數名稱為 AssetID
            chapterTitle: chapterTitle,
            subChapterTitle: subChapterTitle 
          })
        })

        const responseData = await response.json()
        if (!response.ok) {
          throw new Error(responseData.detail || '刪除子章節失敗')
        }

        // 如果後端更新成功，同步更新前端的狀態
        if (responseData.status === 'success') {
          console.log("刪除子章節成功", responseData)
        }

        return responseData
      } catch (error) {
        console.error('刪除子章節時發生錯誤:', error)
        throw error
      }
    },

    // 生成報告書文字
    async generateText(chapterTitle, subChapterTitle) {
      try {
        const company_info_assetID = this.company_info_assetID
        const response = await fetch(`http://localhost:8000/api/report/generate_text`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            company_info_assetID: company_info_assetID, 
            chapter_title: chapterTitle, 
            sub_chapter_title: subChapterTitle 
          })
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.detail || '生成文字失敗')
        }

        const responseData = await response.json()
        if (responseData.status === 'success') {
          // console.log("生成文字成功", responseData)
          return responseData
        } else {
          throw new Error('生成文字失敗')
        }
      } catch (error) {
        console.error('生成報告書文字時發生錯誤:', error)
        throw error
      }
    },

    // 準則檢驗
    async verification_criteria_by_chapter(chapterTitle, chapterTitle_text_content) {
      try {
        const response = await fetch(`http://localhost:8002/api/report/gri_verification_criteria_by_chapter`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chapterTitle_text_content: chapterTitle_text_content
          })
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.detail || '準則檢驗失敗')
        }

        const responseData = await response.json()
        if (responseData.status === 'success') {
          console.log("準則檢驗成功", responseData)
          
          // 從輸入的文本中提取章節標題
          const titleMatch = chapterTitle_text_content.match(/標題：(.+?)\n/)
          if (titleMatch) {
            const chapterTitle = titleMatch[1]
            // 找到對應的章節並更新其 guidelines
            const chapter = this.chapters.find(c => c.chapterTitle === chapterTitle)
            if (chapter) {
              chapter.guidelines = responseData.data
            }
          }
          await this.updateVerificationResult(chapterTitle, responseData.data)
          
          return responseData
        } else {
          throw new Error('準則檢驗失敗')
        }
      } catch (error) {
        console.error('準則檢驗時發生錯誤:', error)
        throw error
      }
    },

    // 更新檢驗結果
    async updateVerificationResult(chapterTitle, guidelines) {
      try {
        const response = await fetch(`http://localhost:8000/api/report/update_verification_result`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            AssetID: this.asset_id,
            chapterTitle: chapterTitle,
            guidelines: guidelines
          })
        });

        const responseData = await response.json();
        if (!response.ok) {
          throw new Error(responseData.detail || '更新檢驗結果失敗');
        }

        // 如果後端更新成功，同步更新前端的狀態
        if (responseData.status === 'success') {
          // 找到並更新對應章節的 guidelines
          const chapter = this.chapters.find(c => c.chapterTitle === chapterTitle);
          if (chapter) {
            chapter.guidelines = guidelines;
          }
          console.log("更新檢驗結果成功", responseData);
        }

        return responseData;
      } catch (error) {
        console.error('更新檢驗結果時發生錯誤:', error);
        throw error;
      }
    }
  }
})