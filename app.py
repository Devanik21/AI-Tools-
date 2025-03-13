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

# Custom CSS (condensed)
st.markdown("""<style>.main{background-color:#f8f9fa}.stApp{max-width:1200px;margin:0 auto}.tool-category{font-size:1.2rem;font-weight:bold;margin-top:1rem;color:#1e3a8a}div[data-testid="stVerticalBlock"]{gap:0.5rem}.stButton>button{background:linear-gradient(90deg,#3b82f6,#8b5cf6);color:white;font-weight:600;border-radius:10px;padding:10px 20px;box-shadow:0 4px 14px rgba(0,0,0,0.1);transition:all 0.3s ease}.stButton>button:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,0.15)}div.stTabs [data-baseweb="tab-list"]{gap:8px}div.stTabs [data-baseweb="tab"]{background-color:#f0f9ff;border-radius:8px 8px 0px 0px;padding:10px 16px;font-weight:600}div.stTabs [aria-selected="true"]{background-color:#bfdbfe}.output-box{background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:20px;margin-top:20px}.history-item{padding:10px;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:8px;background-color:white}</style>""", unsafe_allow_html=True)

# Initialize session state
if 'api_key' not in st.session_state: st.session_state.api_key = ""
if 'history' not in st.session_state: st.session_state.history = []
if 'api_model' not in st.session_state: st.session_state.api_model = "gemini-2.0-flash"
if 'prompt_templates' not in st.session_state: st.session_state.prompt_templates = {}

