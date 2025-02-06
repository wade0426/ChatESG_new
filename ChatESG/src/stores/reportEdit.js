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
    }
  },

  actions: {
    // 設定報告書的檔案名稱
    setFileName(fileName) {
      this.fileName = fileName
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
            BlockID: BlockID || uuidv4(), // 如果沒有提供 BlockID，則生成新的 UUID
            access_permissions: access_permissions || uuidv4() // 如果沒有提供 access_permissions，則生成新的 UUID
          })
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
    initializeDefaultChapters() {
      this.chapters = [
        {
          chapterTitle: '永續發展策略',
          subChapters: [
            {
              subChapterTitle: '永續治理架構',
              BlockID: uuidv4(),
              access_permissions: uuidv4()
            }
          ]
        },
        {
          chapterTitle: '經濟績效',
          subChapters: [
            {
              subChapterTitle: '營運財務概況',
              BlockID: uuidv4(),
              access_permissions: uuidv4()
            },
            {
              subChapterTitle: '收入概況',
              BlockID: uuidv4(),
              access_permissions: uuidv4()
            }
          ]
        }
      ]
    }
  }
}) 