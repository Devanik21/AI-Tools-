import streamlit as st
import google.generativeai as genai

# Configure the Streamlit page
st.set_page_config(
    page_title="AI Creator Hub",
    page_icon="🤖",
    layout="wide",
)

# Custom CSS for styling
st.markdown(
    """
    <style>
        body {
            background-color: #f5f5dc;
        }
        .stSelectbox>div>div {
            background-color: #fff7e6;
            border-radius: 10px;
            padding: 8px;
            font-weight: bold;
        }
        .stButton>button {
            background: linear-gradient(to right, #12c2e9, #c471ed, #f64f59);
            color: white;
            font-weight: bold;
            border-radius: 10px;
            padding: 10px 20px;
            box-shadow: 0px 5px 15px rgba(0, 0, 0, 0.3);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar for API Key
with st.sidebar:
    st.markdown("### 🔑 API Configuration")
    api_key = st.text_input("Enter Google Gemini API Key:", type="password")
    
# Page Header
st.title("🤖 AI Creator Hub")
st.write("Unlock the power of AI with 100+ tools for writing, creativity, and productivity!")

# List of AI Tools
ai_tools = [
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
    "Children’s Story Creator", "Love Letter Generator", "AI Parenting Guide", "Public Speaking Coach",
    "Academic Research Paper Helper", "Wikipedia Article Generator", "AI Novel Writer", "AI Personal Coach",
    "AI Coding Assistant", "Programming Documentation Generator", "Math Problem Solver",
    "AI Physics Tutor", "Resume Bullet Point Generator", "LinkedIn Bio Writer", "Personal Branding Guide",
    "AI Productivity Planner", "AI Idea Brainstorming Tool", "Freelance Proposal Generator",
    "YouTube Video Idea Generator", "Podcast Episode Planner", "AI Stock Market Summary",
    "AI Mindfulness Coach", "AI Therapy Journal Guide", "AI Language Translator", "AI Recipe Generator",
    "AI Grocery List Creator", "AI Home Decor Stylist", "AI Fashion Stylist", "AI Workout Motivation Coach",
    "AI AI-Powered Travel Guide", "AI Nutritionist", "AI Daily Planner", "AI Essay Outline Generator",
    "AI Note-Taking Assistant", "AI Whitepaper Generator", "AI Freelance Gig Ideas Generator",
    "AI Interview Question Generator", "AI Learning Path Guide", "AI Business Email Generator",
    "AI Resume Optimization Tool", "AI AI-Powered Product Naming Tool", "AI Research Summary Generator"
]

# Select an AI Tool
tool = st.selectbox("📌 Choose an AI Tool:", ai_tools)

# Generate button
if st.button("🚀 Generate AI Content"):
    if not api_key:
        st.warning("⚠️ Please enter a valid Google Gemini API Key in the sidebar.")
    else:
        try:
            # Configure API
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            
            # Create a prompt for AI
            prompt = f"Generate content using the '{tool}' feature. Ensure high quality and relevance."
            
            # Generate response
            with st.spinner("🔄 Generating AI content..."):
                response = model.generate_content(prompt)
            
            # Display result
            st.success("✅ Generated AI Content:")
            st.write(response.text)
        
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.info("If you're having issues, try using a different model like 'gemini-1.5-pro'.")
