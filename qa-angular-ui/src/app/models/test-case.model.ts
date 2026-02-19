export interface TestCase {
  testId: string;
  name?: string;
  createdAt?: string;
  status?: 'queued' | 'running' | 'passed' | 'failed';
  metadata?: Record<string, unknown>;
}
