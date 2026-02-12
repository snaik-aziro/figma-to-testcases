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
from pathlib import Path

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.figma_client import FigmaClient
from app.services.document_parser import DocumentParser
from app.services.test_generator import TestGenerator
from app.services.cache_manager import CacheManager
from app.config import get_settings

# Load settings
settings = get_settings()

# Initialize cache manager
cache_manager = CacheManager(cache_dir=".cache/figma_data")

# Page config
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

# Custom CSS
st.markdown("""
<style>
    /* General App Styling */
    .stApp {
        background-color: #F0F2F6;
    }

    /* Main Headers */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #1A237E; /* Dark Blue */
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px #ccc;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #546E7A; /* Blue Grey */
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Sidebar Styling */
    .css-1d391kg {
        background-color: #FFFFFF;
        border-right: 1px solid #E0E0E0;
    }
    .st-emotion-cache-16txtl3 {
        padding: 2rem 1rem;
    }

    /* Card-like containers */
    .test-case-card, .success-box, .info-box {
        padding: 1.5rem;
        background-color: #FFFFFF;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 5px solid;
    }

    .test-case-card { border-color: #1E88E5; } /* Blue */
    .success-box { border-color: #4CAF50; } /* Green */
    .info-box { border-color: #FFC107; } /* Amber */

    /* Test Step Styling */
    .step-item {
        padding: 0.75rem;
        margin: 0.5rem 0;
        background-color: #F8F9FA;
        border: 1px solid #E0E0E0;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: all 0.2s ease-in-out;
    }
    .step-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.06);
    }
    .step-item strong {
        color: #0D47A1; /* Darker Blue */
    }

    /* Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }

    /* Expander styling */
    .stExpander {
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        background-color: #FFFFFF;
    }
    .stExpander>div[role="button"] {
        font-weight: 600;
        color: #37474F; /* Blue Grey Dark */
        padding: 1rem;
    }

</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header"> QA Test Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Test Case Generation from Figma Designs & PRD Documents</div>', unsafe_allow_html=True)

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
                    
                    for screen in raw_screens:
                        # Create a temporary client to use filtering logic
                        temp_client = FigmaClient(access_token="dummy")
                        
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

        # Load PRD data
        if prd_file:
            with st.spinner("Processing PRD..."):
                try:
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(prd_file.name)[1]) as tmp_file:
                        tmp_file.write(prd_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    parser = DocumentParser()
                    
                    # Determine file type and call the correct parser
                    file_extension = Path(tmp_path).suffix.lower()
                    if file_extension == '.pdf':
                        prd_result = parser.parse_pdf(tmp_path)
                    elif file_extension == '.docx':
                        prd_result = parser.parse_docx(tmp_path)
                    elif file_extension == '.json':
                        prd_result = parser.parse_json(tmp_path)
                    else: # Assuming .txt or other plain text
                        with open(tmp_path, "r", encoding="utf-8") as f:
                            prd_result = {"full_text": f.read()}

                    st.session_state.prd_context = prd_result.get('full_text', '')[:3000]
                    os.unlink(tmp_path)
                    st.success("✅ PRD loaded successfully.")
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
        if st.button(" Generate Test Cases", type="primary", use_container_width=True):
            if not settings.gemini_api_key:
                st.error("Cannot generate tests: Gemini API Key is missing.")
            elif selected_screen:
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
    else:
        if st.session_state.screens:
            st.info(" Click 'Generate Test Cases' to create tests for the selected screen")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.9rem;">
    Figma Test Generator v1.0
</div>
""", unsafe_allow_html=True)