# Expanded list of AI Tools (original + 100 more)
ai_tools = [
    # Original tools
    "Resume Generator", "Cover Letter Generator", "Poem Creator", "Story Generator", "Dream Interpreter", 
    "Email Writer", "Blog Post Generator", "Content Rewriter", "Ad Copy Generator", "Cold Email Generator",
    "Grammar & Spell Checker", "Summary Generator", "Social Media Post Generator", "Product Description Generator",
    "Slogan Maker", "Book Title Generator", "Business Idea Generator", "Character Name Generator",
    "Dialogue Creator", "Motivational Quote Generator", "News Headline Generator", "AI Interview Coach",
    "Academic Essay Generator", "Letter Writer", "Notice Generator", "Debate Outline Maker", "Script Writer",
    "AI Research Assistant", "Startup Pitch Creator", "SEO Keyword Generator", "AI Business Consultant",
    "Tagline Creator", "Caption Generator", "AI Joke Generator", "Metaphor Creator", "Horror Story Generator",
    "Science Fiction Story Generator", "Travel Itinerary Planner", "AI Song Lyrics Writer",
    "Speech Creator", "AI Argument Generator", "Press Release Generator", "Marketing Strategy Maker",
    "Technical Writing Assistant", "AI Homework Helper", "Wedding Speech Generator", "AI Storyboard Creator",
    "Personalized Learning Plan Generator", "Grant Proposal Writer", "Book Review Generator",
    "Product Review Generator", "TED Talk Script Creator", "AI Startup Name Generator", "AI Therapy Bot",
    "AI Meditation Guide", "AI Horoscope Reader", "Personalized Workout Plan Creator", "AI Tarot Reader",
    "Children's Story Creator", "Love Letter Generator", "AI Parenting Guide", "Public Speaking Coach",
    "Academic Research Paper Helper", "Wikipedia Article Generator", "AI Novel Writer", "AI Personal Coach",
    "AI Coding Assistant", "Programming Documentation Generator", "Math Problem Solver",
    "AI Physics Tutor", "Resume Bullet Point Generator", "LinkedIn Bio Writer", "Personal Branding Guide",
    "AI Productivity Planner", "AI Idea Brainstorming Tool", "Freelance Proposal Generator",
    "YouTube Video Idea Generator", "Podcast Episode Planner", "AI Stock Market Summary",
    "AI Mindfulness Coach", "AI Therapy Journal Guide", "AI Language Translator", "AI Recipe Generator",
    "AI Grocery List Creator", "AI Home Decor Stylist", "AI Fashion Stylist", "AI Workout Motivation Coach",
    "AI Travel Guide", "AI Nutritionist", "AI Daily Planner", "AI Essay Outline Generator",
    "AI Note-Taking Assistant", "AI Whitepaper Generator", "AI Freelance Gig Ideas Generator",
    "AI Interview Question Generator", "AI Learning Path Guide", "AI Business Email Generator",
    "AI Resume Optimization Tool", "AI Product Naming Tool", "AI Research Summary Generator",
    
    # Adding 100 more tools
    "Fantasy World Builder", "Sci-Fi Technology Creator", "Historical Fiction Prompt", "Memoir Starter",
    "Educational Curriculum Designer", "Lesson Plan Generator", "Student Assessment Creator", "Tutoring Script",
    "Lab Report Writer", "Scientific Paper Abstract", "Literature Review Helper", "Academic Citation Generator",
    "Thesis Statement Creator", "Research Methodology Guide", "Data Analysis Interpreter", "Statistical Analysis Helper",
    "Experimental Design Assistant", "Survey Question Generator", "Focus Group Moderator Script", "Interview Protocol Creator",
    "Case Study Template", "Business Case Analysis", "SWOT Analysis Generator", "Market Research Summary",
    "Competitor Analysis Framework", "Pricing Strategy Helper", "Product Launch Plan", "Go-to-Market Strategy",
    "Customer Persona Creator", "User Journey Mapper", "User Experience Survey", "A/B Test Planner",
    "Content Calendar Creator", "Editorial Guidelines Generator", "Style Guide Creator", "Brand Voice Developer",
    "Mission Statement Creator", "Company Values Articulator", "Team Building Exercise Planner", "Remote Work Policy Creator",
    "HR Policy Generator", "Job Description Writer", "Performance Review Template", "Employee Handbook Creator",
    "Onboarding Process Designer", "Training Manual Writer", "Professional Development Plan", "Career Path Advisor",
    "Salary Negotiation Script", "Networking Conversation Starter", "Elevator Pitch Creator", "Personal Mission Statement",
    "Life Purpose Explorer", "Goal Setting Framework", "Habit Tracker Template", "Time Management System",
    "Prioritization Framework", "Decision-Making Matrix", "Problem-Solving Framework", "Critical Thinking Exercise",
    "Mindfulness Practice Guide", "Stress Management Plan", "Emotional Intelligence Developer", "Conflict Resolution Script",
    "Relationship Advice Generator", "Dating Profile Writer", "Anniversary Message Creator", "Wedding Vow Writer",
    "Breakup Letter Composer", "Apology Letter Writer", "Gratitude Letter Creator", "Friendship Message Generator",
    "Family Reunion Planner", "Holiday Tradition Creator", "Cultural Celebration Guide", "Festival Planning Assistant",
    "Event Invitation Writer", "Party Planning Checklist", "Gift Suggestion Generator", "Thank You Note Writer",
    "Eulogy Writer", "Memorial Service Planner", "Legacy Letter Creator", "Ethical Will Generator",
    "Bucket List Creator", "Life Story Prompt", "Autobiography Outline", "Family History Recorder",
    "Genealogy Research Guide", "Heirloom Story Documenter", "Ancestry Interview Questions", "Cultural Heritage Explorer",
    "Travel Journal Prompt", "Adventure Planner", "Souvenir Story Creator", "Photo Album Caption Writer",
    "Movie Review Generator", "Book Club Discussion Guide", "Podcast Script Template", "YouTube Video Script",
    "Social Media Content Calendar", "Viral Content Formula", "Influencer Collaboration Pitch", "Brand Partnership Proposal"
]

