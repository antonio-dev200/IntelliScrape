<template>
  <div class="task-management">
    <h2>抓取任务管理</h2>

    <!-- Create New Task Form -->
    <div class="card">
      <h3>创建新任务</h3>
      <form @submit.prevent="handleCreateTask">
        <div class="form-group">
          <label for="task-name">任务名称:</label>
          <input id="task-name" v-model="newTask.name" type="text" placeholder="例如：每日财报采集" required />
        </div>
        <div class="form-group">
          <label for="dataset-id">标准数据集ID:</label>
          <input id="dataset-id" v-model.number="newTask.standard_dataset_id" type="number" placeholder="例如：1" required />
        </div>
        <div class="form-group">
          <label for="source-ids">数据源ID (逗号分隔):</label>
          <input id="source-ids" v-model="dataSourceIdsInput" type="text" placeholder="例如：1,2,3" required />
        </div>
        <div class="form-group">
          <label for="cron-schedule">CRON表达式 (可选):</label>
          <input id="cron-schedule" v-model="newTask.schedule_cron" type="text" placeholder="例如：0 5 * * *" />
        </div>
        <button type="submit" :disabled="isLoading">
          {{ isLoading ? '正在创建...' : '创建任务' }}
        </button>
      </form>
    </div>

    <!-- Task List -->
    <div class="card">
      <h3>已创建的任务</h3>
      <button @click="fetchTasks" :disabled="isLoading">刷新列表</button>
      <p v-if="error" class="error">加载任务列表失败: {{ error }}</p>
      <table v-if="tasks.length > 0" class="task-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>数据集ID</th>
            <th>数据源ID</th>
            <th>CRON</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in tasks" :key="task.id">
            <td>{{ task.id }}</td>
            <td>{{ task.name }}</td>
            <td>{{ task.standard_dataset_id }}</td>
            <td>{{ task.data_source_ids.join(', ') }}</td>
            <td>{{ task.schedule_cron || 'N/A' }}</td>
            <td><span class="status-badge" :class="task.status">{{ task.status }}</span></td>
          </tr>
        </tbody>
      </table>
      <p v-else>还没有创建任何抓取任务。</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useUIStore } from '../stores/ui';
import { listCrawlTasks, createCrawlTask } from '../api';
import { storeToRefs } from 'pinia';

const uiStore = useUIStore();
const { isLoading, error } = storeToRefs(uiStore);

const tasks = ref([]);
const dataSourceIdsInput = ref('');
const newTask = reactive({
  name: '',
  standard_dataset_id: null,
  data_source_ids: [],
  schedule_cron: '',
});

const fetchTasks = async () => {
  try {
    const response = await listCrawlTasks();
    tasks.value = response.data;
  } catch (e) {
    console.error('Failed to fetch tasks:', e);
  }
};

const handleCreateTask = async () => {
  // Convert comma-separated string to array of numbers
  newTask.data_source_ids = dataSourceIdsInput.value.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));

  if (newTask.data_source_ids.length === 0) {
    alert('请输入有效的数据源ID。');
    return;
  }
  // Set schedule_cron to null if it's an empty string
  const payload = { ...newTask };
  if (!payload.schedule_cron) {
    payload.schedule_cron = null;
  }

  try {
    await createCrawlTask(payload);
    alert('任务创建成功！');
    // Reset form
    Object.assign(newTask, { name: '', standard_dataset_id: null, data_source_ids: [], schedule_cron: '' });
    dataSourceIdsInput.value = '';
    // Refresh list
    fetchTasks();
  } catch (e) {
    console.error('Failed to create task:', e);
  }
};

onMounted(() => {
  fetchTasks();
});
</script>

<style scoped>
.task-management {
  max-width: 900px;
  margin: auto;
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
}
button:disabled {
  background-color: #ccc;
}
.error {
  color: #d9534f;
}
.task-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}
.task-table th, .task-table td {
  border: 1px solid #ddd;
  padding: 0.75rem;
  text-align: left;
}
.task-table th {
  background-color: #f2f2f2;
}
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  color: white;
}
.status-badge.pending {
  background-color: #777;
}
.status-badge.in_progress {
  background-color: #f0ad4e;
}
</style>
