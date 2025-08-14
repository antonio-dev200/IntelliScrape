import axios from 'axios';

// Create an Axios instance
const apiClient = axios.create({
  // The BFF service will be running on port 8000.
  // In a real application, this would be configured via environment variables.
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- Theme Management API Calls ---

export const triggerAnalysis = (dataSourceId, themeName) => {
  return apiClient.post('/themes/analyze', {
    data_source_id: dataSourceId,
    theme_name: themeName,
  });
};

export const getWorkbenchData = (themeName) => {
  return apiClient.get(`/themes/${themeName}/workbench`);
};

export const standardizeTheme = (payload) => {
  return apiClient.post('/themes/standardize', payload);
};

export const getAnalysisStatus = (themeName) => {
  return apiClient.get('/themes/analysis_status', { params: { theme_name: themeName } });
};


// --- Crawl Task Management API Calls ---

export const createCrawlTask = (taskData) => {
  return apiClient.post('/crawl-tasks/', taskData);
};

export const listCrawlTasks = () => {
  return apiClient.get('/crawl-tasks/');
};
