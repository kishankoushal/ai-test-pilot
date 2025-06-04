import streamlit as st
import requests
import time
from langsmith import Client
from langsmith_setup import get_langsmith_client, get_project_name
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="QA Assistant – Review Test Plans", layout="wide")

st.title("🧪 QA Assistant – Review Test Plans and Cases")

# Initialize LangSmith client
try:
    client = get_langsmith_client()
    project_name = get_project_name()
    langsmith_available = True
except Exception as e:
    langsmith_available = False
    st.warning(f"⚠️ LangSmith integration not available: {str(e)}")

# Input: Confluence Page ID
page_id = st.text_input("Enter Confluence Page ID")

# ngrok_base_url = "https://9517-2409-40c2-301d-d786-9dab-e442-c408-23aa.ngrok-free.app"
ngrok_base_url = os.environ.get("BACKEND_URL", "http://localhost:8080")

# Create tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["📊 Results", "🔄 Processing Steps", "📈 LangSmith Metrics", "🔗 LangSmith Traces"])

if st.button("🚀 Generate from PRD"):
    start_time = time.time()
    request_id = datetime.now().strftime("%Y%m%d%H%M%S")
    
    with tab2:
        # Create progress placeholders for each step
        status_container = st.container()
        progress_bar = st.progress(0)
        
        step_statuses = {
            "confluence": st.empty(),
            "parsing": st.empty(),
            "chunking": st.empty(),
            "feature_extraction": st.empty(),
            "test_plan": st.empty(),
            "test_case": st.empty()
        }
        
        # Initialize all steps as "Waiting..."
        for step_key, placeholder in step_statuses.items():
            placeholder.info(f"⏳ {step_key.replace('_', ' ').title()}: Waiting...")
            
        # Update overall status
        status_container.info("Starting process...")
    
    try:
        # Step 1: Fetch from Confluence
        with tab2:
            step_statuses["confluence"].success(f"🔄 Fetching from Confluence: In progress...")
            progress_bar.progress(10)
            status_container.info("Fetching PRD from Confluence...")
        
        # Make the actual API call
        res = requests.get(f"{ngrok_base_url}/prd/parse_prd/?page_id={page_id}")
        res.raise_for_status()
        data = res.json()
        
        # Update progress for each step (simulating since we can't track the actual steps in a single API call)
        with tab2:
            step_statuses["confluence"].success(f"✅ Fetching from Confluence: Complete")
            step_statuses["parsing"].success(f"✅ Parsing HTML: Complete")
            step_statuses["chunking"].success(f"✅ Chunking Document: Complete")
            step_statuses["feature_extraction"].success(f"✅ Feature Extraction: Complete")
            step_statuses["test_plan"].success(f"✅ Test Plan Generation: Complete")
            step_statuses["test_case"].success(f"✅ Test Case Generation: Complete")
            progress_bar.progress(100)
            status_container.success(f"✅ Processing complete in {time.time() - start_time:.2f} seconds!")

        # Show results in tab 1
        with tab1:
            st.success("✅ Parsed successfully!")
            
            st.subheader("🔍 Extracted Features")
            for f in data["features"]:
                st.markdown(f"- {f}")

            st.subheader("📝 Test Plans")
            for i, plan in enumerate(data["plans"]):
                st.markdown(f"**Plan {i+1}**:\n\n{plan}")

            st.subheader("🧪 Test Cases")
            for i, tc in enumerate(data["cases"]):
                st.markdown(f"**Case {i+1}**:\n\n{tc}")
                
        # Show LangSmith metrics in tab 3 if available
        if langsmith_available:
            with tab3:
                try:
                    # Fetch recent runs from the last 5 minutes
                    five_minutes_ago = datetime.now() - timedelta(minutes=5)
                    recent_runs = client.list_runs(
                        project_name=project_name,
                        start_time=five_minutes_ago.isoformat(),
                        execution_order=1  # Only parent runs
                    )
                    
                    if recent_runs:
                        # Calculate and display metrics
                        total_tokens = sum(run.metrics.get('total_tokens', 0) for run in recent_runs if hasattr(run, 'metrics'))
                        prompt_tokens = sum(run.metrics.get('prompt_tokens', 0) for run in recent_runs if hasattr(run, 'metrics'))
                        completion_tokens = sum(run.metrics.get('completion_tokens', 0) for run in recent_runs if hasattr(run, 'metrics'))
                        
                        st.metric("Total Tokens Used", f"{total_tokens:,}")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Prompt Tokens", f"{prompt_tokens:,}")
                        with col2:
                            st.metric("Completion Tokens", f"{completion_tokens:,}")
                        
                        # Show run times by component
                        st.subheader("Component Execution Times")
                        run_times = {}
                        for run in recent_runs:
                            name = run.name or "unnamed"
                            duration = run.end_time - run.start_time if run.end_time and run.start_time else 0
                            run_times[name] = duration.total_seconds() if hasattr(duration, 'total_seconds') else 0
                        
                        for name, duration in run_times.items():
                            st.metric(f"{name}", f"{duration:.2f}s")
                    else:
                        st.info("No recent runs found in LangSmith")
                except Exception as e:
                    st.warning(f"Error fetching LangSmith metrics: {str(e)}")
        
            # Show LangSmith traces in tab 4
            with tab4:
                if langsmith_available:
                    try:
                        st.subheader("Recent LangSmith Traces")
                        five_minutes_ago = datetime.now() - timedelta(minutes=5)
                        recent_runs = list(client.list_runs(
                            project_name=project_name,
                            start_time=five_minutes_ago.isoformat(),
                            limit=10
                        ))
                        
                        if recent_runs:
                            langsmith_url = "https://smith.langchain.com"
                            for run in recent_runs:
                                run_id = run.id
                                run_name = run.name or "Unnamed Run"
                                status = run.status
                                start_time = run.start_time.strftime("%H:%M:%S") if run.start_time else "N/A"
                                
                                status_emoji = "✅" if status == "success" else "❌" if status == "error" else "⏳"
                                st.markdown(f"{status_emoji} **{run_name}** - Started at {start_time}")
                                st.markdown(f"[View in LangSmith]({langsmith_url}/runs/{run_id})")
                        else:
                            st.info("No recent traces found in LangSmith")
                    except Exception as e:
                        st.warning(f"Error fetching LangSmith traces: {str(e)}")
                else:
                    st.warning("LangSmith integration not available")
                    
                # Add a direct link to LangSmith project
                if langsmith_available:
                    st.markdown(f"### 🔗 View All Traces")
                    st.markdown(f"[Open Project in LangSmith](https://smith.langchain.com/projects/{project_name})")

    except Exception as e:
        with tab2:
            progress_bar.progress(100)
            status_container.error(f"❌ Process failed after {time.time() - start_time:.2f} seconds")
            
        with tab1:
            st.error(f"❌ Error: {str(e)}")