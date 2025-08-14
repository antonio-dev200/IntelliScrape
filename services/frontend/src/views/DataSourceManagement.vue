<template>
  <div class="source-management">
    <h2>数据源管理</h2>

    <div class="card">
      <button @click="openModal()">添加新数据源</button>
    </div>

    <!-- Data Source Table -->
    <div class="card">
      <h3>已有数据源</h3>
      <table class="source-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>站点密钥 (Site Key)</th>
            <th>名称</th>
            <th>URL</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="source in dataSources" :key="source.id">
            <td>{{ source.id }}</td>
            <td>{{ source.site_key }}</td>
            <td>{{ source.name }}</td>
            <td><a :href="source.url" target="_blank">{{ source.url }}</a></td>
            <td>
              <button class="edit" @click="openModal(source)">编辑</button>
              <button class="delete" @click="handleDelete(source.id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal for Create/Edit -->
    <div v-if="isModalOpen" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <h3>{{ editingSource ? '编辑数据源' : '添加新数据源' }}</h3>
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="site-key">站点密钥:</label>
            <input id="site-key" v-model="form.site_key" required />
          </div>
          <div class="form-group">
            <label for="name">名称:</label>
            <input id="name" v-model="form.name" required />
          </div>
          <div class="form-group">
            <label for="url">URL:</label>
            <input id="url" v-model="form.url" type="url" required />
          </div>
          <div class="form-group">
            <label for="description">描述:</label>
            <textarea id="description" v-model="form.description"></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" @click="closeModal">取消</button>
            <button type="submit" :disabled="isLoading">{{ isLoading ? '正在保存...' : '保存' }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useUIStore } from '../stores/ui';
import { listDataSources, createDataSource, updateDataSource, deleteDataSource } from '../api';
import { storeToRefs } from 'pinia';

const uiStore = useUIStore();
const { isLoading } = storeToRefs(uiStore);

const dataSources = ref([]);
const isModalOpen = ref(false);
const editingSource = ref(null);
const form = reactive({
  id: null,
  site_key: '',
  name: '',
  url: '',
  description: '',
});

const fetchSources = async () => {
  try {
    const response = await listDataSources();
    dataSources.value = response.data;
  } catch (e) {
    console.error('Failed to fetch data sources:', e);
  }
};

const openModal = (source = null) => {
  if (source) {
    editingSource.value = source;
    Object.assign(form, source);
  } else {
    editingSource.value = null;
    Object.assign(form, { id: null, site_key: '', name: '', url: '', description: '' });
  }
  isModalOpen.value = true;
};

const closeModal = () => {
  isModalOpen.value = false;
};

const handleSubmit = async () => {
  try {
    if (editingSource.value) {
      await updateDataSource(editingSource.value.id, form);
    } else {
      await createDataSource(form);
    }
    closeModal();
    fetchSources();
  } catch (e) {
    console.error('Failed to save data source:', e);
    alert(`保存失败: ${e.response?.data?.detail || e.message}`);
  }
};

const handleDelete = async (id) => {
  if (confirm('你确定要删除这个数据源吗？')) {
    try {
      await deleteDataSource(id);
      fetchSources();
    } catch (e) {
      console.error('Failed to delete data source:', e);
    }
  }
};

onMounted(() => {
  fetchSources();
});
</script>

<style scoped>
/* General styles */
.source-management { max-width: 1000px; margin: auto; padding: 1rem; }
.card { background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
button { padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9rem; margin-right: 0.5rem; }
button:disabled { background-color: #ccc; }

/* Table styles */
.source-table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
.source-table th, .source-table td { border-bottom: 1px solid #ddd; padding: 0.75rem; text-align: left; }
.source-table th { background-color: #f7f7f7; }
.source-table td button.edit { background-color: #ffc107; }
.source-table td button.delete { background-color: #dc3545; color: white; }

/* Modal styles */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; }
.modal-content { background: white; padding: 2rem; border-radius: 8px; width: 90%; max-width: 500px; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; }
.form-group input, .form-group textarea { width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; }
.modal-actions { margin-top: 1.5rem; text-align: right; }
.modal-actions button[type="submit"] { background-color: #007bff; color: white; }
</style>
