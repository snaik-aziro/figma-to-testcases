export interface ApiResponse<T = any> {
  data?: T;
  error?: { code: string; message: string } | null;
  meta?: Record<string, unknown>;
}
