import React, { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi } from '@/api/auth';
import type { User } from '@/store/auth';

interface AuthContextType {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  setAccessToken: (token: string | null) => void;
  setRefreshToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: { email: string; password: string }) => Promise<any>;
  register: (data: { email: string; password: string; name?: string }) => Promise<any>;
  logout: () => Promise<any>;
  loginError: any;
  registerError: any;
  isLoginLoading: boolean;
  isRegisterLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

// Helper functions to get initial state from localStorage
const getInitialAccessToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
};

const getInitialRefreshToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('refresh_token');
};

const getInitialUser = (): User | null => {
  if (typeof window === 'undefined') return null;
  const storedUser = localStorage.getItem('user');
  if (storedUser) {
    try {
      return JSON.parse(storedUser);
    } catch (e) {
      console.error('Failed to parse user from localStorage', e);
      return null;
    }
  }
  return null;
};

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const queryClient = useQueryClient();

  // Initialize state from localStorage immediately
  const [accessToken, setAccessToken] = useState<string | null>(getInitialAccessToken);
  const [refreshToken, setRefreshToken] = useState<string | null>(getInitialRefreshToken);
  const [user, setUser] = useState<User | null>(getInitialUser);
  const [isInitialized, setIsInitialized] = useState(false);

  // Mark as initialized after first render
  useEffect(() => {
    setIsInitialized(true);
  }, []);

  // Sync to localStorage when state changes
  useEffect(() => {
    if (accessToken !== null) {
      localStorage.setItem('access_token', accessToken);
    } else {
      localStorage.removeItem('access_token');
    }
  }, [accessToken]);

  useEffect(() => {
    if (refreshToken !== null) {
      localStorage.setItem('refresh_token', refreshToken);
    } else {
      localStorage.removeItem('refresh_token');
    }
  }, [refreshToken]);

  useEffect(() => {
    if (user !== null) {
      localStorage.setItem('user', JSON.stringify(user));
    } else {
      localStorage.removeItem('user');
    }
  }, [user]);

  const isAuthenticated = !!accessToken;

  // Get current user query
  const { data: currentUser, isLoading } = useQuery({
    queryKey: ['currentUser'],
    queryFn: authApi.getCurrentUser,
    enabled: !!accessToken && !user,
    retry: false,
  });

  // Update user when query succeeds
  useEffect(() => {
    if (currentUser && !user) {
      setUser(currentUser);
    }
  }, [currentUser, user]);

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      setAccessToken(data.access_token);
      setRefreshToken(data.refresh_token || null);
      setUser(data.user);
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      setAccessToken(data.access_token || null);
      setRefreshToken(data.refresh_token || null);
      setUser(data.user);
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
  });

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSettled: () => {
      setAccessToken(null);
      setRefreshToken(null);
      setUser(null);
      queryClient.clear();
    },
  });

  const value: AuthContextType = {
    accessToken,
    refreshToken,
    user,
    setAccessToken,
    setRefreshToken,
    setUser,
    isAuthenticated,
    isLoading: !isInitialized || isLoading, // Wait for initialization and user query
    login: loginMutation.mutateAsync,
    register: registerMutation.mutateAsync,
    logout: logoutMutation.mutateAsync,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
    isLoginLoading: loginMutation.isPending,
    isRegisterLoading: registerMutation.isPending,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
