<template>
  <div class="workbench">
    <h2>标准化工作台: {{ themeName }}</h2>
    <p v-if="isLoading">正在加载工作台数据...</p>
    <p v-if="error" class="error">加载失败: {{ error }}</p>

    <div v-if="workbenchData" class="grid-container">
      <div class="card">
        <h3>已存在的标准字段</h3>
        <ul v-if="workbenchData.existing_standard_fields.length > 0">
          <li v-for="field in workbenchData.existing_standard_fields" :key="field">{{ field }}</li>
        </ul>
        <p v-else>该主题还没有标准字段。</p>
      </div>

      <div class="card discovered-fields">
        <h3>新发现的字段</h3>
        <p>为每个字段选择一个选择器，并决定如何将其标准化。</p>
        <div v-for="field in workbenchData.discovered_fields" :key="field.name" class="field-item">
          <h4>{{ field.name }}</h4>
          <p class="field-meta">在 {{ field.count }}/{{ field.sources_count }} 个来源中发现</p>

          <div class="selectors">
            <strong>选择器:</strong>
            <div v-for="(count, selector) in field.selectors" :key="selector" class="selector-choice">
              <input type="radio" :id="`${field.name}-${selector}`" :name="field.name" :value="selector" v-model="fieldSelectorMap[field.name]">
              <label :for="`${field.name}-${selector}`" class="selector-badge">{{ selector }} ({{ count }})</label>
            </div>
          </div>

          <div class="mapping">
            <strong>标准化操作:</strong>
            <select v-model="fieldMapping[field.name]">
              <option value="__IGNORE__">忽略此字段</option>
              <option value="__NEW__">创建为新的标准字段</option>
              <optgroup label="映射到已有标准字段">
                <option v-for="stdField in workbenchData.existing_standard_fields" :key="stdField" :value="stdField">
                  {{ stdField }}
                </option>
              </optgroup>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div class="actions">
      <button @click="handleStandardize" :disabled="isLoading">保存标准化配置</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useUIStore } from '../stores/ui';
import { getWorkbenchData, standardizeTheme } from '../api';
import { storeToRefs } from 'pinia';

const themeName = ref('公司财务报告');
const uiStore = useUIStore();
const { isLoading, error } = storeToRefs(uiStore);

const workbenchData = ref(null);
const fieldSelectorMap = reactive({});
const fieldMapping = reactive({});

const fetchWorkbenchData = async () => {
  try {
    const response = await getWorkbenchData(themeName.value);
    workbenchData.value = response.data;

    // Initialize component state based on fetched data
    workbenchData.value.discovered_fields.forEach(field => {
      // Auto-select the most common selector
      const mostCommonSelector = Object.keys(field.selectors).sort((a, b) => field.selectors[b] - field.selectors[a])[0];
      fieldSelectorMap[field.name] = mostCommonSelector;

      // Auto-map recommended fields to __NEW__, others to __IGNORE__
      if (workbenchData.value.recommendations.includes(field.name)) {
        fieldMapping[field.name] = '__NEW__';
      } else {
        fieldMapping[field.name] = '__IGNORE__';
      }
    });
  } catch (e) {
    console.error('Failed to fetch workbench data:', e);
  }
};

const handleStandardize = async () => {
  const fieldsToStandardize = [];
  const finalMappings = [];

  for (const discoveredField in fieldMapping) {
    const mappingAction = fieldMapping[discoveredField];
    const selectedSelector = fieldSelectorMap[discoveredField];

    if (mappingAction === '__IGNORE__' || !selectedSelector) {
      continue; // Skip ignored fields or fields without a selected selector
    }

    if (mappingAction === '__NEW__') {
      fieldsToStandardize.push({
        field_name: discoveredField,
        description: `Standardized field for ${discoveredField}.`,
        data_type: 'Text',
      });
      finalMappings.push({
        field_name: discoveredField, // The new standard field has the same name
        selector: selectedSelector,
      });
    } else {
      // Mapping to an existing standard field
      finalMappings.push({
        field_name: mappingAction, // The name of the existing standard field
        selector: selectedSelector,
      });
    }
  }

  if (fieldsToStandardize.length === 0 && finalMappings.length === 0) {
    alert('没有可保存的标准化配置。');
    return;
  }

  const payload = {
    theme_name: themeName.value,
    description: `Standardized dataset for ${themeName.value}.`,
    fields_to_standardize: fieldsToStandardize,
    source_configs: [
      {
        data_source_id: 1, // Simplified for one data source
        mappings: finalMappings,
        extra_fields: [],
      },
    ],
  };

  try {
    await standardizeTheme(payload);
    alert('标准化配置已成功保存！');
    fetchWorkbenchData(); // Refresh data
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
.grid-container { display: grid; grid-template-columns: 1fr 2fr; gap: 1.5rem; align-items: start; }
.card { background: #f9f9f9; border: 1px solid #ddd; border-radius: 8px; padding: 1.5rem; }
.discovered-fields { grid-column: 2 / 3; grid-row: 1 / 3; }
.field-item { border-bottom: 1px solid #eee; padding: 1.5rem 0; }
.field-item:last-child { border-bottom: none; }
.field-item h4 { margin-top: 0; margin-bottom: 0.25rem; }
.field-meta { font-size: 0.9rem; color: #666; margin-top: 0; }
.selectors, .mapping { margin-top: 1rem; }
.selectors strong, .mapping strong { display: block; margin-bottom: 0.5rem; font-size: 0.9rem; }
.selector-choice { display: inline-flex; align-items: center; margin-right: 1rem; }
.selector-badge { background-color: #f0f0f0; border: 1px solid #d9d9d9; padding: 0.2rem 0.5rem; border-radius: 4px; font-family: monospace; }
.selector-choice input[type="radio"]:checked + .selector-badge { border-color: #007bff; background-color: #e6f7ff; }
.mapping select { width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; }
.actions { margin-top: 2rem; text-align: right; }
button { padding: 0.75rem 1.5rem; border: none; background-color: #28a745; color: white; border-radius: 4px; cursor: pointer; font-size: 1.1rem; }
.error { color: #d9534f; }
</style>
