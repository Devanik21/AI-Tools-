import streamlit as st
import google.generativeai as genai
import io
import base64
import json
import time
import os
from datetime import datetime
import re
from collections import Counter
import pandas as pd
import uuid

# Configure Streamlit page
st.set_page_config(page_title="Advanced AI Creator Hub", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

# Compressed CSS with advanced styling
st.markdown("""<style>
:root{--primary:#4f46e5;--secondary:#06b6d4;--dark:#1e293b;--light:#f8fafc;--success:#10b981;--warning:#f59e0b;--error:#ef4444}
.main{background:linear-gradient(135deg,var(--light),#eff6ff)}
.main.dark{background:linear-gradient(135deg,var(--dark),#0f172a)}
.stApp{max-width:1200px;margin:0 auto}
.tool-category{font-size:1.1rem;font-weight:600;color:var(--primary)}
div[data-testid="stVerticalBlock"]{gap:0.4rem}
.stButton>button{background:linear-gradient(90deg,var(--primary),var(--secondary));color:white;font-weight:500;border-radius:8px;padding:8px 16px;box-shadow:0 3px 12px rgba(0,0,0,0.12);transition:all 0.2s ease}
.stButton>button:hover{transform:translateY(-2px);box-shadow:0 6px 14px rgba(79,70,229,0.2)}
div.stTabs [data-baseweb="tab-list"]{gap:4px}
div.stTabs [data-baseweb="tab"]{background-color:#312e81;border-radius:6px 6px 0px 0px;padding:8px 16px;font-weight:500}
div.stTabs [aria-selected="true"]{background-color:#4f46e5}
.output-box{background-color:var(--light);border:1px solid #e2e8f0;border-radius:8px;padding:16px;margin-top:16px;box-shadow:0 2px 6px rgba(0,0,0,0.05)}
.output-box.dark{background-color:#1e293b;border:1px solid #334155}
.history-item{padding:12px;border:1px solid #e5e7eb;border-radius:6px;margin-bottom:6px;background-color:white;transition:all 0.2s ease}
.history-item:hover{box-shadow:0 4px 10px rgba(0,0,0,0.08);transform:translateY(-1px)}
.history-item.dark{background-color:#334155;border:1px solid #475569}
.theme-light{background-color:var(--light)}
.theme-dark{background-color:var(--dark);color:var(--light)}
.prompt-editor{border:1px solid #e2e8f0;border-radius:6px;padding:10px}
.tool-btn{transition:all 0.15s ease;border:1px solid #e5e7eb;border-radius:6px;text-align:center;padding:8px 12px;margin:4px 0}
.tool-btn:hover{background-color:#f1f5f9;transform:translateY(-1px);box-shadow:0 2px 5px rgba(0,0,0,0.05)}
.tool-btn.dark{border:1px solid #475569;background-color:#1e293b}
.tool-btn.dark:hover{background-color:#334155}
.banner{padding:12px;border-radius:8px;margin-bottom:12px;background:linear-gradient(90deg,#c7d2fe,#ddd6fe);font-weight:500}
.banner.dark{background:linear-gradient(90deg,#312e81,#4c1d95);color:white}
.status-badge{padding:3px 8px;border-radius:12px;font-size:0.75rem;font-weight:500}
.badge-success{background-color:#d1fae5;color:#047857}
.badge-warning{background-color:#fef3c7;color:#b45309}
.badge-error{background-color:#fee2e2;color:#b91c1c}
.sidebar-section{margin-bottom:20px;border-bottom:1px solid #e5e7eb;padding-bottom:15px}
</style>""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'api_key' not in st.session_state: st.session_state.api_key = ""
    if 'history' not in st.session_state: st.session_state.history = []
    if 'api_model' not in st.session_state: st.session_state.api_model = "gemini-2.0-flash"
    if 'prompt_templates' not in st.session_state: st.session_state.prompt_templates = {}
    if 'favorites' not in st.session_state: st.session_state.favorites = []
    if 'current_theme' not in st.session_state: st.session_state.current_theme = "light"
    if 'model_params' not in st.session_state: st.session_state.model_params = {
        "temperature": 0.7, "top_p": 0.95, "top_k": 40, "max_output_tokens": 2048
    }
    if 'user_history' not in st.session_state: st.session_state.user_history = []
    if 'workspace' not in st.session_state: st.session_state.workspace = {"templates": {}}
    
init_session_state()

# Helper functions
def analyze_content(text):
    """Analyze text content for metrics and insights"""
    if not text:
        return {}
    
    # Basic text analysis
    word_count = len(re.findall(r'\w+', text))
    sentence_count = len(re.findall(r'[.!?]+', text)) + 1
    paragraph_count = len(text.split('\n\n'))
    
    # Readability metrics
    words = re.findall(r'\w+', text.lower())
    word_lengths = [len(word) for word in words]
    avg_word_length = sum(word_lengths) / len(word_lengths) if word_lengths else 0
    
    # Sentiment analysis (simplified)
    positive_words = ['good', 'great', 'excellent', 'best', 'positive', 'happy', 'wonderful', 'amazing']
    negative_words = ['bad', 'worst', 'terrible', 'negative', 'poor', 'awful', 'horrible']
    
    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)
    
    sentiment = "Positive" if positive_count > negative_count else "Negative" if negative_count > positive_count else "Neutral"
    
    # Most common words (excluding common stopwords)
    stopwords = ['the', 'a', 'an', 'in', 'to', 'for', 'of', 'and', 'is', 'are', 'was', 'were']
    filtered_words = [word for word in words if word not in stopwords and len(word) > 2]
    common_words = Counter(filtered_words).most_common(7)
    
    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "paragraph_count": paragraph_count,
        "avg_word_length": round(avg_word_length, 2),
        "sentiment": sentiment,
        "common_words": common_words,
        "reading_time": round(word_count / 200, 1)  # Avg reading time in minutes
    }

def generate_ai_tools():
    """Generate AI tools based on categories and multipliers"""
    # Create base categories with tools
    base_categories = {
        "Writing": ["Blog Post", "Article", "Email", "Report", "Resume", "Cover Letter", "Social Media"],
        "Creative": ["Story", "Poem", "Script", "Dialogue", "Character", "Setting", "Plot"],
        "Business": ["Marketing Copy", "Pitch Deck", "Business Plan", "SWOT Analysis", "Strategy"],
        "Technical": ["Code", "Documentation", "Tutorial", "Technical Guide", "API Design"],
        "Education": ["Lesson Plan", "Course Outline", "Quiz", "Study Guide", "Research Paper"],
        "Personal": ["Journal", "Reflection", "Goal Setting", "Self-improvement", "Daily Planner"]
    }
    
    # Modifiers to expand variations
    modifiers = ["Advanced", "Custom", "Professional", "Smart", "Interactive", "Comprehensive"]
    formats = ["Generator", "Creator", "Assistant", "Helper", "Tool", "Builder"]
    
    # Generate expanded list of tools
    expanded_categories = {}
    for category, tools in base_categories.items():
        expanded_tools = []
        for tool in tools:
            expanded_tools.append(tool)
            # Add variations with modifiers
            for modifier in modifiers[:2]:
                expanded_tools.append(f"{modifier} {tool}")
            # Add variations with formats
            for format in formats[:2]:
                expanded_tools.append(f"{tool} {format}")
        
        expanded_categories[category] = expanded_tools
    
    # Create flat list for search
    all_tools = []
    for category, tools in expanded_categories.items():
        all_tools.extend(tools)
    
    return all_tools, expanded_categories

def load_prompt_templates():
    """Generate prompt templates for tools"""
    templates = {}
    all_tools, _ = generate_ai_tools()
    
    for tool in all_tools:
        templates[tool] = f"Generate content using the '{tool}' feature for: {{prompt}}. Ensure the output is high quality, relevant, and tailored to the user's needs."
    
    return templates

def generate_ai_content(prompt, api_key, model_name):
    """Generate content with AI using specified model and parameters"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        with st.spinner("🔮 AI is generating content..."):
            response = model.generate_content(prompt, generation_config=st.session_state.model_params)
            return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def save_to_history(tool_name, prompt, output):
    """Save generated content to history with unique ID"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry_id = str(uuid.uuid4())[:8]
    analysis = analyze_content(output)
    
    st.session_state.history.insert(0, {
        "id": entry_id,
        "timestamp": timestamp,
        "tool": tool_name,
        "prompt": prompt,
        "output": output,
        "analysis": analysis,
        "favorited": False
    })
    
    # Keep history at manageable size
    if len(st.session_state.history) > 30:
        st.session_state.history = st.session_state.history[:30]

def toggle_favorite(item_id):
    """Toggle favorite status for history item"""
    for item in st.session_state.history:
        if item.get("id") == item_id:
            item["favorited"] = not item.get("favorited", False)
            if item["favorited"] and item not in st.session_state.favorites:
                st.session_state.favorites.append(item)
            elif not item["favorited"] and item in st.session_state.favorites:
                st.session_state.favorites.remove(item)
            break

def get_color_theme():
    """Get current color theme class names"""
    is_dark = st.session_state.current_theme == "dark"
    return {
        "main": "dark" if is_dark else "",
        "box": "dark" if is_dark else "",
        "item": "dark" if is_dark else "",
        "banner": "dark" if is_dark else ""
    }

# Initialize tools and templates
all_tools, tool_categories = generate_ai_tools()
if not st.session_state.prompt_templates:
    st.session_state.prompt_templates = load_prompt_templates()

# Sidebar for configuration
with st.sidebar:
    st.image("https://via.placeholder.com/200x60?text=AI+HUB", width=200)
    
    # API Configuration
    with st.expander("🔑 API Configuration", expanded=False):
        api_key = st.text_input("Google Gemini API Key:", type="password", 
                               value=st.session_state.api_key,
                               help="Stored in session only")
        if api_key: st.session_state.api_key = api_key
        
        # Model selection with expanded options
        st.session_state.api_model = st.selectbox(
            "AI Model:",
            ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"],
            index=0
        )
        
        # Advanced model parameters
        with st.expander("Model Parameters"):
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.model_params["temperature"] = st.slider(
                    "Temperature:", min_value=0.0, max_value=1.0, 
                    value=st.session_state.model_params["temperature"], step=0.05)
                st.session_state.model_params["top_k"] = st.slider(
                    "Top K:", min_value=1, max_value=100, 
                    value=st.session_state.model_params["top_k"], step=1)
            with col2:
                st.session_state.model_params["top_p"] = st.slider(
                    "Top P:", min_value=0.0, max_value=1.0, 
                    value=st.session_state.model_params["top_p"], step=0.05)
                st.session_state.model_params["max_output_tokens"] = st.slider(
                    "Max Output:", min_value=100, max_value=8192, 
                    value=st.session_state.model_params["max_output_tokens"], step=100)
    
    # Tool search
    st.sidebar.markdown("### 🔍 Find Tools")
    search_term = st.text_input("Search tools:", key="sidebar_search")
    filtered_tools = [tool for tool in all_tools if search_term.lower() in tool.lower()] if search_term else []
    
    if filtered_tools:
        st.markdown(f"**{len(filtered_tools)} tools found**")
        for i, tool in enumerate(filtered_tools[:10]):
            if st.button(tool, key=f"sb_tool_{i}", use_container_width=True):
                st.session_state.selected_tool = tool
                st.rerun()
    
    # Favorites Section

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⭐ Favorites")
    
    if st.session_state.favorites:
        for i, item in enumerate(st.session_state.favorites[:5]):
            st.sidebar.markdown(f"**{item['tool']}** - {item['timestamp']}")
    else:
        st.sidebar.markdown("No favorites yet. Star your best creations!")
        
    # Theme Toggle
    st.sidebar.markdown("---")
    theme_col1, theme_col2 = st.sidebar.columns(2)
    with theme_col1:
        if st.button("🌞 Light", use_container_width=True):
            st.session_state.current_theme = "light"
            st.rerun()
    with theme_col2:
        if st.button("🌙 Dark", use_container_width=True):
            st.session_state.current_theme = "dark"
            st.rerun()

# Main content area
theme = get_color_theme()
st.markdown(f"<div class='banner {theme['banner']}'>🚀 Create content with AI - Choose a tool to get started</div>", unsafe_allow_html=True)

# Tabs for organization
tab1, tab2, tab3 = st.tabs(["🛠️ Tools", "📚 History", "⚙️ Workspace"])

# TOOLS TAB
with tab1:
    # Top level search and quick access
    st.markdown("### Quick Search")
    main_search = st.text_input("Search for AI tools:", key="main_search_box")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_tool = None
        if main_search:
            filtered_results = [tool for tool in all_tools if main_search.lower() in tool.lower()]
            if filtered_results:
                selected_tool = st.selectbox("Select tool:", filtered_results)
        
    # Categories display
    st.markdown("### Tool Categories")
    
    # Display categories in columns
    categories = list(tool_categories.keys())
    cols = st.columns(3)
    
    selected_category = None
    for i, category in enumerate(categories):
        with cols[i % 3]:
            if st.button(f"{category} ({len(tool_categories[category])})", key=f"cat_{i}", use_container_width=True):
                selected_category = category
    
    # Show tools from selected category
    if selected_category:
        st.markdown(f"#### {selected_category} Tools")
        tools_cols = st.columns(3)
        for i, tool in enumerate(tool_categories[selected_category]):
            with tools_cols[i % 3]:
                if st.button(tool, key=f"tool_{i}", use_container_width=True, 
                           help=f"Use {tool} to generate content"):
                    selected_tool = tool
    
    # Form for generating content
    if selected_tool:
        st.markdown(f"### Using: {selected_tool}")
        
        with st.form(key=f"gen_form_{selected_tool}"):
            # Get template
            template = st.session_state.prompt_templates.get(selected_tool, "Generate content for: {prompt}")
            
            # Prompt builder
            st.markdown("#### Enter your prompt")
            prompt_text = st.text_area("Content description:", height=100, 
                                     help="Describe what you want to generate")
            
            # Options
            col1, col2 = st.columns(2)
            with col1:
                tone = st.selectbox("Tone:", ["Professional", "Casual", "Enthusiastic", 
                                           "Formal", "Friendly", "Technical", "Creative"])
            with col2:
                length = st.selectbox("Length:", ["Short", "Medium", "Long", "Comprehensive"])
            
            # Final prompt construction
            final_prompt = template.format(prompt=prompt_text)
            final_prompt += f"\nTone: {tone}. Length: {length}."
            
            # Generate button
            submitted = st.form_submit_button("✨ Generate Content")
            
            if submitted:
                if not st.session_state.api_key:
                    st.error("Please enter your API key in the sidebar first.")
                elif not prompt_text:
                    st.warning("Please enter a prompt.")
                else:
                    # Call the AI service
                    output = generate_ai_content(final_prompt, st.session_state.api_key, st.session_state.api_model)
                    
                    # Display output
                    st.markdown(f"<div class='output-box {theme['box']}'>", unsafe_allow_html=True)
                    st.markdown("### Generated Content")
                    st.markdown(output)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Save to history
                    save_to_history(selected_tool, prompt_text, output)

# HISTORY TAB
with tab2:
    st.markdown("### Content History")
    
    if not st.session_state.history:
        st.info("No history yet. Generate some content to see it here.")
    else:
        for i, item in enumerate(st.session_state.history):
            with st.expander(f"{item['tool']} - {item['timestamp']}"):
                cols = st.columns([1, 6, 1])
                with cols[0]:
                    favorited = "⭐" if item.get("favorited", False) else "☆"
                    if st.button(favorited, key=f"fav_{item['id']}"):
                        toggle_favorite(item["id"])
                        st.rerun()
                
                with cols[1]:
                    st.markdown(f"**Prompt:** {item['prompt']}")
                    st.markdown("**Output:**")
                    st.markdown(item["output"])
                
                with cols[2]:
                    # Download button and analysis
                    if st.button("📊", key=f"stats_{item['id']}"):
                        # Show analysis
                        analysis = item.get("analysis", analyze_content(item["output"]))
                        st.markdown("#### Content Analysis")
                        st.markdown(f"""
                        - Words: {analysis.get('word_count', 0)}
                        - Sentences: {analysis.get('sentence_count', 0)}
                        - Paragraphs: {analysis.get('paragraph_count', 0)}
                        - Reading time: {analysis.get('reading_time', 0)} min
                        - Sentiment: {analysis.get('sentiment', 'Neutral')}
                        """)
                        
                        # Common words visualization
                        if "common_words" in analysis and analysis["common_words"]:
                            common_words = analysis["common_words"]
                            df = pd.DataFrame(common_words, columns=["Word", "Count"])
                            st.bar_chart(df.set_index("Word"))

# WORKSPACE TAB
with tab3:
    st.markdown("### Personal Workspace")
    
    # Template Management
    with st.expander("📝 Custom Templates", expanded=True):
        st.markdown("Create and save your own prompt templates")
        
        # Template creation form
        with st.form("template_form"):
            template_name = st.text_input("Template Name:")
            template_text = st.text_area("Template (use {prompt} as placeholder):", 
                                       value="Generate a {prompt} with the following characteristics:")
            submit_template = st.form_submit_button("Save Template")
            
            if submit_template and template_name and template_text:
                if "{prompt}" not in template_text:
                    st.error("Template must include {prompt} placeholder")
                else:
                    st.session_state.workspace["templates"][template_name] = template_text
                    st.success(f"Template '{template_name}' saved!")
        
        # Display saved templates
        if st.session_state.workspace["templates"]:
            st.markdown("#### Your Saved Templates")
            for name, template in st.session_state.workspace["templates"].items():
                with st.container():
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.markdown(f"**{name}**")
                        st.text(template)
                    with cols[1]:
                        if st.button("Use", key=f"use_{name}"):
                            # Set this template as active
                            st.session_state.active_template = template
                            st.success(f"Using template: {name}")
    
    # Export/Import
    with st.expander("💾 Export/Import", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Export Data")
            export_options = st.multiselect("Select data to export:", 
                                          ["History", "Templates", "Favorites"])
            
            if st.button("Export Selected Data") and export_options:
                export_data = {}
                if "History" in export_options:
                    export_data["history"] = st.session_state.history
                if "Templates" in export_options:
                    export_data["templates"] = st.session_state.workspace["templates"]
                if "Favorites" in export_options:
                    export_data["favorites"] = st.session_state.favorites
                
                # Convert to JSON
                json_data = json.dumps(export_data, indent=2)
                b64 = base64.b64encode(json_data.encode()).decode()
                
                # Create download link
                href = f'<a href="data:application/json;base64,{b64}" download="ai_hub_export.json">Download Export File</a>'
                st.markdown(href, unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### Import Data")
            uploaded_file = st.file_uploader("Upload exported data file:", type=["json"])
            
            if uploaded_file is not None:
                try:
                    import_data = json.load(uploaded_file)
                    
                    if "history" in import_data:
                        st.session_state.history.extend(import_data["history"])
                    if "templates" in import_data:
                        st.session_state.workspace["templates"].update(import_data["templates"])
                    if "favorites" in import_data:
                        st.session_state.favorites.extend(import_data["favorites"])
                    
                    st.success("Data imported successfully!")
                except Exception as e:
                    st.error(f"Error importing data: {str(e)}")
    
    # Settings
    with st.expander("⚙️ Settings", expanded=False):
        st.markdown("#### Application Settings")
        
        # Reset options
        reset_options = st.multiselect("Reset options:", 
                                    ["History", "Templates", "Favorites", "All Settings"])
        
        if st.button("Reset Selected") and reset_options:
            if "History" in reset_options or "All Settings" in reset_options:
                st.session_state.history = []
            if "Templates" in reset_options or "All Settings" in reset_options:
                st.session_state.workspace["templates"] = {}
            if "Favorites" in reset_options or "All Settings" in reset_options:
                st.session_state.favorites = []
            if "All Settings" in reset_options:
                st.session_state.api_key = ""
                st.session_state.model_params = {
                    "temperature": 0.7, "top_p": 0.95, "top_k": 40, "max_output_tokens": 2048
                }
            
            st.success("Selected items have been reset!")
            time.sleep(1)
            st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888;'>AI Creator Hub • Version 1.0 • Powered by Google Gemini</div>", 
    unsafe_allow_html=True
)
