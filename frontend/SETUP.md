# Frontend Setup

## Tech Stack

- **React 19** - Latest React with React Compiler
- **Mantine v8.3.5** - Modern React component library
- **Jotai v2.15.0** - Primitive and flexible state management
- **React Query v5.90.5** - Powerful data synchronization for React
- **Axios v1.12.2** - Promise based HTTP client
- **Vite v7** - Next generation frontend tooling
- **TypeScript 5.9** - Typed JavaScript

## Project Structure

```
src/
├── api/              # API client functions
│   └── auth.ts       # Authentication API
├── hooks/            # Custom React hooks
│   └── useAuth.ts    # Authentication hook
├── lib/              # Library configurations
│   ├── axios.ts      # Axios instance with interceptors
│   └── queryClient.ts # React Query client config
├── providers/        # React context providers
│   └── AppProviders.tsx # Main app providers wrapper
├── store/            # Jotai atoms (state management)
│   └── auth.ts       # Authentication state atoms
├── App.tsx           # Main App component
└── main.tsx          # Application entry point
```

## Key Features

### 1. Axios Configuration (`src/lib/axios.ts`)
- Auto-attach JWT tokens to requests
- Automatic token refresh on 401 errors
- Request/Response interceptors

### 2. State Management with Jotai (`src/store/auth.ts`)
- `accessTokenAtom` - Access token (persisted to localStorage)
- `refreshTokenAtom` - Refresh token (persisted to localStorage)
- `userAtom` - Current user data
- `isAuthenticatedAtom` - Derived authentication status
- `logoutAtom` - Logout action

### 3. React Query Setup (`src/lib/queryClient.ts`)
- 5-minute stale time
- No auto-refetch on window focus
- Retry once on failure

### 4. Authentication Hook (`src/hooks/useAuth.ts`)
- `login(credentials)` - Login with email/password
- `register(data)` - Register new user
- `logout()` - Logout and clear tokens
- `user` - Current user object
- `isAuthenticated` - Auth status
- `isLoading` - Loading state

## Environment Variables

Create a `.env` file in the frontend directory:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Development

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Usage Examples

### Using Authentication

```tsx
import { useAuth } from '@/hooks/useAuth';

function LoginPage() {
  const { login, isLoginLoading, loginError } = useAuth();

  const handleLogin = async () => {
    try {
      await login({ email: 'user@example.com', password: 'password' });
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return <button onClick={handleLogin}>Login</button>;
}
```

### Using Mantine Components

```tsx
import { Button, Container, Title } from '@mantine/core';

function MyPage() {
  return (
    <Container>
      <Title order={1}>Hello Mantine</Title>
      <Button variant="filled">Click me</Button>
    </Container>
  );
}
```

### Creating API Endpoints

```tsx
// src/api/posts.ts
import { axiosInstance } from '@/lib/axios';

export const postsApi = {
  getAll: async () => {
    const response = await axiosInstance.get('/api/v1/posts');
    return response.data;
  },
  
  create: async (data: CreatePostData) => {
    const response = await axiosInstance.post('/api/v1/posts', data);
    return response.data;
  },
};
```

### Using React Query

```tsx
import { useQuery, useMutation } from '@tanstack/react-query';
import { postsApi } from '@/api/posts';

function Posts() {
  const { data: posts, isLoading } = useQuery({
    queryKey: ['posts'],
    queryFn: postsApi.getAll,
  });

  const createMutation = useMutation({
    mutationFn: postsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] });
    },
  });

  return <div>{/* Render posts */}</div>;
}
```

### Using Jotai for State

```tsx
import { atom, useAtom } from 'jotai';

const countAtom = atom(0);

function Counter() {
  const [count, setCount] = useAtom(countAtom);
  return (
    <button onClick={() => setCount(c => c + 1)}>
      Count: {count}
    </button>
  );
}
```

## Path Aliases

The project uses `@` as an alias for the `src` directory:

```tsx
// Instead of
import { useAuth } from '../../hooks/useAuth';

// Use
import { useAuth } from '@/hooks/useAuth';
```

## Notes

- All authentication tokens are automatically stored in localStorage
- The axios instance automatically refreshes expired tokens
- React Query DevTools are enabled in development mode
- Mantine components use CSS-in-JS with emotion

