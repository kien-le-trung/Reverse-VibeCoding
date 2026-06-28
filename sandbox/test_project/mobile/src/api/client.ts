const DEFAULT_API_URL = "http://localhost:8000";

export const API_URL = process.env.EXPO_PUBLIC_API_URL ?? DEFAULT_API_URL;

export async function getHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed with ${response.status}`);
  }
  return response.json();
}

