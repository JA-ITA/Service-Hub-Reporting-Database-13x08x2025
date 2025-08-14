import axios from 'axios';

// API Configuration
export const API_BASE = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Helper function to get auth token
export const getAuthHeader = () => {
  const token = localStorage.getItem('auth_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// Axios instance with interceptors for better error handling
export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 10000, // 10 second timeout
});

// Request interceptor to add auth headers
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for consistent error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Auto logout on 401
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_info');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// API Methods
export const authAPI = {
  login: (credentials) => apiClient.post('/auth/login', credentials),
  register: (userData) => apiClient.post('/auth/register', userData),
  forgotPassword: (data) => apiClient.post('/auth/forgot-password', data),
  resetPassword: (data) => apiClient.post('/auth/reset-password', data),
  getCurrentUser: () => apiClient.get('/auth/me'),
};

export const usersAPI = {
  getUsers: () => apiClient.get('/users'),
  getUser: (id) => apiClient.get(`/users/${id}`),
  createUser: (userData) => apiClient.post('/users', userData),
  updateUser: (id, userData) => apiClient.put(`/users/${id}`, userData),
  deleteUser: (id) => apiClient.delete(`/users/${id}`),
  approveUser: (id) => apiClient.post(`/users/${id}/approve`),
  rejectUser: (id) => apiClient.post(`/users/${id}/reject`),
  getProfile: () => apiClient.get('/users/profile'),
  updateProfile: (data) => apiClient.put('/users/profile', data),
  changePassword: (data) => apiClient.post('/users/change-password', data),
};

export const locationsAPI = {
  getLocations: () => apiClient.get('/locations'),
  getLocation: (id) => apiClient.get(`/locations/${id}`),
  createLocation: (data) => apiClient.post('/locations', data),
  updateLocation: (id, data) => apiClient.put(`/locations/${id}`, data),
  deleteLocation: (id) => apiClient.delete(`/locations/${id}`),
  getDeletedLocations: () => apiClient.get('/locations/deleted'),
  restoreLocation: (id) => apiClient.post(`/locations/${id}/restore`),
};

export const templatesAPI = {
  getTemplates: () => apiClient.get('/templates'),
  getTemplate: (id) => apiClient.get(`/templates/${id}`),
  createTemplate: (data) => apiClient.post('/templates', data),
  updateTemplate: (id, data) => apiClient.put(`/templates/${id}`, data),
  deleteTemplate: (id) => apiClient.delete(`/templates/${id}`),
  getDeletedTemplates: () => apiClient.get('/templates/deleted'),
  restoreTemplate: (id) => apiClient.post(`/templates/${id}/restore`),
};

export const rolesAPI = {
  getRoles: () => apiClient.get('/roles'),
  createRole: (data) => apiClient.post('/roles', data),
  updateRole: (id, data) => apiClient.put(`/roles/${id}`, data),
  deleteRole: (id) => apiClient.delete(`/roles/${id}`),
};

export const submissionsAPI = {
  getSubmissions: () => apiClient.get('/submissions'),
  createSubmission: (data) => apiClient.post('/submissions', data),
  updateSubmission: (id, data) => apiClient.put(`/submissions/${id}`, data),
  deleteSubmission: (id) => apiClient.delete(`/submissions/${id}`),
};

export const reportsAPI = {
  generateCSV: (params) => apiClient.get('/reports/csv', { 
    params, 
    responseType: 'blob' 
  }),
  getStatistics: (params) => apiClient.get('/statistics', { params }),
  generateCustomFieldReport: (data) => apiClient.post('/statistics/generate-custom-field', data),
  getCustomFields: (templateId) => apiClient.get(`/statistics/custom-fields?template_id=${templateId}`),
  generatePDF: (params) => apiClient.get('/reports/pdf', { 
    params, 
    responseType: 'blob' 
  }),
};

export default apiClient;