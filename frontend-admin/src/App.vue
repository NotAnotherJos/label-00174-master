<template>
  <div class="app-container">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="header-content">
        <div class="logo">
          <svg class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          <span class="logo-text">报文批阅系统</span>
        </div>
        <div class="header-stats" v-if="stats.total > 0">
          <span class="stat-item">
            <span class="stat-value">{{ stats.total }}</span>
            <span class="stat-label">批阅记录</span>
          </span>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 上传卡片 -->
      <section class="upload-section fade-in">
        <div class="section-header">
          <h2>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
            </svg>
            上传文件
          </h2>
          <p class="section-desc">上传手抄PDF报文和TXT标准参照文件进行自动批阅</p>
        </div>

        <div class="upload-grid">
          <!-- PDF上传 -->
          <div 
            class="upload-card" 
            :class="{ 'has-file': pdfFile, 'drag-over': pdfDragOver }"
            @dragover.prevent="pdfDragOver = true"
            @dragleave="pdfDragOver = false"
            @drop.prevent="handlePdfDrop"
          >
            <input 
              type="file" 
              ref="pdfInput" 
              accept=".pdf" 
              @change="handlePdfSelect"
              hidden
            />
            <div class="upload-icon pdf-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
                <path d="M12 3v6a1 1 0 001 1h6"/>
                <text x="7" y="17" font-size="5" fill="currentColor" stroke="none">PDF</text>
              </svg>
            </div>
            <div class="upload-info">
              <h3>{{ pdfFile ? pdfFile.name : '手抄报文 PDF' }}</h3>
              <p v-if="pdfFile">{{ formatFileSize(pdfFile.size) }}</p>
              <p v-else>拖拽文件或点击选择</p>
            </div>
            <button class="upload-btn" @click="$refs.pdfInput.click()">
              {{ pdfFile ? '更换文件' : '选择文件' }}
            </button>
          </div>

          <!-- TXT上传 -->
          <div 
            class="upload-card"
            :class="{ 'has-file': txtFile, 'drag-over': txtDragOver }"
            @dragover.prevent="txtDragOver = true"
            @dragleave="txtDragOver = false"
            @drop.prevent="handleTxtDrop"
          >
            <input 
              type="file" 
              ref="txtInput" 
              accept=".txt" 
              @change="handleTxtSelect"
              hidden
            />
            <div class="upload-icon txt-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
                <path d="M12 3v6a1 1 0 001 1h6"/>
                <path d="M9 13h6M9 17h4"/>
              </svg>
            </div>
            <div class="upload-info">
              <h3>{{ txtFile ? txtFile.name : '标准参照 TXT' }}</h3>
              <p v-if="txtFile">{{ formatFileSize(txtFile.size) }}</p>
              <p v-else>拖拽文件或点击选择</p>
            </div>
            <button class="upload-btn" @click="$refs.txtInput.click()">
              {{ txtFile ? '更换文件' : '选择文件' }}
            </button>
          </div>
        </div>

        <!-- 开始批阅按钮 -->
        <div class="action-bar">
          <button 
            class="review-btn"
            :class="{ 'loading': isReviewing }"
            :disabled="!canReview || isReviewing"
            @click="startReview"
          >
            <svg v-if="!isReviewing" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <svg v-else class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" stroke-dasharray="60" stroke-dashoffset="20"/>
            </svg>
            {{ isReviewing ? '批阅中...' : '开始批阅' }}
          </button>
        </div>
      </section>

      <!-- 结果显示 -->
      <section v-if="currentResult" class="result-section fade-in">
        <div class="section-header">
          <h2>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            批阅结果
          </h2>
        </div>

        <!-- 得分展示 -->
        <div class="score-display">
          <div class="score-circle" :class="getScoreClass(currentResult.score)">
            <span class="score-value">{{ currentResult.score.toFixed(1) }}</span>
            <span class="score-label">分</span>
          </div>
          <div class="score-info">
            <div class="score-meta">
              <span class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                </svg>
                总组数: {{ currentResult.total_groups }}
              </span>
              <span class="meta-item error">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                错误数: {{ currentResult.error_count }}
              </span>
            </div>
            <p class="score-message">{{ currentResult.message }}</p>
          </div>
        </div>

        <!-- 错误详情表格 -->
        <div v-if="currentResult.errors && currentResult.errors.length > 0" class="errors-table-container">
          <h3 class="table-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            错误详情
          </h3>
          <div class="table-wrapper">
            <table class="errors-table">
              <thead>
                <tr>
                  <th>位置</th>
                  <th>提交值</th>
                  <th>正确值</th>
                  <th>类型</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(error, index) in currentResult.errors" :key="index" class="slide-in" :style="{ animationDelay: `${index * 50}ms` }">
                  <td class="position-cell">
                    <span class="position-badge">
                      第{{ error.segment }}段 - 第{{ error.line }}行 - 第{{ error.position }}组
                    </span>
                  </td>
                  <td class="value-cell wrong">
                    <code>{{ error.submitted_value }}</code>
                  </td>
                  <td class="value-cell correct">
                    <code>{{ error.correct_value }}</code>
                  </td>
                  <td class="type-cell">
                    <span class="error-type" :class="error.error_type">
                      {{ getErrorTypeLabel(error.error_type) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 下载报告按钮 -->
        <div class="report-actions">
          <button class="report-btn" @click="downloadReport('text')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
            </svg>
            下载文本报告
          </button>
          <button class="report-btn pdf" @click="downloadReport('pdf')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
            </svg>
            下载PDF报告
          </button>
        </div>
      </section>

      <!-- 历史记录 -->
      <section v-if="reviewHistory.length > 0" class="history-section fade-in">
        <div class="section-header">
          <h2>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            历史记录
          </h2>
        </div>
        <div class="history-list">
          <div 
            v-for="item in reviewHistory" 
            :key="item.id" 
            class="history-item"
            @click="loadResult(item.id)"
          >
            <div class="history-file">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
              </svg>
              <span>{{ item.pdf_filename }}</span>
            </div>
            <div class="history-meta">
              <span class="history-score" :class="getScoreClass(item.score)">
                {{ item.score.toFixed(1) }}分
              </span>
              <span class="history-errors">{{ item.error_count }}处错误</span>
              <span class="history-time">{{ formatTime(item.created_at) }}</span>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- 通知提示 -->
    <div v-if="notification.show" class="notification" :class="notification.type">
      <svg v-if="notification.type === 'success'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
      <span>{{ notification.message }}</span>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

// API基础URL
const API_BASE = '/api'

export default {
  name: 'App',
  data() {
    return {
      pdfFile: null,
      txtFile: null,
      pdfDragOver: false,
      txtDragOver: false,
      isReviewing: false,
      currentResult: null,
      reviewHistory: [],
      stats: { total: 0 },
      notification: {
        show: false,
        type: 'success',
        message: ''
      }
    }
  },
  computed: {
    canReview() {
      return this.pdfFile && this.txtFile
    }
  },
  mounted() {
    this.loadHistory()
  },
  methods: {
    handlePdfSelect(e) {
      const file = e.target.files[0]
      if (file && file.name.toLowerCase().endsWith('.pdf')) {
        this.pdfFile = file
      } else {
        this.showNotification('请选择PDF格式文件', 'error')
      }
    },
    handleTxtSelect(e) {
      const file = e.target.files[0]
      if (file && file.name.toLowerCase().endsWith('.txt')) {
        this.txtFile = file
      } else {
        this.showNotification('请选择TXT格式文件', 'error')
      }
    },
    handlePdfDrop(e) {
      this.pdfDragOver = false
      const file = e.dataTransfer.files[0]
      if (file && file.name.toLowerCase().endsWith('.pdf')) {
        this.pdfFile = file
      } else {
        this.showNotification('请拖拽PDF格式文件', 'error')
      }
    },
    handleTxtDrop(e) {
      this.txtDragOver = false
      const file = e.dataTransfer.files[0]
      if (file && file.name.toLowerCase().endsWith('.txt')) {
        this.txtFile = file
      } else {
        this.showNotification('请拖拽TXT格式文件', 'error')
      }
    },
    async startReview() {
      if (!this.canReview) return
      
      this.isReviewing = true
      this.currentResult = null
      
      try {
        const formData = new FormData()
        formData.append('pdf_file', this.pdfFile)
        formData.append('txt_file', this.txtFile)
        
        const response = await axios.post(`${API_BASE}/review/quick`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        this.currentResult = response.data
        this.showNotification('批阅完成！', 'success')
        this.loadHistory()
      } catch (error) {
        console.error('批阅失败:', error)
        this.showNotification(
          error.response?.data?.detail || '批阅失败，请重试',
          'error'
        )
      } finally {
        this.isReviewing = false
      }
    },
    async loadHistory() {
      try {
        const response = await axios.get(`${API_BASE}/reviews`)
        this.reviewHistory = response.data.items || []
        this.stats.total = response.data.total || 0
      } catch (error) {
        console.error('加载历史记录失败:', error)
      }
    },
    async loadResult(reviewId) {
      try {
        const response = await axios.get(`${API_BASE}/review/${reviewId}`)
        this.currentResult = response.data
      } catch (error) {
        console.error('加载结果失败:', error)
        this.showNotification('加载结果失败', 'error')
      }
    },
    async downloadReport(format) {
      if (!this.currentResult) return
      
      try {
        const response = await axios.get(
          `${API_BASE}/review/${this.currentResult.id}/report?format=${format}`,
          { responseType: format === 'pdf' ? 'blob' : 'text' }
        )
        
        const blob = format === 'pdf' 
          ? new Blob([response.data], { type: 'application/pdf' })
          : new Blob([response.data], { type: 'text/plain' })
        
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `report_${this.currentResult.id}.${format === 'pdf' ? 'pdf' : 'txt'}`
        a.click()
        URL.revokeObjectURL(url)
        
        this.showNotification('报告下载成功', 'success')
      } catch (error) {
        console.error('下载报告失败:', error)
        this.showNotification('下载报告失败', 'error')
      }
    },
    showNotification(message, type = 'success') {
      this.notification = { show: true, type, message }
      setTimeout(() => {
        this.notification.show = false
      }, 3000)
    },
    formatFileSize(bytes) {
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
      return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    },
    formatTime(isoString) {
      const date = new Date(isoString)
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    getScoreClass(score) {
      if (score >= 90) return 'excellent'
      if (score >= 80) return 'good'
      if (score >= 60) return 'pass'
      return 'fail'
    },
    getErrorTypeLabel(type) {
      const labels = {
        mismatch: '内容错误',
        missing: '内容缺失',
        extra: '多余内容'
      }
      return labels[type] || type
    }
  }
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Header */
.header {
  background: rgba(26, 26, 46, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-icon {
  width: 32px;
  height: 32px;
  color: var(--accent-cyan);
}

.logo-text {
  font-size: 1.25rem;
  font-weight: 600;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-violet));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-stats {
  display: flex;
  gap: 1.5rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--accent-emerald);
  font-family: var(--font-mono);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* Main Content */
.main-content {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  width: 100%;
}

/* Section */
.section-header {
  margin-bottom: 1.5rem;
}

.section-header h2 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.section-header h2 svg {
  width: 24px;
  height: 24px;
  color: var(--accent-cyan);
}

.section-desc {
  color: var(--text-secondary);
  margin-top: 0.25rem;
  font-size: 0.875rem;
}

/* Upload Section */
.upload-section {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
  border: 1px solid var(--border-color);
}

.upload-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.upload-card {
  background: var(--bg-secondary);
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
}

.upload-card:hover {
  border-color: var(--accent-cyan);
  background: rgba(34, 211, 238, 0.05);
}

.upload-card.drag-over {
  border-color: var(--accent-cyan);
  background: rgba(34, 211, 238, 0.1);
  transform: scale(1.02);
}

.upload-card.has-file {
  border-style: solid;
  border-color: var(--accent-emerald);
  background: rgba(16, 185, 129, 0.05);
}

.upload-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 1rem;
  color: var(--text-muted);
}

.upload-card.has-file .upload-icon {
  color: var(--accent-emerald);
}

.pdf-icon {
  color: var(--accent-rose);
}

.upload-card.has-file .pdf-icon {
  color: var(--accent-emerald);
}

.txt-icon {
  color: var(--accent-amber);
}

.upload-card.has-file .txt-icon {
  color: var(--accent-emerald);
}

.upload-info h3 {
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
  color: var(--text-primary);
  word-break: break-all;
}

.upload-info p {
  font-size: 0.875rem;
  color: var(--text-muted);
}

.upload-btn {
  margin-top: 1rem;
  padding: 0.5rem 1.5rem;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.upload-btn:hover {
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
}

/* Action Bar */
.action-bar {
  display: flex;
  justify-content: center;
}

.review-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 3rem;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-violet));
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 1.125rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: var(--shadow-lg);
}

.review-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow);
}

.review-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.review-btn svg {
  width: 24px;
  height: 24px;
}

.review-btn.loading svg.spin {
  animation: spin 1s linear infinite;
}

/* Result Section */
.result-section {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
  border: 1px solid var(--border-color);
}

.score-display {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 2rem;
  background: var(--bg-secondary);
  border-radius: 12px;
  margin-bottom: 2rem;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border: 4px solid;
  flex-shrink: 0;
}

.score-circle.excellent {
  border-color: var(--accent-emerald);
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
}

.score-circle.good {
  border-color: var(--accent-cyan);
  box-shadow: 0 0 20px rgba(34, 211, 238, 0.3);
}

.score-circle.pass {
  border-color: var(--accent-amber);
  box-shadow: 0 0 20px rgba(245, 158, 11, 0.3);
}

.score-circle.fail {
  border-color: var(--accent-rose);
  box-shadow: 0 0 20px rgba(244, 63, 94, 0.3);
}

.score-value {
  font-size: 2.5rem;
  font-weight: 700;
  font-family: var(--font-mono);
  line-height: 1;
}

.score-circle.excellent .score-value { color: var(--accent-emerald); }
.score-circle.good .score-value { color: var(--accent-cyan); }
.score-circle.pass .score-value { color: var(--accent-amber); }
.score-circle.fail .score-value { color: var(--accent-rose); }

.score-label {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.score-info {
  flex: 1;
}

.score-meta {
  display: flex;
  gap: 2rem;
  margin-bottom: 1rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  color: var(--text-secondary);
}

.meta-item svg {
  width: 20px;
  height: 20px;
}

.meta-item.error {
  color: var(--accent-rose);
}

.score-message {
  font-size: 1.125rem;
  color: var(--text-primary);
}

/* Errors Table */
.errors-table-container {
  margin-bottom: 2rem;
}

.table-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 1rem;
}

.table-title svg {
  width: 20px;
  height: 20px;
  color: var(--accent-amber);
}

.table-wrapper {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.errors-table {
  width: 100%;
  border-collapse: collapse;
}

.errors-table th,
.errors-table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.errors-table th {
  background: var(--bg-tertiary);
  font-weight: 500;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.errors-table tr:hover {
  background: var(--bg-hover);
}

.position-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: var(--bg-tertiary);
  border-radius: 4px;
  font-size: 0.875rem;
  font-family: var(--font-mono);
  color: var(--text-secondary);
}

.value-cell code {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 0.9375rem;
}

.value-cell.wrong code {
  background: rgba(244, 63, 94, 0.15);
  color: var(--accent-rose);
}

.value-cell.correct code {
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent-emerald);
}

.error-type {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.error-type.mismatch {
  background: rgba(244, 63, 94, 0.15);
  color: var(--accent-rose);
}

.error-type.missing {
  background: rgba(245, 158, 11, 0.15);
  color: var(--accent-amber);
}

.error-type.extra {
  background: rgba(139, 92, 246, 0.15);
  color: var(--accent-violet);
}

/* Report Actions */
.report-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.report-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.report-btn:hover {
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
}

.report-btn.pdf:hover {
  border-color: var(--accent-rose);
  color: var(--accent-rose);
}

.report-btn svg {
  width: 20px;
  height: 20px;
}

/* History Section */
.history-section {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid var(--border-color);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: var(--bg-secondary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.history-item:hover {
  background: var(--bg-hover);
  border-color: var(--border-color);
}

.history-file {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--text-primary);
}

.history-file svg {
  width: 20px;
  height: 20px;
  color: var(--accent-cyan);
}

.history-meta {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.history-score {
  font-weight: 600;
  font-family: var(--font-mono);
}

.history-score.excellent { color: var(--accent-emerald); }
.history-score.good { color: var(--accent-cyan); }
.history-score.pass { color: var(--accent-amber); }
.history-score.fail { color: var(--accent-rose); }

.history-errors {
  color: var(--text-muted);
  font-size: 0.875rem;
}

.history-time {
  color: var(--text-muted);
  font-size: 0.875rem;
  font-family: var(--font-mono);
}

/* Notification */
.notification {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-radius: 12px;
  animation: slideIn 0.3s ease-out;
  z-index: 1000;
}

.notification.success {
  background: rgba(16, 185, 129, 0.95);
  color: white;
}

.notification.error {
  background: rgba(244, 63, 94, 0.95);
  color: white;
}

.notification svg {
  width: 24px;
  height: 24px;
}

/* Responsive */
@media (max-width: 768px) {
  .header-content {
    padding: 1rem;
  }
  
  .main-content {
    padding: 1rem;
  }
  
  .upload-section,
  .result-section,
  .history-section {
    padding: 1.5rem;
  }
  
  .score-display {
    flex-direction: column;
    text-align: center;
  }
  
  .score-meta {
    justify-content: center;
  }
  
  .history-item {
    flex-direction: column;
    gap: 0.75rem;
    align-items: flex-start;
  }
  
  .history-meta {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
