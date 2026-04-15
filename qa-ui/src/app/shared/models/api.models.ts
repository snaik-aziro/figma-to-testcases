/* ============ Figma Fetch ============ */
export interface FigmaFetchPayload {
  fileUrlOrId: string;
  token: string;
  options?: {
    page?: string;
    cache?: boolean;
  };
}

export interface FigmaFetchResponse {
  cacheId: string;
  screens: any[];
  designUrl?: string;
  lastFetched?: string;
}

/* ============ Design Files ============ */
export interface DesignFilesResponse {
  cacheId: string;
  files: DesignFile[];
  totalCount: number;
}

export interface DesignFile {
  id: string;
  name: string;
  url?: string;
  lastModified?: string;
}

/* ============ Analyze Files ============ */
export interface AnalyzeFilesPayload {
  cacheId: string;
  prdText: string;
  options?: {
    applyFiltering?: boolean;
  };
}

export interface AnalyzeFilesResponse {
  screens: ScreenItem[];
  totalScreens: number;
  analysisMetadata?: {
    completedAt?: string;
    duration?: number;
  };
}

export interface ScreenItem {
  name: string;
  screen_type: string;
  description?: string;
  components?: any[];
}

/* ============ Generate Test Cases ============ */
export interface GenerateTestCasesPayload {
  cacheId: string;
  screenId: string;
  testType: string;
  testCount: number;
  prefer_premium?: boolean;
  prdText: string;
  options?: Record<string, any>;
  generateAll?: boolean;
}

export interface GenerateTestCasesPayloadResponse {
  runId: string;
  totalTestCount: number;
  screens: Screen[];
  errors: ErrorItem[];
}

export interface Screen {
  screen_id: string;
  screen_name: string;
  testCount: number;
  tests: TestCase[];
}

export interface TestCase {
  title: string;
  description: string;
  priority: string;
  preconditions: string[];
  test_steps: TestStep[];
  expected_results: string[];
  tags: string[];
  requirement_ids: string[];
  confidence_score: number;
  test_type: string;
}

export interface TestStep {
  step_number: number;
  action: string;
  expected_result: string;
  test_data: any;
}

export interface ErrorItem {
  code: string;
  message: string;
  details?: any;
}

/* ============ Common ============ */
export interface ApiError {
  statusCode: number;
  message: string;
  details?: any;
  timestamp?: string;
}
