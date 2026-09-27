import { QueryRequest, QueryResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error('Unable to process your request. Please try again.');
    }

    return response.json();
  }

  async processQuery(query: string, userRole: string = 'user'): Promise<QueryResponse> {
    const request: QueryRequest = {
      query,
      user_role: userRole,
    };

    return this.request<QueryResponse>('/api/query', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async trialIntelligence(query: string): Promise<QueryResponse> {
    return this.request<QueryResponse>('/api/trials/intelligence', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }

  async compoundIntelligence(query: string): Promise<QueryResponse> {
    return this.request<QueryResponse>('/api/compounds/intelligence', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }

  async safetyAnalysis(query: string): Promise<QueryResponse> {
    return this.request<QueryResponse>('/api/safety/analyze', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }

  async researchRetrieve(query: string): Promise<QueryResponse> {
    return this.request<QueryResponse>('/api/research/retrieve', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }

  async synthesize(query: string): Promise<QueryResponse> {
    return this.request<QueryResponse>('/api/synthesis/synthesize', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }
}

export const apiService = new ApiService();
