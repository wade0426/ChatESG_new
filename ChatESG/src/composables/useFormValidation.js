import { reactive } from 'vue'

export function useFormValidation(config) {
  const errors = reactive({})

  // 初始化錯誤物件
  if (config.rules) {
    Object.keys(config.rules).forEach(field => {
      errors[field] = ''
    })
  }

  // 驗證表單
  const validateForm = (formData) => {
    let isValid = true
    
    // 重置所有錯誤訊息
    Object.keys(errors).forEach(field => {
      errors[field] = ''
    })

    // 遍歷每個欄位的驗證規則
    Object.keys(config.rules).forEach(field => {
      const rules = config.rules[field]
      const value = formData[field]

      // 遍歷該欄位的所有驗證規則
      for (const rule of rules) {
        // required 驗證
        if (rule.required && !value?.toString().trim()) {
          errors[field] = rule.message
          isValid = false
          break
        }

        // 最大長度驗證
        if (rule.max && value?.toString().length > rule.max) {
          errors[field] = rule.message
          isValid = false
          break
        }

        // 最小長度驗證
        if (rule.min && value?.toString().length < rule.min) {
          errors[field] = rule.message
          isValid = false
          break
        }

        // 正則表達式驗證
        if (rule.pattern && !rule.pattern.test(value)) {
          errors[field] = rule.message
          isValid = false
          break
        }

        // 自定義驗證函數
        if (rule.validator && !rule.validator(value)) {
          errors[field] = rule.message
          isValid = false
          break
        }
      }
    })

    return isValid
  }

  return {
    errors,
    validateForm
  }
} 