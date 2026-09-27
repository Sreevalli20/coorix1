import { QueryRequest, QueryResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://coorix1.onrender.com';

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    console.log(`API Request: ${url}`, options);
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    console.log(`API Response status: ${response.status}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API Error: ${response.status} - ${errorText}`);
      throw new Error(`Unable to process your request (${response.status}). Please try again.`);
    }

    const data = await response.json();
    console.log('API Response data:', data);
    return data;
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
