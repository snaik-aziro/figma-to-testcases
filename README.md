# QA Test Generator

AI-powered QA Test Case Generator that creates comprehensive test cases from Figma designs and requirement documents.

## Features

- 🎨 **Figma Integration**: Extract UI components and screens from Figma files
- � **Smart Caching**: Prevent API rate limits with intelligent data caching
- 📄 **Document Parsing**: Parse requirements from PDF, DOCX, and text files
- 🤖 **AI Test Generation**: Generate test cases using Claude AI
- 📝 **Baseline Knowledge**: Leverage 250+ industry-standard test scenarios
- 🎯 **Noise Reduction**: Filter decorative elements with relevance scoring
- 🔗 **Traceability**: Link test cases to requirements
- 📊 **Coverage Reports**: Track requirement coverage

## Key Improvements (v1.1)

### 1. Figma Data Caching
- **Problem Solved**: Prevents API rate limit hits during testing
- **How It Works**: Automatically caches fetched data, allows loading from cache
- **Benefits**: 5-10x faster iterations, reduced API costs
- **Usage**: Select "Load from Cache" in Streamlit UI
- **Details**: See [CACHING_GUIDE.md](CACHING_GUIDE.md)

### 2. Baseline Test Knowledge
- **Problem Solved**: LLM-only generation misses standard test scenarios
- **How It Works**: 250+ predefined test scenarios for 20 UI components and 10 screen patterns
- **Benefits**: Consistent, comprehensive, industry-standard test cases

### 3. Noise Reduction with Heuristic Scoring
- **Problem Solved**: Figma JSON contains 80-90% noise (decorative elements)
- **How It Works**: Relevance scoring filters out low-value components
- **Benefits**: Cleaner context for LLM, better test case quality
- **Scoring**: Button=100, Input=62, Decorative Shape=0

## Quick Start

### Prerequisites

- Python 3.10+
- Figma Access Token
- Gemini API Key

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd qa-test-generator
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure environment:**

    Create a `.env` file from the example and add your API keys:
    ```bash
    cp .env.example .env
    ```
    Now, edit the `.env` file with your `FIGMA_ACCESS_TOKEN` and `GEMINI_API_KEY`.

### Running the Application

Start the Streamlit web server:
```bash
streamlit run demo_ui.py
```
The application will now be running at `http://localhost:8501`.

### Usage

1. **Run the Streamlit Web UI:**

   To start the web interface, run the following command from the root of the `qa-test-generator` directory:

   ```bash
   streamlit run demo_ui.py
   ```

2. **Open in Browser:**

   Streamlit will provide a local URL (usually `http://localhost:8501`). Open this in your web browser to access the application.

### How to Use the Tool

The Streamlit interface guides you through the process:

1.  **Configure Figma Access**:
    *   On the sidebar, enter your **Figma File URL** and **Figma Access Token**.
    *   Click **"Fetch & Cache from Figma"**. This will download and locally cache the design data, preventing future API calls for the same file.

2.  **Load Design and Requirements**:
    *   Once fetched, or if you have a local JSON file, select your cached file or upload it.
    *   Optionally, upload a **Product Requirements Document (PRD)** in PDF, DOCX, or text format.
    *   Click **"Analyze Design & PRD"**. This processes the design, filters out decorative elements, and extracts context from your PRD.

3.  **Generate Test Cases**:
    *   Select a specific screen from the dropdown menu to view its components.
    *   Click **"Generate Test Cases"**. The AI will generate functional, visual, and accessibility tests based on the screen's components and the PRD context.

4.  **Review and Export**:
    *   The generated test cases will appear on the right.
    *   Review the test cases, and once satisfied, click **"Export as JSON"** to download them.



## Project Structure

```
qa-test-generator/
├── app/
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── services/
│   │   ├── __init__.py
│   │   ├── figma_client.py  # Figma API client
│   │   ├── document_parser.py # Document parsing
│   │   └── test_generator.py # AI test generation
│   └── data/
│       └── test_baseline.json # Baseline test scenarios
├── demo_ui.py               # Streamlit UI application
├── requirements.txt
├── .env.example
└── README.md
```

## Configuration

The application is configured via a `.env` file. Copy the `.env.example` to `.env` and fill in the required API keys.

| Variable             | Description                                     | Default  |
| -------------------- | ----------------------------------------------- | -------- |
| `FIGMA_ACCESS_TOKEN` | Your personal Figma API access token.           | Required |
| `GEMINI_API_KEY`     | Your Google AI Studio API key for test generation. | Required |

## Test Case Types

- **Functional**: Verify user interactions and business logic
- **Visual**: UI/UX consistency and styling
- **Accessibility**: WCAG compliance and screen reader support
- **Edge Case**: Boundary testing and error scenarios

## Example Output

```json
{
  "test_id": "TC-0001",
  "title": "Verify login button functionality",
  "test_type": "functional",
  "priority": "high",
  "preconditions": ["User is on login page", "Valid credentials exist"],
  "test_steps": [
    {
      "step_number": 1,
      "action": "Enter valid username",
      "expected_result": "Username field accepts input"
    },
    {
      "step_number": 2,
      "action": "Enter valid password",
      "expected_result": "Password field shows masked input"
    },
    {
      "step_number": 3,
      "action": "Click Login button",
      "expected_result": "User is redirected to dashboard"
    }
  ],
  "expected_results": ["User successfully logged in", "Dashboard is displayed"],
  "tags": ["authentication", "login", "critical-path"]
}
```
