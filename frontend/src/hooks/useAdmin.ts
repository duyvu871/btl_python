import { useAuth } from '@/providers/AuthProvider';

export const useAdmin = () => {
  const { user, isAuthenticated, isLoading } = useAuth();

  const isAdmin = user?.role === 'admin';

  return {
    isAdmin,
    isAuthenticated,
    isLoading,
    user,
  };
};
