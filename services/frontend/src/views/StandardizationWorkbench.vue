<template>
  <div class="workbench">
    <h2>标准化工作台: {{ themeName }}</h2>
    <p v-if="isLoading">正在加载工作台数据...</p>
    <p v-if="error" class="error">加载失败: {{ error }}</p>

    <div v-if="workbenchData" class="grid-container">
      <!-- Section 1: Existing Standard Fields -->
      <div class="card">
        <h3>已存在的标准字段</h3>
        <ul v-if="workbenchData.existing_standard_fields.length > 0">
          <li v-for="field in workbenchData.existing_standard_fields" :key="field">{{ field }}</li>
        </ul>
        <p v-else>该主题还没有标准字段。</p>
      </div>

      <!-- Section 2: Recommendations -->
      <div class="card recommendations">
        <h3>AI 推荐标准字段</h3>
        <p>基于在多个来源中出现的频率，我们推荐以下字段：</p>
        <ul v-if="workbenchData.recommendations.length > 0">
          <li v-for="rec in workbenchData.recommendations" :key="rec">
            <span class="rec-badge">{{ rec }}</span>
          </li>
        </ul>
        <p v-else>没有足够的数据以生成推荐。</p>
      </div>

      <!-- Section 3: Discovered Fields -->
      <div class="card discovered-fields">
        <h3>新发现的字段</h3>
        <p>请选择需要提升为标准字段的条目，并为其指定一个选择器:</p>
        <div v-for="field in workbenchData.discovered_fields" :key="field.name" class="field-item">
          <input type="checkbox" :id="field.name" :value="field.name" v-model="selectedFieldNames" @change="toggleFieldSelection(field.name, $event)">
          <label :for="field.name">
            <strong>{{ field.name }}</strong> (在 {{ field.count }}/{{ field.sources_count }} 个来源中发现)
          </label>
          <div class="selectors" :class="{ 'disabled': !selectedFieldNames.includes(field.name) }">
            <div v-for="(count, selector) in field.selectors" :key="selector" class="selector-choice">
              <input
                type="radio"
                :id="`${field.name}-${selector}`"
                :name="field.name"
                :value="selector"
                v-model="fieldSelectorMap[field.name]"
                :disabled="!selectedFieldNames.includes(field.name)">
              <label :for="`${field.name}-${selector}`" class="selector-badge">
                {{ selector }} ({{ count }})
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="actions">
      <button @click="handleStandardize" :disabled="isLoading || selectedFieldNames.length === 0">
        {{ isLoading ? '正在保存...' : '保存标准化配置' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useUIStore } from '../stores/ui';
import { getWorkbenchData, standardizeTheme } from '../api';
import { storeToRefs } from 'pinia';

// For now, themeName is hardcoded. In a real app, this would come from the route.
const themeName = ref('公司财务报告');

const uiStore = useUIStore();
const { isLoading, error } = storeToRefs(uiStore);

const workbenchData = ref(null);
const selectedFieldNames = ref([]); // Tracks which fields are checked
const fieldSelectorMap = reactive({}); // Tracks the chosen selector for each field

const toggleFieldSelection = (fieldName, event) => {
  if (event.target.checked) {
    // When checked, auto-select the most common selector
    const fieldData = workbenchData.value.discovered_fields.find(f => f.name === fieldName);
    if (fieldData && fieldData.selectors) {
      const mostCommonSelector = Object.keys(fieldData.selectors).sort((a, b) => fieldData.selectors[b] - fieldData.selectors[a])[0];
      fieldSelectorMap[fieldName] = mostCommonSelector;
    }
  } else {
    // When unchecked, clear the selector choice
    delete fieldSelectorMap[fieldName];
  }
};

const fetchWorkbenchData = async () => {
  try {
    const response = await getWorkbenchData(themeName.value);
    workbenchData.value = response.data;
    // Pre-select recommended fields and their selectors for user convenience
    response.data.recommendations.forEach(recName => {
      if (!selectedFieldNames.value.includes(recName)) {
        selectedFieldNames.value.push(recName);
        toggleFieldSelection(recName, { target: { checked: true } });
      }
    });
  } catch (e) {
    console.error('Failed to fetch workbench data:', e);
  }
};

const handleStandardize = async () => {
  if (Object.keys(fieldSelectorMap).length === 0) {
    alert('请至少为一个标准字段选择一个选择器。');
    return;
  }

  const payload = {
    theme_name: themeName.value,
    description: `Standardized dataset for ${themeName.value}.`,
    fields_to_standardize: Object.keys(fieldSelectorMap).map(fieldName => ({
      field_name: fieldName,
      description: `Standardized field for ${fieldName}.`,
      data_type: 'Text', // Defaulting to Text for simplicity
    })),
    // This part is still simplified, but now it correctly builds the mappings
    // based on user selection for a single data source.
    source_configs: [
      {
        data_source_id: 1, // Assuming we are configuring for data source 1
        mappings: Object.entries(fieldSelectorMap).map(([fieldName, selector]) => ({
          field_name: fieldName,
          selector: selector,
        })),
        extra_fields: [], // Extra fields logic can be added later
      },
    ],
  };

  try {
    await standardizeTheme(payload);
    alert('标准化配置已成功保存！');
    // Refetch data to show the new state
    fetchWorkbenchData();
  } catch (e) {
    console.error('Failed to standardize theme:', e);
  }
};

onMounted(() => {
  fetchWorkbenchData();
});
</script>

<style scoped>
.workbench { max-width: 1200px; margin: auto; padding: 1rem; }
.grid-container { display: grid; grid-template-columns: 1fr 2fr; gap: 1.5rem; }
.card { background: #f9f9f9; border: 1px solid #ddd; border-radius: 8px; padding: 1.5rem; }
.recommendations { grid-column: 1 / 2; background-color: #e6f7ff; border-color: #91d5ff; }
.discovered-fields { grid-column: 2 / 3; grid-row: 1 / 3; }
.rec-badge { background-color: #1890ff; color: white; padding: 0.3rem 0.6rem; border-radius: 12px; font-size: 0.9rem; display: inline-block; margin: 0.2rem; }
.field-item { border-bottom: 1px solid #eee; padding: 1rem 0; }
.field-item:last-child { border-bottom: none; }
.field-item > label { font-size: 1.1rem; margin-left: 0.5rem; }
.selectors { margin-top: 0.75rem; margin-left: 1.7rem; padding-left: 1rem; border-left: 2px solid #f0f0f0; }
.selectors.disabled { opacity: 0.5; pointer-events: none; }
.selector-choice { display: flex; align-items: center; margin-bottom: 0.5rem; }
.selector-choice input[type="radio"] { margin-right: 0.5rem; }
.selector-badge { background-color: #f0f0f0; border: 1px solid #d9d9d9; padding: 0.2rem 0.5rem; border-radius: 4px; font-family: monospace; font-size: 0.85rem; cursor: pointer; }
.selector-choice input[type="radio"]:checked + .selector-badge { border-color: #007bff; background-color: #e6f7ff; }
.actions { margin-top: 2rem; text-align: right; }
button { padding: 0.75rem 1.5rem; border: none; background-color: #28a745; color: white; border-radius: 4px; cursor: pointer; font-size: 1.1rem; }
button:disabled { background-color: #ccc; }
.error { color: #d9534f; }
</style>
