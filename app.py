import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import base64
import json
import time
import os
from datetime import datetime

# Configure the Streamlit page
st.set_page_config(
    page_title="Ultimate AI Creator Hub",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (highly condensed)
st.markdown("""<style>.main{background-color:#f8f9fa}.stApp{max-width:1200px;margin:0 auto}.tool-category{font-size:1.2rem;font-weight:bold;margin-top:1rem;color:#1e3a8a}div[data-testid="stVerticalBlock"]{gap:0.5rem}.stButton>button{background:linear-gradient(90deg,#3b82f6,#8b5cf6);color:white;font-weight:600;border-radius:10px;padding:10px 20px;box-shadow:0 4px 14px rgba(0,0,0,0.1);transition:all 0.3s ease}.stButton>button:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,0.15)}div.stTabs [data-baseweb="tab-list"]{gap:8px}div.stTabs [data-baseweb="tab"]{background-color:#f0f9ff;border-radius:8px 8px 0px 0px;padding:10px 16px;font-weight:600}div.stTabs [aria-selected="true"]{background-color:#bfdbfe}.output-box{background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:20px;margin-top:20px}.history-item{padding:10px;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:8px;background-color:white}.category-selector{margin:10px 0}.search-box{margin:15px 0}</style>""", unsafe_allow_html=True)

# Initialize session state
if 'api_key' not in st.session_state: st.session_state.api_key = ""
if 'history' not in st.session_state: st.session_state.history = []
if 'api_model' not in st.session_state: st.session_state.api_model = "gemini-2.0-flash"
if 'prompt_templates' not in st.session_state: st.session_state.prompt_templates = {}

# Function to generate expanded AI tools list
@st.cache_data
def generate_ai_tools():
    # Core categories with most common tools
    core_tools = {
        "Writing": [
            "Resume Generator", "Cover Letter Generator", "Email Writer", "Blog Post Generator", 
            "Content Rewriter", "Grammar Checker", "Summary Generator", "Academic Essay", 
            "Letter Writer", "Script Writer", "Technical Writer", "Research Paper Helper", 
            "Whitepaper Generator", "Thesis Statement", "Literature Review", "Citation Generator",
            "Lab Report Writer", "Case Study Template", "Editorial Guidelines", "Style Guide Creator",
            "Professional Bio", "Executive Summary", "Project Proposal", "Meeting Minutes", 
            "Documentation Writer", "SOP Writer", "Policy Draft Generator", "Legal Document Helper",
            "Contract Clause Generator", "Terms & Conditions", "Privacy Policy Creator"
        ],
        
        "Creative": [
            "Poem Creator", "Story Generator", "Dialogue Creator", "Character Creator", 
            "Book Title Generator", "Horror Story", "Sci-Fi Story", "Song Lyrics", 
            "Children's Story", "Novel Outline", "Metaphor Creator", "Joke Generator", 
            "Fantasy World Builder", "Sci-Fi Technology", "Historical Fiction", "Memoir Starter",
            "Poetry Prompt", "Creative Writing Prompt", "Short Story Starter", "Screenplay Format Helper",
            "Plot Twist Generator", "Character Backstory", "Fictional Setting", "Alternate History",
            "Mythical Creature Creator", "Magic System Designer", "Fictional Language", "Story Conflict Generator"
        ],
        
        "Business": [
            "Business Idea Generator", "Startup Pitch", "SEO Keywords", "Business Consultant",
            "Marketing Strategy", "Grant Proposal", "Freelance Proposal", "LinkedIn Bio", 
            "Branding Guide", "Business Email", "SWOT Analysis", "Business Case", 
            "Market Research", "Competitor Analysis", "Pricing Strategy", "Product Launch Plan", 
            "Go-to-Market Strategy", "Customer Persona", "Mission Statement", "Company Values",
            "Executive Summary", "Business Plan Outline", "Investor Pitch Deck", "Funding Request",
            "Project Timeline", "Risk Assessment", "ROI Calculator", "KPI Framework"
        ],
        
        "Social Media": [
            "Social Post Generator", "Caption Generator", "Viral Tweet", 
            "YouTube Video Idea", "Tagline Creator", "Pinterest Description",
            "Cold Emails", "Podcast Episode", "Content Calendar", "Viral Content Formula", 
            "Influencer Pitch", "Brand Partnership", "YouTube Script", "Dating Profile", 
            "Networking Opener", "TikTok Trend Ideas", "Instagram Story Series",
            "LinkedIn Article", "Twitter Thread", "Facebook Ad Copy", "Hashtag Strategy"
        ],
        
        "Productivity": [
            "Productivity Planner", "Daily Planner", "Travel Itinerary", "Note-Taking Assistant",
            "Brainstorming Tool", "Grocery List", "Interview Coach", "Learning Path Guide",
            "Time Management", "Prioritization Framework", "Decision Matrix", 
            "Problem-Solving", "Critical Thinking", "Goal Setting", "Habit Tracker",
            "Professional Development", "Weekly Schedule", "Project Management", "Task Breakdown"
        ]
    }
    
    # Extended categories
    extended_categories = {
        "Personal Development": [
            "Dream Interpreter", "Therapy Assistant", "Meditation Guide", "Horoscope Reader", 
            "Workout Plan Creator", "Tarot Reader", "Love Letter Generator", "Parenting Guide", 
            "Public Speaking Coach", "Personal Coach", "Mindfulness Coach", "Therapy Journal", 
            "Personal Mission", "Life Purpose", "Stress Management", "Emotional Intelligence", 
            "Gratitude Letter", "Self-Reflection Prompt", "Personal SWOT Analysis", "Life Priorities",
            "Personal Values Explorer", "Habit Change Plan", "Morning Routine", "Evening Ritual",
            "Digital Detox Plan", "Focus Enhancement", "Motivation Builder", "Confidence Booster"
        ],
        
        "Educational": [
            "Homework Helper", "Coding Assistant", "Documentation Generator", "Math Problem Solver",
            "Physics Tutor", "Language Translator", "Essay Outline", "Curriculum Designer",
            "Lesson Plan", "Student Assessment", "Tutoring Script", "Scientific Abstract",
            "Research Methodology", "Data Analysis", "Statistical Helper", "Experimental Design",
            "Chemistry Problem Solver", "Biology Concept Explainer", "History Timeline Creator",
            "Geography Quiz Generator", "Language Learning Exercise", "Music Theory Helper"
        ],
        
        "Marketing": [
            "Ad Copy Generator", "Product Description", "Slogan Maker", "Press Release",
            "Product Naming Tool", "Blog Post", "Book Review", "Product Review",
            "Brand Voice", "User Journey Map", "UX Survey", "A/B Test Planner",
            "Content Calendar", "Email Campaign", "Newsletter Template", "Landing Page Copy",
            "Value Proposition", "USP Generator", "Brand Positioning Statement", "Marketing Persona"
        ],
                 
        "Human Resources": [
            "HR Policy Generator", "Job Description", "Performance Review", "Employee Handbook",
            "Onboarding Process", "Training Manual", "Team Building", "Remote Work Policy",
            "Career Path Advisor", "Salary Negotiation", "Interview Questions", "Feedback Framework",
            "Conflict Resolution", "Diversity Statement", "Employee Survey", "Recognition Program"
        ],
                        
        "Events & Celebrations": [
            "Wedding Speech", "Event Invitation", "Party Planning", "Gift Suggestions",
            "Thank You Note", "Eulogy Writer", "Memorial Service", "Anniversary Message",
            "Family Reunion", "Holiday Tradition", "Cultural Celebration", "Festival Planning",
            "Birthday Message", "Graduation Speech", "Toast Generator", "Ceremony Script"
        ],
                              
        "Relationships": [
            "Relationship Advice", "Conflict Resolution", "Apology Letter", 
            "Friendship Message", "Breakup Letter", "Legacy Letter", "Ethical Will", 
            "Ancestry Interview", "Cultural Heritage", "Dating Conversation Starters",
            "Long-Distance Tips", "Relationship Check-in", "Boundary Setting Guide"
        ],
                      
        "Entertainment": [
            "Movie Review", "Book Club Guide", "Podcast Script", "TED Talk Script",
            "Storyboard Creator", "Souvenir Story", "Photo Caption", "Market Summary",
            "Board Game Rules", "Tabletop RPG Adventure", "Fan Fiction Prompt", "Film Analysis",
            "TV Show Pitch", "Music Review", "Concert Setlist", "Festival Guide"
        ],
        
        "Health & Wellness": [
            "Diet Plan Generator", "Fitness Routine", "Mental Health Guide", "Sleep Improvement Plan",
            "Meditation Script", "Yoga Sequence", "Nutrition Guide", "Symptom Analyzer",
            "Health Goal Setter", "Wellness Challenge", "Self-Care Routine", "Stress Reduction",
            "Hydration Reminder", "Medical Question Helper", "Allergy Management", "Recovery Plan"
        ],
        
        "Finance": [
            "Budget Template", "Investment Strategy", "Debt Reduction Plan", "Retirement Calculator",
            "Tax Preparation Guide", "Financial Goal Setting", "Expense Tracker", "Savings Plan",
            "Financial Literacy Guide", "Money Management Tips", "Real Estate Analysis", "Mortgage Helper",
            "Credit Score Improvement", "Insurance Guide", "Cryptocurrency Explainer", "Estate Planning"
        ],
        
        "Technology": [
            "Tech Tutorial Writer", "Software Comparison", "Digital Transformation Guide", "IT Solution Finder",
            "Cybersecurity Tips", "Data Privacy Guide", "Tech Trend Analysis", "Digital Strategy",
            "AI Use Case Generator", "Blockchain Explainer", "Software Requirements", "Tech Roadmap",
            "API Documentation", "System Architecture", "Database Schema", "Cloud Migration Plan"
        ],
        
        "Legal": [
            "Legal Agreement Writer", "Disclaimer Generator", "Copyright Notice", "DMCA Template",
            "Legal Term Explainer", "Intellectual Property Guide", "Compliance Checklist", "Legal Research",
            "Contract Review Guide", "Licensing Agreement", "Partnership Agreement", "NDA Generator"
        ]
    }
    
    # Specialized categories
    specialized_categories = {
        "E-commerce": [
            "Product Listing", "Return Policy", "Shipping Information", "Customer FAQ",
            "Abandoned Cart Email", "Product Launch Email", "Discount Announcement", "Sale Campaign"
        ],
        
        "Food & Cooking": [
            "Recipe Creator", "Food Description", "Cooking Tutorial", "Menu Design",
            "Meal Plan Generator", "Food Blog Post", "Flavor Profile", "Ingredient Substitution"
        ],
        
        "Travel & Lifestyle": [
            "Travel Guide", "Destination Description", "Packing List", "Travel Blog",
            "Accommodation Review", "Attraction Description", "Local Experience", "Cultural Guide"
        ],
        
        "Academic & Research": [
            "Hypothesis Generator", "Research Question", "Literature Search", "Methodology Designer",
            "Data Collection Plan", "Statistics Explainer", "Academic Presentation", "Grant Application"
        ],
        
        "Nonprofit & Social": [
            "Mission Statement", "Donation Appeal", "Volunteer Recruitment", "Impact Report",
            "Community Survey", "Advocacy Campaign", "Fundraising Letter", "Awareness Campaign"
        ]
    }
    
    # Combine all categories
    all_categories = {**core_tools, **extended_categories, **specialized_categories}
    
    # Create flat list of all tools
    all_tools = []
    for category, tools in all_categories.items():
        all_tools.extend(tools)
    
    return all_tools, all_categories

# Get all tools and categories
ai_tools, tool_categories = generate_ai_tools()

# Function to load prompt templates (condensed)
@st.cache_data
def load_prompt_templates():
    base_templates = {
        "Resume Generator": "Create a professional resume for {prompt}. Include sections for summary, work experience, education, skills, and achievements.",
        "Cover Letter Generator": "Write a persuasive cover letter for {prompt}. It should highlight relevant skills and explain why I'm a good fit for the position.",
        "Poem Creator": "Write a beautiful poem about {prompt}. The poem should be evocative and use vivid imagery.",
        "Story Generator": "Create an engaging story about {prompt}. Include interesting characters, setting, and plot.",
        "Email Writer": "Write a professional email about {prompt}. Ensure it has a clear purpose, concise content, and appropriate tone.",
    }
    
    # Generic template for all other tools
    templates = {}
    for tool in ai_tools:
        if tool in base_templates:
            templates[tool] = base_templates[tool]
        else:
            tool_name = tool.strip()
            templates[tool_name] = f"Generate content using the '{tool_name}' feature for: {{prompt}}. Ensure the output is high quality, relevant, and tailored to the user's needs."
    
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
    st.markdown(f"### 📊 Stats")
    st.markdown(f"**Total Tools:** {len(ai_tools)}+")
    st.markdown(f"**Categories:** {len(tool_categories)}")

# Main app content
st.title("🧠 Ultimate AI Creator Hub")
st.markdown("##### 600+ AI tools to supercharge your creativity and productivity")

# Create tabs for different sections
tabs = st.tabs(["🛠️ Tools", "📚 History", "ℹ️ About"])

with tabs[0]:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Select a Tool")
        selected_category = st.selectbox("Choose a category:", list(tool_categories.keys()), key="category_selector")
        category_tools = tool_categories[selected_category]
        
        # Filter tools based on search term within category
        displayed_tools = [tool for tool in category_tools if tool in filtered_tools]
        selected_tool = st.selectbox("Select a tool:", displayed_tools, key="tool_selector")
        
        # Load templates
        prompt_templates = load_prompt_templates()
        
        # Tool info and input area
        st.markdown(f"### {selected_tool}")
        st.markdown("Enter your request:")
        user_prompt = st.text_area("", height=150, placeholder="Type your request here...")
        
        # Advanced options in expander
        with st.expander("Advanced Options"):
            col_a, col_b = st.columns(2)
            with col_a:
                tone = st.selectbox("Tone:", ["Professional", "Casual", "Humorous", "Formal", "Inspirational", "Persuasive", "Educational", "Dramatic"])
            with col_b:
                length = st.select_slider("Length:", options=["Very Short", "Short", "Medium", "Long", "Very Long"])
            
            # Additional advanced options
            format_options = st.multiselect("Format Elements:", ["Headings", "Bullet Points", "Numbered List", "Bold Key Points", "Examples", "Statistics"], default=["Headings", "Bold Key Points"])
            audience = st.selectbox("Target Audience:", ["General", "Professionals", "Students", "Executives", "Technical", "Children", "Seniors"])
        
        generate_button = st.button("🚀 Generate Content")
    
    with col2:
        st.markdown("### Generated Content")
        if generate_button:
            if not st.session_state.api_key:
                st.warning("⚠️ Please enter a valid Google Gemini API Key in the sidebar.")
            else:
                template = prompt_templates.get(selected_tool, "Generate content about: {prompt}")
                format_str = ", ".join(format_options) if format_options else "Standard"
                full_prompt = f"""Task: {selected_tool}
Tone: {tone}
Length: {length}
Format: {format_str}
Audience: {audience}

{template.format(prompt=user_prompt)}"""
                
                output = generate_ai_content(full_prompt, st.session_state.api_key, st.session_state.api_model)
                st.markdown("""<div class="output-box">""", unsafe_allow_html=True)
                st.markdown(output)
                st.markdown("""</div>""", unsafe_allow_html=True)
                
                # Save to history
                save_to_history(selected_tool, user_prompt, output)
                
                # Action buttons
                col_copy, col_edit, col_export = st.columns(3)
                with col_copy: st.button("📋 Copy to Clipboard")
                with col_edit: st.button("✏️ Edit & Refine")
                with col_export:
                    st.download_button(label="💾 Download", data=output, 
                                      file_name=f"{selected_tool.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt", 
                                      mime="text/plain")

with tabs[1]:
    st.markdown("### Your Generation History")
    if not st.session_state.history:
        st.info("You haven't generated any content yet. Your history will appear here.")
    else:
        # History filter
        history_filter = st.text_input("🔍 Filter history:", key="history_filter")
        filtered_history = [item for item in st.session_state.history 
                           if history_filter.lower() in item['tool'].lower() or 
                              history_filter.lower() in item['prompt'].lower()] if history_filter else st.session_state.history
        
        # Display history items
        for i, item in enumerate(filtered_history):
            with st.expander(f"{item['tool']} - {item['timestamp']}"):
                st.markdown(f"**Prompt:** {item['prompt']}")
                st.markdown(f"**Output:**\n{item['output']}")
                col1, col2 = st.columns(2)
                with col1: st.button(f"📋 Copy", key=f"copy_{i}")
                with col2: st.button(f"🔄 Regenerate", key=f"regen_{i}")

with tabs[2]:
    st.markdown("### About Ultimate AI Creator Hub")
    st.markdown("""
    This application provides a comprehensive suite of AI-powered tools to assist with various creative and professional tasks.
    
    **Key Features:**
    - 600+ specialized AI tools in one place
    - Professional content generation
    - History tracking for your generations
    - Advanced customization options
    
    **How to use:**
    1. Enter your Google Gemini API key in the sidebar
    2. Select a tool category and specific tool
    3. Enter your request details
    4. Customize with advanced options as needed
    5. Click 'Generate Content'
    
    **Privacy Note:**
    Your API key is only stored in your current session and is not saved on any server.
    """)

# Footer
st.markdown("---")
st.markdown("""<div style="text-align: center; color: #6b7280; font-size: 0.8rem;">
Ultimate AI Creator Hub • Powered by Gemini • Made with ❤️ • 600+ AI Tools
</div>""", unsafe_allow_html=True)