# Extended categories with new tools
tool_categories = {
    "Writing": ["Resume Generator", "Cover Letter Generator", "Email Writer", "Blog Post Generator", "Content Rewriter", 
                "Grammar & Spell Checker", "Summary Generator", "Academic Essay Generator", "Letter Writer", 
                "Script Writer", "Technical Writing Assistant", "Research Paper Helper", "Whitepaper Generator",
                "Thesis Statement Creator", "Literature Review Helper", "Academic Citation Generator", "Lab Report Writer",
                "Case Study Template", "Editorial Guidelines Generator", "Style Guide Creator"],
    
    "Creative": ["Poem Creator", "Story Generator", "Dialogue Creator", "Character Name Generator", "Book Title Generator", 
                 "Horror Story Generator", "Science Fiction Story Generator", "AI Song Lyrics Writer", "Children's Story Creator",
                 "AI Novel Writer", "Metaphor Creator", "AI Joke Generator", "Fantasy World Builder", "Sci-Fi Technology Creator",
                 "Historical Fiction Prompt", "Memoir Starter", "Wedding Vow Writer", "Family History Recorder",
                 "Adventure Planner", "Travel Journal Prompt"],
    
    "Business": ["Business Idea Generator", "Startup Pitch Creator", "SEO Keyword Generator", "AI Business Consultant",
                 "Marketing Strategy Maker", "Grant Proposal Writer", "Freelance Proposal Generator", 
                 "LinkedIn Bio Writer", "Personal Branding Guide", "Business Email Generator", "SWOT Analysis Generator", 
                 "Business Case Analysis", "Market Research Summary", "Competitor Analysis Framework", 
                 "Pricing Strategy Helper", "Product Launch Plan", "Go-to-Market Strategy", "Customer Persona Creator",
                 "Mission Statement Creator", "Company Values Articulator"],
    
    "Social Media": ["Social Media Post Generator", "Caption Generator", "Viral Tweet Generator", 
                     "YouTube Video Idea Generator", "Tagline Creator", "Pinterest Title & Description",
                     "Personalized Cold Emails", "Podcast Episode Planner", "Social Media Content Calendar",
                     "Viral Content Formula", "Influencer Collaboration Pitch", "Brand Partnership Proposal",
                     "YouTube Video Script", "Dating Profile Writer", "Networking Conversation Starter"],
    
    "Productivity": ["AI Productivity Planner", "Daily Planner", "Travel Itinerary Planner", "AI Note-Taking Assistant",
                     "AI Idea Brainstorming Tool", "Grocery List Creator", "AI Interview Coach", "Learning Path Guide",
                     "Time Management System", "Prioritization Framework", "Decision-Making Matrix", 
                     "Problem-Solving Framework", "Critical Thinking Exercise", "Goal Setting Framework", 
                     "Habit Tracker Template", "Professional Development Plan"],
    
    "Personal": ["Dream Interpreter", "AI Therapy Bot", "AI Meditation Guide", "AI Horoscope Reader", 
                 "Personalized Workout Plan Creator", "AI Tarot Reader", "Love Letter Generator", 
                 "AI Parenting Guide", "Public Speaking Coach", "AI Personal Coach", "AI Mindfulness Coach",
                 "AI Therapy Journal Guide", "Personal Mission Statement", "Life Purpose Explorer",
                 "Stress Management Plan", "Emotional Intelligence Developer", "Gratitude Letter Creator"],
    
    "Educational": ["AI Homework Helper", "AI Coding Assistant", "Programming Documentation Generator", 
                   "Math Problem Solver", "AI Physics Tutor", "AI Language Translator", "Essay Outline Generator",
                   "Educational Curriculum Designer", "Lesson Plan Generator", "Student Assessment Creator",
                   "Tutoring Script", "Scientific Paper Abstract", "Research Methodology Guide",
                   "Data Analysis Interpreter", "Statistical Analysis Helper", "Experimental Design Assistant"],
    
    "Marketing": ["Ad Copy Generator", "Product Description Generator", "Slogan Maker", "Press Release Generator",
                 "AI-Powered Product Naming Tool", "One-Shot Blog Post", "Book Review Generator",
                 "Product Review Generator", "Brand Voice Developer", "User Journey Mapper", 
                 "User Experience Survey", "A/B Test Planner", "Content Calendar Creator"],
                 
    "Human Resources": ["HR Policy Generator", "Job Description Writer", "Performance Review Template", 
                        "Employee Handbook Creator", "Onboarding Process Designer", "Training Manual Writer",
                        "Team Building Exercise Planner", "Remote Work Policy Creator", "Career Path Advisor",
                        "Salary Negotiation Script"],
                        
    "Events & Celebrations": ["Wedding Speech Generator", "Event Invitation Writer", "Party Planning Checklist", 
                              "Gift Suggestion Generator", "Thank You Note Writer", "Eulogy Writer", 
                              "Memorial Service Planner", "Anniversary Message Creator", "Family Reunion Planner",
                              "Holiday Tradition Creator", "Cultural Celebration Guide", "Festival Planning Assistant"],
                              
    "Relationships": ["Relationship Advice Generator", "Conflict Resolution Script", "Apology Letter Writer", 
                      "Friendship Message Generator", "Breakup Letter Composer", "Legacy Letter Creator", 
                      "Ethical Will Generator", "Ancestry Interview Questions", "Cultural Heritage Explorer"],
                      
    "Entertainment": ["Movie Review Generator", "Book Club Discussion Guide", "Podcast Script Template", 
                      "TED Talk Script Creator", "AI Storyboard Creator", "Souvenir Story Creator", 
                      "Photo Album Caption Writer", "AI Stock Market Summary"]
}

