import { defineStore } from 'pinia';

export const useUIStore = defineStore('ui', {
  state: () => ({
    isLoading: false,
    error: null, // Can be a string or an object
  }),
  actions: {
    setLoading(loading) {
      this.isLoading = loading;
    },
    setError(error) {
      this.error = error;
      // Optionally, clear the error after a few seconds
      if (error) {
        setTimeout(() => {
          this.error = null;
        }, 5000);
      }
    },
    clearError() {
      this.error = null;
    },
  },
});
