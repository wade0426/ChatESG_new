import { defineStore } from 'pinia'
import { v4 as uuidv4 } from 'uuid'

export const useReportEditStore = defineStore('reportEdit', {
  state: () => ({
    fileName: '未命名報告書',
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
      }
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

    // 更新中章節的圖片內容
    updateSubChapterImages(blockId, images) {
      for (const chapter of this.chapters) {
        const subChapter = chapter.subChapters.find(sub => sub.BlockID === blockId)
        if (subChapter) {
          subChapter.img_content_url = images.map(image => ({
            url: image.url || image,
            title: image.title || '',
            subtitle: image.subtitle || ''
          }))
          break
        }
      }
    },

    // 刪除大章節及其所有中章節
    removeChapter(chapterTitle) {
      const index = this.chapters.findIndex(c => c.chapterTitle === chapterTitle)
      if (index !== -1) {
        this.chapters.splice(index, 1)
      }
    },

    // 刪除特定大章節下的中章節
    removeSubChapter(chapterTitle, subChapterTitle) {
      const chapter = this.chapters.find(c => c.chapterTitle === chapterTitle)
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
          
          // 設置章節結構
          if (reportData.content && reportData.content.chapters) {
            this.chapters = reportData.content.chapters.map(chapter => ({
              chapterTitle: chapter.chapterTitle,
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
    }
  }
}) 