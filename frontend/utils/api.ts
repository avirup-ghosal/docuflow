import axios from 'axios';
import Cookies from 'js-cookie';

// 1. Create centralized Axios instance
const api = axios.create({
  baseURL: '/api', // Triggers the rewrite rule in next.config.mjs
  headers: {
    'Content-Type': 'application/json',
  },
});

// 2. Request Interceptor (Middleware)
// Before sending any request, check if we have a token.
api.interceptors.request.use((config) => {
  const token = Cookies.get('token');
  
  if (token && config.headers) {
    //"Authorization: Bearer <token>"
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  return config;
}, (error) => {
  return Promise.reject(error);
});


api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove('token');
    }
    return Promise.reject(error);
  }
);

export default api;