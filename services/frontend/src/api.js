import axios from 'axios';
import { useUIStore } from './stores/ui';

// Create an Axios instance
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Axios Interceptors for UI State Management
apiClient.interceptors.request.use(
  (config) => {
    const uiStore = useUIStore();
    uiStore.setLoading(true);
    uiStore.clearError();
    return config;
  },
  (error) => {
    const uiStore = useUIStore();
    uiStore.setError(error.message || 'A request error occurred.');
    uiStore.setLoading(false);
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => {
    const uiStore = useUIStore();
    uiStore.setLoading(false);
    return response;
  },
  (error) => {
    const uiStore = useUIStore();
    // Extract a more specific error message if available from the API response
    const errorMessage = error.response?.data?.detail || error.message || 'An unknown error occurred.';
    uiStore.setError(errorMessage);
    uiStore.setLoading(false);
    return Promise.reject(error);
  }
);


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
