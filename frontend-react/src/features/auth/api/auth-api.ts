import { api } from "@/lib/api-client"

export interface RegisterRequest {
  email: string
  password: string
  full_name?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

export interface User {
  user_id: string
  email: string
  full_name: string | null
  is_active: boolean
  created_at: string
}

export const authApi = {
  /**
   * Register a new user
   */
  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>("/register", data)
    return response.data
  },

  /**
   * Login with email and password
   */
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>("/login", data)
    return response.data
  },

  /**
   * Get current user profile
   */
  async getMe(): Promise<User> {
    const response = await api.get<User>("/me")
    return response.data
  },

  /**
   * Logout (client-side token removal, no server endpoint)
   */
  logout(): void {
    // Token removal handled by auth store
  },
}
