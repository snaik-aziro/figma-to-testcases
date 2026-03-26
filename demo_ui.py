"""
QA Test Generator - Demo UI
A Streamlit-based interface for showcasing the MVP
"""

import streamlit as st
import json
import os
import sys
import asyncio
import httpx
import time
from pathlib import Path
import base64

def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = get_base64_image("app/data/azirotech_logo.jpg")
cover_base64 = get_base64_image("app/data/azirotech_cover.jpg")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.figma_client import FigmaClient
from app.services.prd_analyzer import analyze_prd
from app.services.document_parser import DocumentParser
from app.services.test_generator import TestGenerator
from app.services.cache_manager import CacheManager
from app.config import get_settings
from app.models.database import TestCaseType

settings = get_settings()

cache_manager = CacheManager(cache_dir=".cache/figma_data")

st.set_page_config(
    page_title="QA Test Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.example.com/help',
        'Report a bug': "https://www.example.com/bug",
        'About': "# QA Test Generator. AI-Powered Test Case Generation."
    }
)

st.markdown("""
<style>

/* ==========================================
   AZIROTECH EXECUTIVE DESIGN SYSTEM
   ========================================== */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: "Inter", "Segoe UI", "Helvetica Neue", sans-serif;
}

.stApp {
    background-color: #F7F9FB;
    color: #1C1F26;
}

/* ==========================================
   TOP BRAND BAR
   ========================================== */

.top-bar {
    display: flex;
    align-items: center;
    height: 60px;
    padding: 0 2rem;
    background-color: #FFFFFF;
    border-bottom: 1px solid #EEF1F5;
}

.brand-logo {
    height: 34px;
}

.cover-strip {
    height: 80px;
    background-size: cover;
    background-position: center;
    opacity: 0.06;
    margin-bottom: 2rem;
}

/* ==========================================
   TYPOGRAPHY
   ========================================== */

.main-header {
    font-size: 2.2rem;
    font-weight: 700;
    color: #0B1F3A;
    letter-spacing: 0.4px;
    margin-bottom: 0.25rem;
    text-align: left;
}

.sub-header {
    font-size: 1rem;
    font-weight: 500;
    color: #5F6B7A;
    margin-bottom: 2.5rem;
    text-align: left;
}

h2, h3 {
    font-weight: 600;
    color: #0B1F3A;
    margin-top: 2rem;
    margin-bottom: 1rem;
}

/* ==========================================
   SIDEBAR
   ========================================== */

section[data-testid="stSidebar"] {
    background-color: #0B1F3A;
    padding: 2rem 1.5rem;
    border-right: 1px solid #1f365a;
}

section[data-testid="stSidebar"] * {
    color: #FFFFFF;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-weight: 600;
}

/* ==========================================
   INPUT VISIBILITY FIX
   ========================================== */

input, textarea {
    color: #1C1F26 !important;
    background-color: #FFFFFF !important;
}

div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #1C1F26 !important;
}

div[role="listbox"] {
    background-color: #FFFFFF !important;
    color: #1C1F26 !important;
}

/* ==========================================
   CARD SYSTEM
   ========================================== */

.stExpander {
    background: #FFFFFF;
    border: 1px solid #EEF1F5;
    border-radius: 6px;
}

.stExpander > div[role="button"] {
    font-weight: 600;
    padding: 1rem 1.5rem;
    background: #F9FAFB;
    border-radius: 6px;
}

/* Remove flashy effects */
.step-item {
    padding: 0.9rem 1rem;
    margin: 0.6rem 0;
    background-color: #F9FAFB;
    border: 1px solid #EEF1F5;
    border-radius: 6px;
    font-size: 0.95rem;
}

.step-item strong {
    color: #0B1F3A;
}

.step-item em {
    color: #5F6B7A;
}

/* ==========================================
   BUTTON SYSTEM
   ========================================== */

.stButton>button {
    border-radius: 4px;
    font-weight: 600;
    padding: 0.6rem 1.2rem;
    background-color: #0B1F3A;
    color: #FFFFFF;
    border: none;
    transition: background-color 0.15s ease-in-out;
}

.stButton>button:hover {
    background-color: #1f365a;
}

.stButton>button:focus {
    box-shadow: 0 0 0 2px #C6A7E;
    outline: none;
}

/* Success alert refinement */
.stAlert-success {
    background-color: #E8F1EC !important;
    color: #1C1F26 !important;
    border: 1px solid #D6E5DA !important;
    border-radius: 6px !important;
}

/* Divider rhythm */
hr {
    border: none;
    height: 1px;
    background-color: #EEF1F5;
    margin: 2.5rem 0;
}

</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="top-bar">
    <img src="data:image/jpeg;base64,{logo_base64}" class="brand-logo"/>
</div>

<div class="cover-strip" style="background-image: url('data:image/jpeg;base64,{cover_base64}')"></div>

<div class="main-header">QA Test Generator</div>
<div class="sub-header">
AI-Powered Test Case Generation from Figma Designs & PRD Documents
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'screens' not in st.session_state:
    st.session_state.screens = None
if 'prd_context' not in st.session_state:
    st.session_state.prd_context = None
if 'test_cases' not in st.session_state:
    st.session_state.test_cases = None
if 'figma_url' not in st.session_state:
    st.session_state.figma_url = ''
if 'figma_token' not in st.session_state:
    st.session_state.figma_token = ''
if 'figma_file_id' not in st.session_state:
    st.session_state.figma_file_id = None
if 'local_figma_data' not in st.session_state:
    st.session_state.local_figma_data = None


# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")

    # --- Step 1: Get Figma Data ---
    st.subheader("Step 1: Fetch or Upload Design")
    
    fetch_method = st.radio(
        "Choose design source:",
        ("Fetch from Figma API", "Use Local/Cached JSON")
    )

    if fetch_method == "Fetch from Figma API":
        figma_url = st.text_input(
            "Figma File URL or ID:", 
            st.session_state.figma_url,
            help="Provide the full URL of the Figma file."
        )
        figma_token = st.text_input(
            "Figma Access Token:", 
            st.session_state.figma_token, 
            type="password",
            help="Your personal access token for the Figma API."
        )
        st.session_state.figma_url = figma_url
        st.session_state.figma_token = figma_token
        
        if st.button("Fetch & Cache from Figma"):
            if not figma_url or not figma_token:
                st.error("Figma URL and Token are required.")
            else:
                with st.spinner("Fetching from Figma API..."):
                    try:
                        client = FigmaClient(access_token=figma_token)
                        file_id = client.extract_file_id(figma_url)
                        screens_data = asyncio.run(client.extract_screens(file_id))
                        
                        cache_data = {'screens': [s.model_dump() for s in screens_data]}
                        cache_manager.save(file_id, cache_data, file_name=file_id)
                        
                        st.session_state.figma_file_id = file_id
                        st.success(f"✅ Fetched and cached. File ID: {file_id}")
                    except Exception as e:
                        st.error(f"Failed to fetch from Figma: {e}")

    else: # Use Local/Cached JSON
        cached_files = cache_manager.list_cached_files()
        cached_options = {f"{meta['file_name']} ({meta['cached_at']})": meta['file_id'] for meta in cached_files}
        
        selected_cache = st.selectbox(
            "Select a cached file:", 
            options=[""] + list(cached_options.keys())
        )

        uploaded_file = st.file_uploader(
            "Or upload a new JSON file:", 
            type=['json']
        )

        if selected_cache:
            st.session_state.figma_file_id = cached_options[selected_cache]
            st.session_state.local_figma_data = None # Clear uploaded data
            st.info(f"Selected cached file: {st.session_state.figma_file_id}")
        
        if uploaded_file:
            st.session_state.local_figma_data = json.load(uploaded_file)
            st.session_state.figma_file_id = None # Clear cached selection
            st.info(f"Loaded uploaded file: {uploaded_file.name}")

    st.divider()

    # --- Step 2: Load and Analyze ---
    st.subheader("Step 2: Load & Analyze")
    
    prd_file = st.file_uploader(
        "Upload PRD (Optional):", 
        type=['pdf', 'docx', 'txt', 'json']
    )

    if st.button("Analyze Design & PRD", type="primary"):
        # Reset state
        st.session_state.screens = None
        st.session_state.prd_context = None
        
        # Load Figma data
        figma_data_loaded = False
        with st.spinner("Loading and processing Figma data..."):
            if st.session_state.local_figma_data:
                # Priority to uploaded file
                raw_screens = st.session_state.local_figma_data.get('screens', [])
                figma_data_loaded = True
            elif st.session_state.figma_file_id:
                # Fallback to cached file
                cached_data = cache_manager.load(st.session_state.figma_file_id)
                if cached_data:
                    raw_screens = cached_data.get('screens', [])
                    figma_data_loaded = True
            
            # If PRD was uploaded with the Analyze action, process it first so
            # PRD signals are available for scoring.
            if prd_file:
                try:
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(prd_file.name)[1]) as tmp_file:
                        tmp_file.write(prd_file.getvalue())
                        tmp_path = tmp_file.name
                    parser = DocumentParser()
                    file_extension = Path(tmp_path).suffix.lower()
                    if file_extension == '.pdf':
                        prd_result = parser.parse_pdf(tmp_path)
                    elif file_extension == '.docx':
                        prd_result = parser.parse_docx(tmp_path)
                    elif file_extension == '.json':
                        prd_result = parser.parse_json(tmp_path)
                    else:
                        with open(tmp_path, 'r', encoding='utf-8') as f:
                            prd_result = {'full_text': f.read()}
                    st.session_state.prd_context = prd_result.get('full_text', '')[:6000]
                    os.unlink(tmp_path)
                except Exception:
                    st.session_state.prd_context = st.session_state.get('prd_context', None)

            # Apply component filtering and noise reduction
            if figma_data_loaded:
                st.session_state.screens = raw_screens
                
                # Show filtering statistics
                total_components_before = sum(
                    len(s.get('components', []) or []) for s in raw_screens
                )
                
                # Apply filtering if enabled
                if settings.enable_component_filtering:
                    from app.services.figma_client import FigmaClient
                    
                    filtered_screens = []
                    total_components_after = 0
                    
                    # Precompute PRD signals for clients (if available)
                    prd_signals = None
                    if st.session_state.get('prd_context'):
                        prd_signals = analyze_prd(st.session_state.get('prd_context'))

                    for screen in raw_screens:
                        # Create a temporary client to use filtering logic
                        temp_client = FigmaClient(access_token="dummy", prd_signals=prd_signals)
                        
                        # Apply filtering to components
                        if isinstance(screen, dict):
                            filtered_components = temp_client._filter_components_by_relevance(
                                screen.get('components', []) or []
                            )
                            filtered_screen = screen.copy()
                            filtered_screen['components'] = filtered_components
                            filtered_screens.append(filtered_screen)
                            total_components_after += len(filtered_components)
                        else:
                            filtered_screens.append(screen)
                            total_components_after += len(screen.get('components', []) or [])
                    
                    st.session_state.screens = filtered_screens
                    
                    # Show filtering impact
                    filtered_count = total_components_before - total_components_after
                    filter_rate = (filtered_count / total_components_before * 100) if total_components_before > 0 else 0
                    
                    col_before, col_after, col_filtered = st.columns(3)
                    with col_before:
                        st.metric("Components (Before)", total_components_before)
                    with col_after:
                        st.metric("Components (After)", total_components_after)
                    with col_filtered:
                        st.metric("Filtered Out", f"{filtered_count} ({filter_rate:.1f}%)")
                    
                    if filter_rate > 0:
                        st.info(f"✅ Noise reduction applied: {filter_rate:.1f}% of decorative/low-priority components removed")
                    else:
                        st.warning(f"⚠️ No components filtered (all scored ≥ {settings.component_relevance_threshold}). Threshold may be too low.")
        
        if figma_data_loaded:
            st.success(f"✅ Loaded and processed {len(st.session_state.screens)} screens.")
        else:
            st.error("No Figma data selected. Please fetch, upload, or select a cached file in Step 1.")

        # Load PRD data (only if not already processed above)
        if prd_file and not st.session_state.get('prd_context'):
            with st.spinner("Processing PRD..."):
                try:
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(prd_file.name)[1]) as tmp_file:
                        tmp_file.write(prd_file.getvalue())
                        tmp_path = tmp_file.name
                    parser = DocumentParser()
                    file_extension = Path(tmp_path).suffix.lower()
                    if file_extension == '.pdf':
                        prd_result = parser.parse_pdf(tmp_path)
                    elif file_extension == '.docx':
                        prd_result = parser.parse_docx(tmp_path)
                    elif file_extension == '.json':
                        prd_result = parser.parse_json(tmp_path)
                    else:
                        with open(tmp_path, 'r', encoding='utf-8') as f:
                            prd_result = {'full_text': f.read()}
                    st.session_state.prd_context = prd_result.get('full_text', '')[:6000]
                    os.unlink(tmp_path)
                    st.success(" PRD loaded successfully.")
                except Exception as e:
                    st.error(f"Failed to process PRD: {e}")

    st.divider()
    st.subheader("API Keys")
    if not settings.gemini_api_key:
        st.warning("Google API Key (gemini_api_key) not found in .env file. Test generation will fail.")
        st.code("GEMINI_API_KEY='your-key-here'", language="shell")

# Main content
if os.path.exists("static/logo.png"):
    st.image("static/logo.png", width=150)
col1, col2 = st.columns([1, 2])

with col1:
    st.header(" Screens")
    
    if st.session_state.screens:
        screens = st.session_state.screens
        
        # Helper to get attribute from dict or object
        def get_attr(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        # Screen type filter
        screen_types = list(set(get_attr(s, 'screen_type', 'general') for s in screens))
        selected_type = st.selectbox("Filter by type:", ["All"] + sorted(screen_types))
        
        # Filter screens
        if selected_type != "All":
            filtered_screens = [s for s in screens if get_attr(s, 'screen_type') == selected_type]
        else:
            filtered_screens = screens
        
        # Display screens
        st.write(f"**{len(filtered_screens)} screens found**")
        
        screen_names = [get_attr(s, 'name', 'Unknown') for s in filtered_screens]
        selected_screen_name = st.selectbox("Select a screen:", screen_names)
        
        # Get selected screen
        selected_screen = next((s for s in filtered_screens if get_attr(s, 'name') == selected_screen_name), None)
        
        if selected_screen:
            st.markdown("---")
            st.subheader("Screen Details")
            st.write(f"**Name:** {get_attr(selected_screen, 'name')}")
            st.write(f"**Type:** {get_attr(selected_screen, 'screen_type')}")
            components = get_attr(selected_screen, 'components', []) or []
            st.write(f"**Components:** {len(components)}")
            
            # Show components
            with st.expander("View Components"):
                for comp in components[:15]:  # Show first 15
                    comp_name = get_attr(comp, 'name', 'Unknown')
                    comp_type = get_attr(comp, 'component_type', 'unknown')
                    relevance = get_attr(comp, 'relevance_score', None)
                    
                    if relevance is not None:
                        # Show relevance score with color coding
                        if relevance >= 70:
                            score_color = "🟢"  # Green - high priority
                        elif relevance >= 40:
                            score_color = "🟡"  # Yellow - medium priority
                        else:
                            score_color = "🔴"  # Red - low priority
                        st.write(f"{score_color} {comp_name} ({comp_type}) - Score: {relevance:.0f}")
                    else:
                        st.write(f"• {comp_name} ({comp_type})")
                if len(components) > 15:
                    st.write(f"... and {len(components) - 15} more components")
    else:
        st.info(" Click 'Load & Analyze' to load screens")

with col2:
    st.header("Generated Test Cases")
    
    if st.session_state.screens:
        # Option to generate for all screens
        generate_all = st.checkbox("Generate for ALL screens", value=False, help="When enabled, generate test cases for every filtered screen. This will consume more tokens and make multiple LLM calls.")

        # Percentile filter preview UI
        st.markdown("---")
        st.subheader("Preview component filtering")
        drop_percent = st.slider("Drop lowest percent of components", min_value=0, max_value=90, value=10, step=5)
        if st.button("Preview filtered components"):
            if not st.session_state.get('screens'):
                st.error("No screens loaded. Run Analyze Design & PRD first.")
            else:
                # Use the first screen as a preview
                preview_screen = st.session_state.screens[0]
                try:
                    from app.services.figma_client import FigmaClient
                    prd_signals = st.session_state.get('prd_signals', {})
                    client = FigmaClient(access_token="dummy", prd_signals=prd_signals)
                    comps = preview_screen.get('components', []) if isinstance(preview_screen, dict) else getattr(preview_screen, 'components', [])
                    result = client.filter_components_percentile(comps, drop_percent)
                    stats = result.get('stats', {})
                    st.write(stats)
                    kept = stats.get('total_components', 0) - stats.get('dropped_estimate', 0)
                    st.success(f"Preview complete — kept approx {kept} of {stats.get('total_components', 0)} components. Cutoff: {stats.get('cutoff_score', 0):.1f}")
                    # Show sample promoted/dropped items if available
                    # Note: result.components is the filtered component tree
                    dropped_sample = []
                    try:
                        # Collect some names from original vs filtered
                        orig_names = [c.get('name', '') for c in comps[:50]]
                        filtered_flat = []
                        def _flatten(cs):
                            for cc in cs:
                                filtered_flat.append(cc.get('name', '') if isinstance(cc, dict) else getattr(cc, 'name', ''))
                                children = cc.get('children', []) if isinstance(cc, dict) else getattr(cc, 'children', [])
                                if children:
                                    _flatten(children)
                        _flatten(result.get('components', []))
                        dropped_sample = [n for n in orig_names if n and n not in filtered_flat][:10]
                    except Exception:
                        dropped_sample = []
                    if dropped_sample:
                        st.write("Sample dropped components:")
                        for s in dropped_sample:
                            st.write(f"- {s}")
                except Exception as e:
                    st.error(f"Preview failed: {e}")

        if st.button(" Generate Test Cases", type="primary", use_container_width=True):
            if not settings.gemini_api_key:
                st.error("Cannot generate tests: Gemini API Key is missing.")
            else:
                # Decide which screens to process
                screens_to_process = []
                try:
                    screens_to_process = filtered_screens if 'filtered_screens' in globals() and filtered_screens else st.session_state.screens
                except Exception:
                    screens_to_process = st.session_state.screens

                if generate_all:
                    # Warn about token usage and rate limits
                    generator = TestGenerator()
                    estimated_tokens = len(screens_to_process) * getattr(generator, 'max_tokens', settings.llm_max_tokens)
                    st.warning(f"Generating for all screens ({len(screens_to_process)}). Estimated total tokens: {estimated_tokens}. Calls will be sequential with small delays to reduce rate-limit risk.")

                    all_test_cases = []
                    progress = st.progress(0)
                    status = st.empty()
                    errors = []

                    for idx, screen in enumerate(screens_to_process, start=1):
                        status.text(f"Processing screen {idx}/{len(screens_to_process)}: {screen.get('name', 'Unnamed')}")
                        try:
                            # Normalize screen to dict
                            if hasattr(screen, 'model_dump'):
                                screen_dict = screen.model_dump()
                            elif hasattr(screen, 'dict'):
                                screen_dict = screen.dict()
                            else:
                                screen_dict = screen

                            # Generate tests (sequential to limit concurrent LLM calls)
                            with st.spinner(f"Generating tests for {screen_dict.get('name', 'screen')}..."):
                                tests = generator.generate_test_cases(screen=screen_dict, requirements=[], prd_context=st.session_state.prd_context)
                                if tests:
                                    # Attach screen metadata to each test case
                                    for t in tests:
                                        t['_source_screen'] = screen_dict.get('name')
                                    all_test_cases.extend(tests)

                        except Exception as e:
                            errors.append({
                                'screen': screen.get('name', 'unknown') if isinstance(screen, dict) else str(screen),
                                'error': str(e)
                            })
                            # Continue processing remaining screens
                        finally:
                            # Small delay to reduce chance of rate-limiting/streaming issues
                            time.sleep(1)
                            progress.progress(int(idx / len(screens_to_process) * 100))
                            status.text("")

                    st.session_state.test_cases = all_test_cases
                    if all_test_cases:
                        st.success(f"Test cases generated for {len(all_test_cases)} total test cases across {len(screens_to_process)} screens.")
                    if errors:
                        st.warning(f"Some screens failed to generate: {len(errors)}. See details below.")
                        with st.expander("Generation Errors"):
                            st.write(errors)

                else:
                    # Single selected screen flow
                    if selected_screen:
                        with st.spinner("AI is generating test cases..."):
                            try:
                                generator = TestGenerator()
                                # Convert to dict if it's a Pydantic model
                                if hasattr(selected_screen, 'model_dump'):
                                    screen_dict = selected_screen.model_dump()
                                elif hasattr(selected_screen, 'dict'):
                                    screen_dict = selected_screen.dict()
                                else:
                                    screen_dict = selected_screen

                                test_cases = generator.generate_test_cases(
                                    screen=screen_dict,
                                    requirements=[],
                                    prd_context=st.session_state.prd_context
                                )
                                st.session_state.test_cases = test_cases
                                if test_cases:
                                    st.success(f" Test cases generated! ({len(test_cases)} test cases)")
                                else:
                                    st.warning(" No test cases were generated. Check the error details below.")
                            except Exception as e:
                                st.error(f"Error generating tests: {e}")
                                import traceback
                                with st.expander("Show Error Details"):
                                    st.code(traceback.format_exc())
                    else:
                        st.warning("Please select a screen first")
    
    # Display test cases
    if st.session_state.test_cases:
        test_cases = st.session_state.test_cases
        
        st.write(f"**{len(test_cases)} test cases generated**")
        
        for i, tc in enumerate(test_cases, 1):
            with st.expander(f" {tc.get('title', f'Test Case {i}')}", expanded=(i==1)):
                # Priority badge
                priority = tc.get('priority', 'medium')
                priority_color = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(priority, '⚪')
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**Priority:** {priority_color} {priority.upper()}")
                with col_b:
                    st.write(f"**Type:** {tc.get('test_type', 'functional')}")
                
                st.write(f"**Description:** {tc.get('description', 'N/A')}")
                
                # Preconditions
                if tc.get('preconditions'):
                    st.write("**Preconditions:**")
                    for pre in tc.get('preconditions', []):
                        st.write(f"  • {pre}")
                
                # Steps
                st.write("**Test Steps:**")
                steps = tc.get('test_steps', []) or tc.get('steps', [])
                if steps:
                    for j, step in enumerate(steps, 1):
                        step_action = step.get('action', 'N/A') if isinstance(step, dict) else str(step)
                        step_expected = step.get('expected_result', 'N/A') if isinstance(step, dict) else ''
                        st.markdown(f"""
                        <div class="step-item">
                            <strong>Step {j}:</strong> {step_action}<br>
                            <em>Expected:</em> {step_expected}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.write("No steps defined")
                
                # Linked requirements
                if tc.get('linked_requirements'):
                    st.write("**Linked Requirements:**")
                    for req in tc.get('linked_requirements', []):
                        st.write(f"   {req}")
        
        # Export button
        st.divider()
        if st.button(" Export as JSON"):
            screen_name = get_attr(selected_screen, 'name', 'export')
            screen_type = get_attr(selected_screen, 'screen_type', 'general')
            output = {
                "screen": screen_name,
                "screen_type": screen_type,
                "test_cases": test_cases
            }
            st.download_button(
                label="Download JSON",
                data=json.dumps(output, indent=2),
                file_name=f"test_cases_{screen_name}.json",
                mime="application/json"
            )
            
        # Evaluate button: call backend evaluate endpoint or fallback to local evaluator
        prefer_premium = st.checkbox("Prefer premium evaluator (may require API key)", value=False)
        if st.button(" Evaluate Testcases", use_container_width=True):
            if not st.session_state.get('test_cases'):
                st.error("No test cases available to evaluate. Generate tests first.")
            else:
                with st.spinner("Running evaluation..."):
                    prd_payload = {"full_text": st.session_state.get('prd_context') or ""}
                    tests_payload = {"test_cases": st.session_state.get('test_cases')}
                    eval_result = None
                    # Try backend HTTP endpoint first
                    try:
                        import httpx
                        payload = {"prd": prd_payload, "tests": tests_payload, "prefer_premium": prefer_premium}
                        # include selected screen JSON when evaluating a single selected screen
                        try:
                            if selected_screen:
                                if hasattr(selected_screen, 'model_dump'):
                                    payload['screen'] = selected_screen.model_dump()
                                elif hasattr(selected_screen, 'dict'):
                                    payload['screen'] = selected_screen.dict()
                                else:
                                    payload['screen'] = selected_screen
                        except Exception:
                            pass

                        resp = httpx.post(
                            "http://localhost:8000/api/tests/evaluate",
                            json=payload,
                            timeout=30.0
                        )
                        if resp.status_code == 200:
                            eval_result = resp.json()
                        else:
                            st.warning(f"Server evaluate returned {resp.status_code}: {resp.text}")
                    except Exception:
                        eval_result = None

                    # Fallback to local evaluator
                    if not eval_result:
                        try:
                            from app.services.evaluator import Evaluator
                            evaluator = Evaluator.with_fallback()
                            # pass selected screen when available so evaluator focuses on that screen
                            screen_for_eval = None
                            try:
                                if selected_screen:
                                    if hasattr(selected_screen, 'model_dump'):
                                        screen_for_eval = selected_screen.model_dump()
                                    elif hasattr(selected_screen, 'dict'):
                                        screen_for_eval = selected_screen.dict()
                                    else:
                                        screen_for_eval = selected_screen
                            except Exception:
                                screen_for_eval = None

                            eval_result = evaluator.evaluate(prd_payload, tests_payload, screen=screen_for_eval, prefer_premium=False)
                        except Exception as e:
                            st.error(f"Evaluation failed: {e}")
                            eval_result = None

                    if eval_result:
                        st.session_state.evaluation = eval_result
                        st.session_state.evaluation_metrics = eval_result.get('metrics', {})
                        st.success("Evaluation complete")

        # Show evaluation if present
        if st.session_state.get('evaluation_metrics'):
            with st.expander("Evaluation Metrics", expanded=True):
                st.json(st.session_state.get('evaluation_metrics'))

        # --- Manual Feedback & Re-evaluation ---
        st.divider()
        st.subheader("Manual Feedback & Re-evaluation")
        st.write("Provide human feedback describing how generated test cases should improve (focus areas, components, assessment criteria). Click 'Re-generate & Evaluate' to apply the feedback once.")

        fb_test_count = st.number_input("Tests to generate", min_value=1, max_value=20, value=5, step=1)
        fb_feedback = st.text_area("Feedback / Instructions for regeneration", height=160, placeholder="e.g. Focus on form validation, increase negative scenarios, prioritize the Submit button and error messages, ensure expected results are explicit.")
        fb_prefer_premium = st.checkbox("Prefer premium evaluator (may use API)", value=False)

        if st.button("Re-generate & Evaluate", use_container_width=True):
            if not selected_screen:
                st.error("Select a screen to re-generate tests for.")
            else:
                if hasattr(selected_screen, 'model_dump'):
                    screen_dict = selected_screen.model_dump()
                elif hasattr(selected_screen, 'dict'):
                    screen_dict = selected_screen.dict()
                else:
                    screen_dict = selected_screen

                generator = TestGenerator()
                with st.spinner("Regenerating tests with feedback and running evaluation..."):
                    try:
                        # Build augmented PRD context by combining original PRD plus feedback
                        base_prd = st.session_state.get('prd_context') or ""
                        augmented_prd = base_prd + "\n\nUSER_FEEDBACK:\n" + fb_feedback if fb_feedback else base_prd

                        new_tests = generator.generate_test_cases(
                            screen=screen_dict,
                            test_type=TestCaseType.FUNCTIONAL,
                            requirements=[],
                            test_count=int(fb_test_count),
                            prd_context=augmented_prd,
                        )

                        # Attach source screen
                        for t in new_tests:
                            t['_source_screen'] = screen_dict.get('name')

                        st.session_state.test_cases = new_tests

                        # Run evaluation (try server endpoint then local fallback)
                        prd_payload = {"full_text": augmented_prd}
                        tests_payload = {"test_cases": new_tests}
                        eval_result = None
                        try:
                            import httpx
                            resp = httpx.post(
                                "http://localhost:8000/api/tests/evaluate",
                                json={"prd": prd_payload, "tests": tests_payload, "prefer_premium": fb_prefer_premium},
                                timeout=30.0
                            )
                            if resp.status_code == 200:
                                eval_result = resp.json()
                        except Exception:
                            eval_result = None

                        if not eval_result:
                            try:
                                from app.services.evaluator import Evaluator
                                evaluator = Evaluator.with_fallback()
                                eval_result = evaluator.evaluate(prd_payload, tests_payload, screen=screen_dict, prefer_premium=fb_prefer_premium)
                            except Exception as e:
                                st.error(f"Evaluation failed: {e}")
                                eval_result = None

                        if eval_result:
                            st.session_state.evaluation = eval_result
                            st.session_state.evaluation_metrics = eval_result.get('metrics', {})
                            st.success("Re-generation and evaluation complete")
                    except Exception as e:
                        st.error(f"Re-generation failed: {e}")

        # Show last manual feedback evaluation
        if st.session_state.get('evaluation_metrics'):
            with st.expander("Latest Evaluation Metrics", expanded=True):
                st.json(st.session_state.get('evaluation_metrics'))
    else:
        if st.session_state.screens:
            st.info(" Click 'Generate Test Cases' to create tests for the selected screen")

# KPI Metrics Dashboard
colA, colB, colC = st.columns(3)
with colA:
    st.metric("Total Screens", len(st.session_state.screens or []))
with colB:
    st.metric("Generated Tests", len(st.session_state.test_cases or []))
with colC:
    st.metric("System Status", "Operational")

st.markdown("---")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.9rem;">
    Figma Test Generator v2.0
</div>
""", unsafe_allow_html=True)