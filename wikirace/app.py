import streamlit as st
import asyncio
import time
from wiki_pathfinder import ShortestPathFinder, WikipediaAPI
import aiohttp

st.set_page_config(
    page_title="WikiRace Engine | Ultimate Pathfinder",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Premium Design System
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }

    .main-title {
        font-size: 3rem;
        font-weight: 800;
        background: -webkit-linear-gradient(#2c3e50, #000000);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }

    .subtitle {
        color: #5d6d7e;
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    .input-card {
        background: rgba(255, 255, 255, 0.9);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.3);
        margin-bottom: 2rem;
    }

    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border: none;
        padding: 0.8rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(30, 60, 114, 0.4);
        background: linear-gradient(90deg, #2a5298 0%, #1e3c72 100%);
    }

    .path-step {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 8px solid #2a5298;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin: 1rem 0;
        transition: transform 0.2s ease;
    }

    .path-step:hover {
        transform: scale(1.02);
    }

    .step-badge {
        background: #ebf5fb;
        color: #2a5298;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 8px;
    }

    .article-title {
        font-size: 1.25rem;
        color: #2c3e50;
        font-weight: 600;
        text-decoration: none !important;
    }

    .anchor-text {
        font-size: 0.9rem;
        color: #27ae60;
        font-weight: 500;
        margin-top: 5px;
        display: block;
    }

    .arrow-divider {
        color: #2a5298;
        text-align: center;
        font-size: 1.5rem;
        opacity: 0.5;
    }

    /* Status styling */
    .stStatusWidget {
        background: white !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
    }
</style>
""", unsafe_allow_html=True)

# Header Section
col_logo_1, col_logo_2, col_logo_3 = st.columns([1, 1, 1])
with col_logo_2:
    st.image("logo.png", use_container_width=True)

st.markdown('<h1 class="main-title">WikiRace Engine</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Finding the objective shortest path with precision logic.</p>', unsafe_allow_html=True)

# Input Section
with st.container():
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        start_article = st.text_input("🏁 Starting From", value="Sir Isaac Newton", help="Any Wikipedia article title")
    with col2:
        end_article = st.text_input("🎯 Destination", value="Axolotl", help="The goal article title")
    
    visible_only = st.toggle("Prose-only Navigation", value=True, help="Ignore navboxes and infoboxes for a more human experience")
    
    search_btn = st.button("Calculate Optimal Path")
    st.markdown('</div>', unsafe_allow_html=True)

if search_btn:
    if not start_article or not end_article:
        st.toast("Please specify both points!", icon="⚠️")
    else:
        async def run_search():
            async with aiohttp.ClientSession() as session:
                api = WikipediaAPI(session)
                finder = ShortestPathFinder(start_article, end_article, visible_only=visible_only)
                
                with st.status("**Analyzing Network...**", expanded=True) as status:
                    st.write("🛰️ Resolving canonical titles...")
                    resolved_start = await api.resolve_title(start_article)
                    resolved_end = await api.resolve_title(end_article)
                    
                    if not resolved_start or not resolved_end:
                        st.error("Error: Article nodes not found in database.")
                        return
                    
                    finder.start = resolved_start
                    finder.end = resolved_end
                    
                    # Reset state for search execution
                    from collections import deque
                    finder.forward_queue = deque([finder.start])
                    finder.forward_parent = {finder.start: None}
                    finder.forward_text = {finder.start: ""}
                    finder.backward_queue = deque([finder.end])
                    finder.backward_parent = {finder.end: None}
                    finder.backward_text = {finder.end: ""}

                    start_time = time.time()
                    step = 0
                    path_data = None
                    
                    while finder.forward_queue and finder.backward_queue:
                        step += 1
                        if len(finder.forward_queue) <= len(finder.backward_queue):
                            st.write(f"🔄 Scanning forward frontier: {len(finder.forward_queue)} nodes")
                            intersection = await finder._expand_forward(api)
                        else:
                            st.write(f"🔄 Scanning reverse frontier: {len(finder.backward_queue)} nodes")
                            intersection = await finder._expand_backward(api)
                        
                        if intersection:
                            st.write("⚡ Connection established!")
                            path_data = finder._reconstruct_path(intersection)
                            st.write("📋 Extracting anchor metadata...")
                            path_data = await finder._resolve_missing_texts(api, path_data)
                            break
                    
                    end_time = time.time()
                    status.update(label=f"Analysis Complete in {end_time - start_time:.1f}s", state="complete")
                
                if path_data:
                    st.markdown("### 🏆 Optimal Route Discovered")
                    st.info(f"Synchronized shortest path requires **{len(path_data) - 1}** redirections.")
                    
                    for i, (title, link_text) in enumerate(path_data):
                        st.markdown(f"""
                        <div class="path-step">
                            <span class="step-badge">NODE {i}</span><br>
                            <a class="article-title" href="https://en.wikipedia.org/wiki/{title.replace(' ', '_')}" target="_blank">{title}</a>
                            {f'<span class="anchor-text">🔗 Linked via: "{link_text}"</span>' if link_text and i > 0 else ''}
                        </div>
                        """, unsafe_allow_html=True)
                        if i < len(path_data) - 1:
                            st.markdown('<div class="arrow-divider">⋮</div>', unsafe_allow_html=True)
                else:
                    st.error("Fragmentation Error: No route found between these nodes.")

        asyncio.run(run_search())
