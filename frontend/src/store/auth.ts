// User interface
export interface User {
  id: string;
  user_name: string;
  email: string;
  verified: boolean;
  role: string;
  preferences: string[];
  created_at: string;
}