# Function to load prompt templates (condensed)
@st.cache_data
def load_prompt_templates():
    templates = {
        "Resume Generator": "Create a professional resume for {prompt}. Include sections for summary, work experience, education, skills, and achievements.",
        "Cover Letter Generator": "Write a persuasive cover letter for {prompt}. It should highlight relevant skills and explain why I'm a good fit for the position.",
        "Poem Creator": "Write a beautiful poem about {prompt}. The poem should be evocative and use vivid imagery.",
    }
    for tool in ai_tools:
        if tool not in templates:
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
    
    # Updated model selection with only Gemini 2.0 Flash and 1.5 Flash
    st.session_state.api_model = st.selectbox(
        "Select AI Model:",
        ["gemini-2.0-flash", "gemini-1.5-flash"],
        index=0
    )
    
    st.markdown("---")
    search_term = st.text_input("🔍 Search for tools:")
    filtered_tools = [tool for tool in ai_tools if search_term.lower() in tool.lower()] if search_term else ai_tools

# Main app content
st.title("🧠 Ultimate AI Creator Hub")
st.markdown("##### 200+ AI tools to supercharge your creativity and productivity")

# Create tabs for different sections
tabs = st.tabs(["🛠️ Tools", "📚 History", "ℹ️ About"])

with tabs[0]:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Select a Tool")
        selected_category = st.selectbox("Choose a category:", list(tool_categories.keys()))
        category_tools = tool_categories[selected_category]
        displayed_tools = [tool for tool in category_tools if tool in filtered_tools]
        selected_tool = st.selectbox("Select a tool:", displayed_tools)
        prompt_templates = load_prompt_templates()
        st.markdown(f"### {selected_tool}")
        st.markdown("Enter your request:")
        user_prompt = st.text_area("", height=150, placeholder="Type your request here...")
        
        with st.expander("Advanced Options"):
            tone = st.selectbox("Tone:", ["Professional", "Casual", "Humorous", "Formal", "Inspirational"])
            length = st.select_slider("Length:", options=["Very Short", "Short", "Medium", "Long", "Very Long"])
        
        generate_button = st.button("🚀 Generate Content")
    
    with col2:
        st.markdown("### Generated Content")
        if generate_button:
            if not st.session_state.api_key:
                st.warning("⚠️ Please enter a valid Google Gemini API Key in the sidebar.")
            else:
                template = prompt_templates.get(selected_tool, "Generate content about: {prompt}")
                full_prompt = f"Task: {selected_tool}\nTone: {tone}\nLength: {length}\n\n{template.format(prompt=user_prompt)}"
                output = generate_ai_content(full_prompt, st.session_state.api_key, st.session_state.api_model)
                st.markdown("""<div class="output-box">""", unsafe_allow_html=True)
                st.markdown(output)
                st.markdown("""</div>""", unsafe_allow_html=True)
                save_to_history(selected_tool, user_prompt, output)
                
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
        for i, item in enumerate(st.session_state.history):
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
    - 200+ specialized AI tools in one place
    - Professional content generation
    - History tracking for your generations
    - Advanced customization options
    
    **How to use:**
    1. Enter your Google Gemini API key in the sidebar
    2. Select a tool category and specific tool
    3. Enter your request details
    4. Click 'Generate Content'
    
    **Privacy Note:**
    Your API key is only stored in your current session and is not saved on any server.
    """)

# Footer
st.markdown("---")
st.markdown("""<div style="text-align: center; color: #6b7280; font-size: 0.8rem;">
Ultimate AI Creator Hub • Powered by Gemini • Made with ❤️
</div>""", unsafe_allow_html=True)
