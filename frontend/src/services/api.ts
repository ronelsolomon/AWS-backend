import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { getToken } from './auth';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:3000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );
  }

  // Generic request method
  async request<T>(config: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.client.request<T>(config);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.message || 'An error occurred');
      }
      throw error;
    }
  }

  // CRUD Operations for Items
  async getItems<T>(): Promise<T> {
    return this.request<T>({
      method: 'GET',
      url: '/items',
    });
  }

  async getItem<T>(id: string): Promise<T> {
    return this.request<T>({
      method: 'GET',
      url: `/items/${id}`,
    });
  }

  async createItem<T>(data: any): Promise<T> {
    return this.request<T>({
      method: 'POST',
      url: '/items',
      data,
    });
  }

  async updateItem<T>(id: string, data: any): Promise<T> {
    return this.request<T>({
      method: 'PUT',
      url: `/items/${id}`,
      data,
    });
  }

  async deleteItem<T>(id: string): Promise<T> {
    return this.request<T>({
      method: 'DELETE',
      url: `/items/${id}`,
    });
  }
}

export const apiClient = new ApiClient();
