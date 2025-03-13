import streamlit as st
import google.generativeai as genai
import io
import base64
import json
import time
import os
from datetime import datetime

# Configure Streamlit page
st.set_page_config(page_title="Ultimate AI Creator Hub", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

# Custom CSS (highly condensed)
st.markdown("""<style>.main{background-color:#f8f9fa}.stApp{max-width:1200px;margin:0 auto}.tool-category{font-size:1.2rem;font-weight:bold;margin-top:1rem;color:#1e3a8a}div[data-testid="stVerticalBlock"]{gap:0.5rem}.stButton>button{background:linear-gradient(90deg,#3b82f6,#8b5cf6);color:white;font-weight:600;border-radius:10px;padding:10px 20px;box-shadow:0 4px 14px rgba(0,0,0,0.1);transition:all 0.3s ease}.stButton>button:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,0.15)}div.stTabs [data-baseweb="tab-list"]{gap:8px}div.stTabs [data-baseweb="tab"]{background-color:#300661;border-radius:8px 8px 0px 0px;padding:10px 16px;font-weight:600}div.stTabs [aria-selected="true"]{background-color:#bfdbfe}.output-box{background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:20px;margin-top:20px}.history-item{padding:10px;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:8px;background-color:white}.category-selector{margin:10px 0}.search-box{margin:15px 0}</style>""", unsafe_allow_html=True)

# Initialize session state
if 'api_key' not in st.session_state: st.session_state.api_key = ""
if 'history' not in st.session_state: st.session_state.history = []
if 'api_model' not in st.session_state: st.session_state.api_model = "gemini-2.0-flash"
if 'prompt_templates' not in st.session_state: st.session_state.prompt_templates = {}

# Function to generate expanded AI tools list
@st.cache_data
def generate_ai_tools():
    # Base categories dictionary - we'll expand with multipliers later
    base_categories = {
        "Writing": [
            "Resume", "Cover Letter", "Email", "Blog Post", "Content Rewrite", "Grammar Check", 
            "Summary", "Academic Essay", "Letter", "Script", "Technical Writing", "Research Paper",
            "Whitepaper", "Thesis Statement", "Literature Review", "Citation", "Lab Report",
            "Case Study", "Editorial Guidelines", "Style Guide", "Professional Bio", "Executive Summary",
            "Project Proposal", "Meeting Minutes", "Documentation", "SOP", "Policy Draft",
            "Legal Document", "Contract Clause", "Terms & Conditions", "Privacy Policy"
        ],
        
        "Creative": [
            "Poem", "Story", "Dialogue", "Character", "Book Title", "Horror Story", "Sci-Fi Story",
            "Song Lyrics", "Children's Story", "Novel Outline", "Metaphor", "Joke", "Fantasy World",
            "Sci-Fi Technology", "Historical Fiction", "Memoir", "Poetry Prompt", "Creative Prompt",
            "Short Story Starter", "Screenplay Format", "Plot Twist", "Character Backstory",
            "Setting Description", "Alternate History", "Mythical Creature", "Magic System",
            "Fictional Language", "Story Conflict"
        ],
        
        "Business": [
            "Business Idea", "Startup Pitch", "SEO Keywords", "Business Consultation", "Marketing Strategy",
            "Grant Proposal", "Freelance Proposal", "LinkedIn Bio", "Branding Guide", "Business Email",
            "SWOT Analysis", "Business Case", "Market Research", "Competitor Analysis", "Pricing Strategy",
            "Product Launch", "Go-to-Market", "Customer Persona", "Mission Statement", "Company Values",
            "Business Plan", "Investor Pitch", "Funding Request", "Project Timeline", "Risk Assessment",
            "ROI Calculator", "KPI Framework"
        ]
    }
    
    # Additional categories to reach 2000+ tools
    extended_categories = {
        "Social Media": ["Post", "Caption", "Viral Tweet", "YouTube Idea", "Tagline", "Pinterest Description",
                        "Cold Email", "Podcast Episode", "Content Calendar", "Viral Formula", "Influencer Pitch",
                        "Brand Partnership", "YouTube Script", "Dating Profile", "Networking Opener",
                        "TikTok Trend", "Instagram Story", "LinkedIn Article", "Twitter Thread", "Facebook Ad",
                        "Hashtag Strategy", "Reel Script", "Community Post", "Review Response", "Crisis Response"],
        
        "Productivity": ["Productivity Plan", "Daily Plan", "Travel Itinerary", "Note-Taking", "Brainstorming",
                         "Grocery List", "Interview Prep", "Learning Path", "Time Management", "Prioritization",
                         "Decision Matrix", "Problem-Solving", "Critical Thinking", "Goal Setting", "Habit Tracker",
                         "Professional Development", "Weekly Schedule", "Project Management", "Task Breakdown"],
        
        "Education": ["Lesson Plan", "Course Outline", "Curriculum", "Educational Quiz", "Study Guide",
                     "Teaching Material", "Assignment", "Workshop", "Test Questions", "Learning Objectives",
                     "Educational Game", "Academic Resource", "Subject Summary", "Syllabus", "Tutorial"],
        
        "Design": ["Design Brief", "Color Palette", "Typography Guide", "Design System", "Logo Concept",
                  "UI Element", "UX Flow", "Website Layout", "Print Material", "Product Packaging",
                  "Illustration Concept", "Icon Set", "Brand Identity", "Style Tile", "Mood Board"],
        
        "Development": ["Code Review", "Technical Spec", "API Documentation", "Development Plan", "Code Architecture",
                       "Database Schema", "Software Requirements", "Testing Strategy", "Bug Report", "Feature Spec",
                       "Code Refactoring", "Algorithm", "Tech Stack", "System Architecture", "Code Snippet"],
        
        "Marketing": ["Marketing Plan", "Campaign Brief", "Ad Copy", "Landing Page", "Email Campaign",
                     "Conversion Strategy", "Growth Hack", "Product Description", "Promotion", "Sales Script",
                     "Value Proposition", "USP", "Elevator Pitch", "Customer Journey", "Messaging Framework"],
        
        "Finance": ["Budget Plan", "Financial Analysis", "Investment Strategy", "Expense Report", "Revenue Forecast",
                   "Cash Flow", "Financial Model", "Cost Reduction", "Profit Optimization", "Tax Strategy",
                   "Retirement Plan", "Debt Management", "Financial Education", "Savings Plan", "Equity Distribution"],
        
        "Health": ["Wellness Plan", "Diet Plan", "Fitness Routine", "Mental Health", "Sleep Improvement",
                  "Meditation Script", "Nutrition Guide", "Health Goal", "Self-Care Routine", "Stress Management",
                  "Recovery Plan", "Symptom Analysis", "Mindfulness Exercise", "Health Tracker", "Medical Information"],
        
        "Legal": ["Legal Analysis", "Contract Template", "Legal Response", "Compliance Check", "Privacy Statement",
                 "Disclaimer", "Terms of Service", "Copyright Notice", "IP Strategy", "Legal Research",
                 "Legal Letter", "Dispute Resolution", "Regulatory Filing", "Legal Defense", "Intellectual Property"],
        
        "Event": ["Event Plan", "Invitation", "Wedding Speech", "Toast", "Anniversary Message", "Party Theme",
                 "Conference Agenda", "Event Marketing", "Catering Menu", "Venue Description", "Entertainment Plan",
                 "Guest List", "Event Schedule", "Thank You Note", "Event Budget", "Virtual Event"],
        
        "Relationships": ["Relationship Advice", "Conflict Resolution", "Apology Letter", "Friendship Message",
                         "Love Letter", "Dating Profile", "Breakup Letter", "Family Communication", "Networking Message",
                         "Condolence Note", "Birthday Message", "Anniversary Note", "Congratulations Note", "Reconnection"],
        
        "Industry": ["Industry Analysis", "Sector Trend", "Market Forecast", "Industry Report", "Competitive Landscape",
                    "Regulatory Impact", "Technology Adoption", "Industry Disruption", "Vertical Strategy", "Supply Chain",
                    "Distribution Channel", "Industry Standards", "Industry Partnership", "Trade Association", "Industry Event"]
    }
    
    # Combine base and extended categories
    all_categories = {**base_categories, **extended_categories}
    
    # Multipliers to expand each tool category (adjectival prefixes)
    tool_multipliers = [
        "Advanced", "Custom", "Premium", "Enhanced", "Professional", "Intelligent", "Smart", "Dynamic",
        "Interactive", "Personalized", "Strategic", "Comprehensive", "Automated", "High-Performance", "Next-Gen",
        "Streamlined", "Optimized", "Scalable", "Innovative", "Creative", "Essential", "Ultimate", "Practical",
        "Specialized", "Expert", "Efficient", "Versatile", "Powerful", "Flexible", "Multi-purpose"
    ]
    
    # Format multipliers (output format variations)
    format_multipliers = [
        "Generator", "Builder", "Creator", "Designer", "Maker", "Assistant", "Helper", "Tool", "Solution",
        "Expert", "Consultant", "Advisor", "Planner", "Architect", "Analyst", "Strategist", "Developer",
        "Manager", "Optimizer", "Writer", "Guide", "Template", "Framework", "System", "Toolkit"
    ]
    
    # Generate expanded tools by combining base tools with multipliers
    expanded_categories = {}
    for category, base_tools in all_categories.items():
        expanded_tools = []
        for base_tool in base_tools:
            # Add the original tool with common suffixes
            for format_mult in format_multipliers[:3]:  # Limit to top 3 formats
                expanded_tools.append(f"{base_tool} {format_mult}")
            
            # Add tools with multipliers (limit to reduce overwhelming options)
            for mult in tool_multipliers[:5]:  # Limit to top 5 multipliers
                expanded_tools.append(f"{mult} {base_tool}")
        
        expanded_categories[category] = expanded_tools
    
    # Create specialized industry categories (new areas)
    specialized_industries = {
        "Healthcare": ["Patient Care", "Medical Record", "Clinical Trial", "Health Assessment", "Treatment Plan",
                      "Healthcare Policy", "Medical Research", "Patient Education", "Telehealth", "Health Insurance",
                      "Medical Device", "Healthcare Compliance", "Medical Diagnosis", "Patient Experience", "Wellness Program"],
        
        "E-commerce": ["Product Listing", "Customer Review", "E-commerce Copy", "Shipping Policy", "Return Policy",
                       "Product Bundle", "Flash Sale", "Customer Engagement", "Shopping Experience", "Loyalty Program",
                       "Product Recommendation", "Checkout Process", "Customer Retention", "Marketplace Strategy", "Pricing Model"],
        
        "Real Estate": ["Property Description", "Market Analysis", "Investment Property", "Rental Analysis", "Home Staging",
                       "Property Marketing", "Neighborhood Guide", "Real Estate Listing", "Agent Bio", "Mortgage Information",
                       "Home Inspection", "Lease Agreement", "Property Management", "HOA Communication", "Commercial Lease"],
        
        "Sustainability": ["Environmental Impact", "Sustainability Report", "Green Initiative", "Carbon Footprint", "ESG Strategy",
                          "Circular Economy", "Sustainable Design", "Climate Action", "Conservation Plan", "Energy Efficiency",
                          "Waste Reduction", "Water Conservation", "Sustainable Supply Chain", "Social Impact", "Eco Certification"],
        
        "Technology": ["Tech Specification", "Product Roadmap", "User Guide", "Tech Support", "Software Release",
                      "Hardware Design", "Tech Solution", "IT Strategy", "Digital Transformation", "Tech Integration",
                      "Tech Troubleshooting", "Cloud Migration", "Data Strategy", "Network Design", "Tech Evaluation"]
    }
    
    # Add specialized industries to the expanded categories
    for industry, tools in specialized_industries.items():
        industry_tools = []
        for tool in tools:
            # Add the original tool with common suffixes
            for format_mult in format_multipliers[:3]:  # Limit to top 3 formats
                industry_tools.append(f"{tool} {format_mult}")
            
            # Add tools with multipliers (limit to reduce overwhelming options)
            for mult in tool_multipliers[:3]:  # Limit to top 3 multipliers
                industry_tools.append(f"{mult} {tool}")
        
        expanded_categories[industry] = industry_tools
    
    # Create flat list of all tools
    all_tools = []
    for category, tools in expanded_categories.items():
        all_tools.extend(tools)
    
    return all_tools, expanded_categories

# Get all tools and categories
ai_tools, tool_categories = generate_ai_tools()

# Function to load prompt templates (dynamic generation)
@st.cache_data
def load_prompt_templates():
    templates = {}
    for tool in ai_tools:
        templates[tool] = f"Generate content using the '{tool}' feature for: {{prompt}}. Ensure the output is high quality, relevant, and tailored to the user's needs."
    return templates

# Function to generate content with AI
def generate_ai_content(prompt, api_key, model_name):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        with st.spinner("🔮 AI is working its magic..."):
            generation_config = {"temperature": 0.7, "top_p": 0.95, "top_k": 40, "max_output_tokens": 2048}
            response = model.generate_content(prompt, generation_config=generation_config)
            return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# Function to save content to history
def save_to_history(tool_name, prompt, output):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.history.insert(0, {"timestamp": timestamp, "tool": tool_name, "prompt": prompt, "output": output})
    if len(st.session_state.history) > 20:
        st.session_state.history = st.session_state.history[:20]

# Sidebar for API configuration
with st.sidebar:
    st.image("https://via.placeholder.com/150x60?text=AI+Hub", width=150)
    st.markdown("### 🔑 API Configuration")
    api_key = st.text_input("Enter Google Gemini API Key:", type="password", value=st.session_state.api_key, help="Your API key is stored in the session and not saved.")
    if api_key: st.session_state.api_key = api_key
    
    # Model selection with Gemini models
    st.session_state.api_model = st.selectbox(
        "Select AI Model:",
        ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
        index=0
    )
    
    st.markdown("---")
    search_term = st.text_input("🔍 Search for tools:")
    filtered_tools = [tool for tool in ai_tools if search_term.lower() in tool.lower()] if search_term else ai_tools
    
    # Statistics
    # Statistics
    st.sidebar.markdown("### 📊 Stats")
    st.sidebar.markdown(f"**Total Tools:** {len(ai_tools)}")
    st.sidebar.markdown(f"**Categories:** {len(tool_categories)}")
    
    # History button in sidebar
    st.sidebar.markdown("---")
    show_history = st.sidebar.button("📜 View History")
    clear_history = st.sidebar.button("🗑️ Clear History")
    if clear_history:
        st.session_state.history = []
        st.sidebar.success("History cleared!")

# Main content area
st.title("🧠 Ultimate AI Creator Hub")
st.markdown("Create amazing content with AI-powered tools - all in one place!")

# Welcome message
if not st.session_state.api_key:
    st.info("👋 Welcome! Please enter your API key in the sidebar to get started.")

# Display history if requested
if show_history and 'history' in st.session_state and len(st.session_state.history) > 0:
    st.header("📜 Content History")
    for i, item in enumerate(st.session_state.history):
        with st.expander(f"{item['timestamp']} - {item['tool']}"):
            st.markdown("**Prompt:**")
            st.markdown(f"```\n{item['prompt']}\n```")
            st.markdown("**Output:**")
            st.markdown(item['output'])
    st.markdown("---")

# Load prompt templates if needed
if not st.session_state.prompt_templates or len(st.session_state.prompt_templates) == 0:
    st.session_state.prompt_templates = load_prompt_templates()

# Tool Selection Section
st.header("🛠️ Select Your Creation Tool")

# Tool selection 
tab1, tab2 = st.tabs(["📋 Categories", "🔍 Search Results"])

with tab1:
    selected_category = st.selectbox("Choose a category:", list(tool_categories.keys()))
    
    # Only show tools from selected category
    if selected_category:
        tools_in_category = tool_categories[selected_category]
        st.markdown(f"### {selected_category} Tools ({len(tools_in_category)})")
        
        # Create grid layout for tools
        cols = st.columns(3)
        for i, tool in enumerate(tools_in_category):
            with cols[i % 3]:
                if st.button(tool, key=f"cat_{tool}"):
                    st.session_state.selected_tool = tool

with tab2:
    if search_term:
        st.markdown(f"### Search Results for '{search_term}' ({len(filtered_tools)})")
        
        # Create grid layout for search results
        cols = st.columns(3)
        for i, tool in enumerate(filtered_tools[:30]):  # Limit to 30 results
            with cols[i % 3]:
                if st.button(tool, key=f"search_{tool}"):
                    st.session_state.selected_tool = tool
    else:
        st.info("Enter a search term in the sidebar to find specific tools.")

# Content generation section
st.header("✨ Create Content")

# Display selected tool or default
selected_tool = st.session_state.get('selected_tool', 'Smart Content Creator')
st.markdown(f"### Currently using: **{selected_tool}**")

# Content prompt area
user_prompt = st.text_area("What would you like to create?", height=100)

# Advanced options expander
with st.expander("⚙️ Advanced Options"):
    template_edit = st.text_area(
        "Customize prompt template (use {prompt} as placeholder for your input):",
        value=st.session_state.prompt_templates.get(selected_tool, "Create {prompt}"),
        height=100
    )
    st.session_state.prompt_templates[selected_tool] = template_edit
    
    # Output length slider
    output_length = st.select_slider(
        "Output Length:",
        options=["Brief", "Standard", "Detailed", "Comprehensive"],
        value="Standard"
    )
    
    # Creativity slider
    creativity = st.slider("Creativity:", min_value=0.0, max_value=1.0, value=0.7, step=0.1)

# Generate button
generate_pressed = st.button("🚀 Generate", type="primary")

# Content generation
if generate_pressed and user_prompt and st.session_state.api_key:
    # Prepare prompt with template
    template = st.session_state.prompt_templates.get(selected_tool, "Create {prompt}")
    formatted_prompt = template.replace("{prompt}", user_prompt)
    
    # Add length instruction
    length_instructions = {
        "Brief": "Keep the response concise and to the point.",
        "Standard": "Provide a standard-length response with adequate detail.",
        "Detailed": "Include thorough details and explanations in the response.",
        "Comprehensive": "Create a comprehensive, in-depth response with extensive details."
    }
    
    full_prompt = f"""{formatted_prompt}
{length_instructions[output_length]}
Make the content {int(creativity * 100)}% creative and {int((1-creativity) * 100)}% factual."""

    # Generate content
    output = generate_ai_content(full_prompt, st.session_state.api_key, st.session_state.api_model)
    
    # Display output
    st.markdown("### 🎉 Your AI-Generated Content")
    with st.container(border=True):
        st.markdown(output)
    
    # Download button
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{selected_tool.replace(' ', '_')}_{timestamp}.txt"
    
    st.download_button(
        label="📥 Download as Text",
        data=output,
        file_name=filename,
        mime="text/plain",
    )
    
    # Save to history
    save_to_history(selected_tool, user_prompt, output)
    
elif generate_pressed and not user_prompt:
    st.warning("Please enter what you'd like to create.")
elif generate_pressed and not st.session_state.api_key:
    st.error("Please enter your API key in the sidebar.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center">
    <p>Ultimate AI Creator Hub | 2025 | The complete solution for AI-powered content creation</p>
</div>
""", unsafe_allow_html=True)

# Add quick-access template section
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔄 Quick Templates")
quick_templates = [
    "Write a blog post about",
    "Create a marketing email for",
    "Design a social media campaign for",
    "Draft a business proposal for",
    "Generate a creative story about"
]

selected_template = st.sidebar.selectbox("Templates:", quick_templates)
if st.sidebar.button("📋 Use Template"):
    st.session_state.template_text = selected_template
    st.experimental_rerun()

# Export/Import functionality
st.sidebar.markdown("---")
st.sidebar.markdown("### 💾 Export/Import History")

# Export history
if st.session_state.history and st.sidebar.button("📤 Export History"):
    history_json = json.dumps(st.session_state.history)
    b64_history = base64.b64encode(history_json.encode()).decode()
    href = f'<a href="data:application/json;base64,{b64_history}" download="ai_content_history.json">Download History File</a>'
    st.sidebar.markdown(href, unsafe_allow_html=True)

# Import history
uploaded_file = st.sidebar.file_uploader("Import History:", type=['json'])
if uploaded_file is not None:
    try:
        imported_history = json.loads(uploaded_file.read())
        if st.sidebar.button("📥 Load Imported History"):
            st.session_state.history = imported_history
            st.sidebar.success("History imported successfully!")
    except Exception as e:
        st.sidebar.error(f"Error importing history: {e}")

# Add theme selector
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎨 App Theme")
themes = ["Light", "Dark", "Blue", "Green", "Purple"]
selected_theme = st.sidebar.selectbox("Select Theme:", themes, index=0)

# Apply selected theme with custom CSS
theme_colors = {
    "Light": {"bg": "#f8f9fa", "accent": "#3b82f6"},
    "Dark": {"bg": "#1e293b", "accent": "#8b5cf6"},
    "Blue": {"bg": "#f0f9ff", "accent": "#0284c7"},
    "Green": {"bg": "#f0fdf4", "accent": "#16a34a"},
    "Purple": {"bg": "#faf5ff", "accent": "#9333ea"}
}

theme_css = f"""
<style>
    .main {{ background-color: {theme_colors[selected_theme]["bg"]} }}
    .stButton>button {{ background: linear-gradient(90deg, {theme_colors[selected_theme]["accent"]}, {theme_colors[selected_theme]["accent"]}88) }}
</style>
"""
st.sidebar.markdown(theme_css, unsafe_allow_html=True)
