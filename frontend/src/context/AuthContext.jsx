import React, { createContext, useContext, useState, useEffect } from 'react';
import api, { getStoredToken, setStoredToken } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(getStoredToken());
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Load user profile on startup if token is present
  useEffect(() => {
    async function loadUser() {
      const activeToken = getStoredToken();
      if (!activeToken) {
        setIsLoading(false);
        return;
      }
      try {
        const userData = await api.getCurrentUser();
        setUser(userData);
      } catch (err) {
        console.warn('Stored token is invalid or expired. Resetting session.', err);
        setStoredToken(null);
        setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }
    loadUser();
  }, []);

  const login = async (username, password) => {
    setAuthError(null);
    try {
      const data = await api.login(username, password);
      setStoredToken(data.access_token);
      setToken(data.access_token);
      setUser(data.user);
      return data.user;
    } catch (err) {
      setAuthError(err.message || 'Login failed.');
      throw err;
    }
  };

  const register = async (userData) => {
    setAuthError(null);
    try {
      const data = await api.register(userData);
      setStoredToken(data.access_token);
      setToken(data.access_token);
      setUser(data.user);
      return data.user;
    } catch (err) {
      setAuthError(err.message || 'Registration failed.');
      throw err;
    }
  };

  const logout = () => {
    setStoredToken(null);
    setToken(null);
    setUser(null);
    setAuthError(null);
  };

  const quickLogin = async (role = 'admin') => {
    if (role === 'admin') {
      return await login('sarang.lead', 'EcoPulse@2026');
    } else {
      return await login('telemetry.analyst', 'EcoPulse@2026');
    }
  };

  const updateProfile = async (profileData) => {
    const updated = await api.updateProfile(profileData);
    setUser(updated);
    return updated;
  };

  const value = {
    user,
    token,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
    isLoading,
    authError,
    setAuthError,
    login,
    register,
    logout,
    quickLogin,
    updateProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
