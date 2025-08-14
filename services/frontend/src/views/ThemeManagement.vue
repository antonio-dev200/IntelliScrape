<template>
  <div class="theme-management">
    <h2>主题配置与分析</h2>

    <div class="card">
      <h3>1. 发起一个新的分析任务</h3>
      <form @submit.prevent="handleAnalysisRequest">
        <div class="form-group">
          <label for="theme-name">主题名称:</label>
          <input id="theme-name" v-model="themeName" type="text" placeholder="例如：公司财务报告" required />
        </div>
        <div class="form-group">
          <label for="data-source-id">数据源ID:</label>
          <input id="data-source-id" v-model.number="dataSourceId" type="number" placeholder="例如：1" required />
        </div>
        <button type="submit" :disabled="isLoading">
          {{ isLoading ? '正在请求...' : '开始分析' }}
        </button>
      </form>
    </div>

    <div class="card">
      <h3>2. 分析任务状态</h3>
      <button @click="fetchStatus" :disabled="isLoading">刷新状态</button>
      <p v-if="error" class="error">查询状态失败: {{ error }}</p>
      <ul v-if="analysisStatuses.length > 0" class="status-list">
        <li v-for="status in analysisStatuses" :key="status.data_source_id" :class="status.status">
          <div>
            <strong>数据源ID {{ status.data_source_id }}:</strong>
            <span class="status-badge">{{ status.status }}</span>
            <small v-if="status.error_message" class="error-detail">错误: {{ status.error_message }}</small>
          </div>
          <div v-if="status.status === 'completed'" class="workbench-link">
            <router-link :to="{ name: 'StandardizationWorkbench', params: { themeName: themeName } }">
              前往工作台 &rarr;
            </router-link>
          </div>
        </li>
      </ul>
      <p v-else>当前主题没有分析任务。</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useUIStore } from '../stores/ui';
import { triggerAnalysis, getAnalysisStatus } from '../api';
import { storeToRefs } from 'pinia';

const uiStore = useUIStore();
const { isLoading, error } = storeToRefs(uiStore);

const themeName = ref('公司财务报告');
const dataSourceId = ref(1);
const analysisStatuses = ref([]);
let pollingInterval = null;

const handleAnalysisRequest = async () => {
  if (!themeName.value || !dataSourceId.value) {
    alert('请输入完整的主题名称和数据源ID。');
    return;
  }
  try {
    await triggerAnalysis(dataSourceId.value, themeName.value);
    // 立即获取一次状态
    fetchStatus();
  } catch (e) {
    // 错误已由api.js中的拦截器处理
    console.error('Trigger analysis failed:', e);
  }
};

const fetchStatus = async () => {
  if (!themeName.value) return;
  try {
    const response = await getAnalysisStatus(themeName.value);
    analysisStatuses.value = response.data;
  } catch (e) {
    console.error('Fetch status failed:', e);
  }
};

onMounted(() => {
  // 组件加载时获取一次状态
  fetchStatus();
  // 每5秒轮询一次状态
  pollingInterval = setInterval(fetchStatus, 5000);
});

onUnmounted(() => {
  // 组件卸载时清除轮询
  if (pollingInterval) {
    clearInterval(pollingInterval);
  }
});
</script>

<style scoped>
.theme-management {
  max-width: 800px;
  margin: 0 auto;
  padding: 1rem;
}
.card {
  background: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}
.form-group {
  margin-bottom: 1rem;
  text-align: left;
}
.form-group label {
  display: block;
  margin-bottom: 0.5rem;
}
.form-group input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}
button {
  padding: 0.75rem 1.5rem;
  border: none;
  background-color: #007bff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}
button:disabled {
  background-color: #ccc;
}
.error {
  color: #d9534f;
}
.status-list {
  list-style-type: none;
  padding: 0;
  text-align: left;
}
.status-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-bottom: 1px solid #eee;
}
.workbench-link a {
  text-decoration: none;
  font-weight: bold;
  color: #007bff;
}
.status-list li:last-child {
  border-bottom: none;
}
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  margin-left: 1rem;
  color: white;
}
.status-list li.completed .status-badge {
  background-color: #5cb85c; /* green */
}
.status-list li.processing .status-badge {
  background-color: #f0ad4e; /* orange */
}
.status-list li.failed .status-badge {
  background-color: #d9534f; /* red */
}
.error-detail {
  display: block;
  margin-top: 0.5rem;
  color: #777;
  font-size: 0.9rem;
}
</style>
