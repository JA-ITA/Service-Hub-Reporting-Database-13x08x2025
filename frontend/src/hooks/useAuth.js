import { useState, useEffect } from 'react';
import { authAPI } from '../utils/api';

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('auth_token');
      const userInfo = localStorage.getItem('user_info');
      
      if (token && userInfo) {
        try {
          const parsedUser = JSON.parse(userInfo);
          setUser(parsedUser);
        } catch (error) {
          console.error('Error parsing user info:', error);
          logout();
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = (userData) => {
    setUser(userData);
    localStorage.setItem('user_info', JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
  };

  const hasPermission = (permission) => {
    if (!user || !user.permissions) return false;
    return user.permissions.includes(permission);
  };

  const hasRole = (role) => {
    if (!user) return false;
    return user.role === role;
  };

  return {
    user,
    loading,
    login,
    logout,
    hasPermission,
    hasRole,
    isAuthenticated: !!user,
  };
};

export default useAuth;