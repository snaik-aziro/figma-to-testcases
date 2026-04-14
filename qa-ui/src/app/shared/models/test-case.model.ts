export interface TestStep {
  step_number: number;
  action: string;
  expected_result: string;
  test_data: any;
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

export interface Screen {
  screen_id: string;
  screen_name: string;
  testCount: number;
  tests: TestCase[];
}

export interface GeneratedTestCasesResponse {
  runId: string;
  totalTestCount: number;
  screens: Screen[];
  errors: any[];
}
