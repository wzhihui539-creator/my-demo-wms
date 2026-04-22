import { useState, useEffect, createContext, useContext } from 'react';
import * as React from 'react';

interface User {
  id: string;
  username: string;
  real_name?: string;
  role?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  login: async () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
      setUser({ id: '1', username: 'admin' });
    }
  }, []);

  const login = async (username: string, password: string) => {
    const response = await fetch(window.location.origin + '/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    
    if (!response.ok) {
      throw new Error('登录失败');
    }
    
    const data = await response.json();
    localStorage.setItem('token', data.access_token);
    setUser(data.user);
    setIsAuthenticated(true);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setIsAuthenticated(false);
    window.location.href = '/login';
  };

  const value = { user, isAuthenticated, login, logout };

  return React.createElement(
    AuthContext.Provider,
    { value },
    children
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
