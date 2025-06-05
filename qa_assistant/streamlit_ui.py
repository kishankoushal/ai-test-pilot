import streamlit as st
import requests
import time
from langsmith import Client
from langsmith_setup import get_langsmith_client, get_project_name
import os
from datetime import datetime, timedelta
import pandas as pd

# Initialize session state to persist data between interactions
if "data" not in st.session_state:
    st.session_state.data = None
if "request_id" not in st.session_state:
    st.session_state.request_id = None
if "generation_time" not in st.session_state:
    st.session_state.generation_time = None
if "langsmith_metrics" not in st.session_state:
    st.session_state.langsmith_metrics = None

st.set_page_config(page_title="QA Assistant – Review Test Plans", layout="wide")

st.title("🧪 AI Test Pilot – Review Test Plans and Cases")

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
tab1, tab2 = st.tabs(["📊 Results", "🔄 Processing Steps"])

if st.button("🚀 Generate from PRD"):
    start_time = time.time()
    request_id = datetime.now().strftime("%Y%m%d%H%M%S")
    st.session_state.request_id = request_id
    
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
            step_statuses["confluence"].info(f"🔄 Fetching from Confluence: In progress...")
            progress_bar.progress(10)
            status_container.info("Fetching PRD from Confluence...")
        
        # Make the actual API call
        res = requests.get(f"{ngrok_base_url}/prd/parse_prd/?page_id={page_id}")
        res.raise_for_status()
        data = res.json()
        
        # Store the data in session state to persist it
        st.session_state.data = data
        st.session_state.generation_time = time.time() - start_time
        
        # Simulate realistic step-by-step progress updates
        with tab2:
            # Step 1: Confluence fetching (already completed)
            step_statuses["confluence"].success(f"✅ Fetching from Confluence: Complete")
            progress_bar.progress(20)
            status_container.info("Parsing HTML content...")
            time.sleep(0.5)  # Add slight delay for visual effect
            
            # Step 2: Parsing
            step_statuses["parsing"].info(f"🔄 Parsing HTML: In progress...")
            time.sleep(0.8)
            step_statuses["parsing"].success(f"✅ Parsing HTML: Complete")
            progress_bar.progress(40)
            status_container.info("Chunking document...")
            time.sleep(0.5)
            
            # Step 3: Chunking
            step_statuses["chunking"].info(f"🔄 Chunking Document: In progress...")
            time.sleep(0.8)
            step_statuses["chunking"].success(f"✅ Chunking Document: Complete")
            progress_bar.progress(60)
            status_container.info("Extracting features...")
            time.sleep(0.5)
            
            # Step 4: Feature extraction
            step_statuses["feature_extraction"].info(f"🔄 Feature Extraction: In progress...")
            time.sleep(1.0)
            step_statuses["feature_extraction"].success(f"✅ Feature Extraction: Complete")
            progress_bar.progress(75)
            status_container.info("Generating test plan...")
            time.sleep(0.5)
            
            # Step 5: Test plan generation
            step_statuses["test_plan"].info(f"🔄 Test Plan Generation: In progress...")
            time.sleep(1.2)
            step_statuses["test_plan"].success(f"✅ Test Plan Generation: Complete")
            progress_bar.progress(90)
            status_container.info("Generating test cases...")
            time.sleep(0.5)
            
            # Step 6: Test case generation
            step_statuses["test_case"].info(f"🔄 Test Case Generation: In progress...")
            time.sleep(1.5)
            step_statuses["test_case"].success(f"✅ Test Case Generation: Complete")
            progress_bar.progress(100)
            
            # Complete
            status_container.success(f"✅ Processing complete in {st.session_state.generation_time:.2f} seconds!")
        
        # Fetch LangSmith metrics
        if langsmith_available:
            try:
                # Fetch recent runs from the last hour (to ensure we see data even after page refresh)
                try:
                    one_hour_ago = datetime.now() - timedelta(hours=1)
                    # Format datetime properly for LangSmith API - use string format directly
                    start_time_str = one_hour_ago.strftime("%Y-%m-%dT%H:%M:%S")
                except Exception:
                    # Fallback to string-based time
                    start_time_str = "2025-01-01T00:00:00"
                
                try:
                    recent_runs = client.list_runs(
                        project_name=project_name,
                        start_time=start_time_str,
                        execution_order=1  # Only parent runs
                    )
                except Exception as e:
                    st.warning(f"Error querying LangSmith API: {str(e)}")
                    recent_runs = []
                
                if recent_runs:
                    # Calculate and display metrics - with defensive coding
                    try:
                        total_tokens = sum(run.metrics.get('total_tokens', 0) for run in recent_runs 
                                        if hasattr(run, 'metrics') and isinstance(run.metrics, dict))
                        prompt_tokens = sum(run.metrics.get('prompt_tokens', 0) for run in recent_runs 
                                         if hasattr(run, 'metrics') and isinstance(run.metrics, dict))
                        completion_tokens = sum(run.metrics.get('completion_tokens', 0) for run in recent_runs 
                                             if hasattr(run, 'metrics') and isinstance(run.metrics, dict))
                    except Exception:
                        total_tokens = 0
                        prompt_tokens = 0
                        completion_tokens = 0
                    
                    # Process run data safely
                    run_data = []
                    for run in recent_runs:
                        try:
                            name = run.name if hasattr(run, 'name') and run.name else "unnamed"
                            
                            # Safe duration calculation
                            duration = 0
                            if (hasattr(run, 'end_time') and hasattr(run, 'start_time') and 
                                run.end_time is not None and run.start_time is not None):
                                try:
                                    duration = (run.end_time - run.start_time).total_seconds()
                                except (TypeError, AttributeError):
                                    duration = 0
                                    
                            run_data.append({
                                "name": name,
                                "duration": duration
                            })
                        except Exception:
                            continue
                    
                    st.session_state.langsmith_metrics = {
                        "total_tokens": total_tokens,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "runs": run_data
                    }
                else:
                    st.session_state.langsmith_metrics = None
            except Exception as e:
                st.warning(f"Error fetching LangSmith metrics: {str(e)}")
                st.session_state.langsmith_metrics = None

    except Exception as e:
        with tab2:
            progress_bar.progress(100)
            status_container.error(f"❌ Process failed after {time.time() - start_time:.2f} seconds")
            
        with tab1:
            st.error(f"❌ Error: {str(e)}")

# Display results if data exists in session state
if st.session_state.data is not None:
    data = st.session_state.data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
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
        
        # Add CSV export functionality
        st.subheader("📤 Export Data")
        
        try:
            # Create simple CSV exports without relying on complex formatting
            col1, col2 = st.columns(2)
            
            with col1:
                # Export test plans as CSV
                plans_df = pd.DataFrame({"Test_Plan": data["plans"]})
                plans_csv = plans_df.to_csv(index=True)
                
                st.download_button(
                    label="📥 Download Test Plans (CSV)",
                    data=plans_csv,
                    file_name=f"test_plans_{timestamp}.csv",
                    mime="text/csv",
                    key="download_plans"  # Unique key prevents conflicts
                )
            
            with col2:
                # Export test cases as CSV
                cases_df = pd.DataFrame({"Test_Case": data["cases"]})
                cases_csv = cases_df.to_csv(index=True)
                
                st.download_button(
                    label="📥 Download Test Cases (CSV)",
                    data=cases_csv,
                    file_name=f"test_cases_{timestamp}.csv",
                    mime="text/csv",
                    key="download_cases"  # Unique key prevents conflicts
                )
            
            # Combined export - no need for Excel, just use CSV
            st.markdown("---")
            
            # Create a combined dataframe with features and test cases
            combined_data = []
            max_length = max(len(data["features"]), len(data["cases"]))
            
            for i in range(max_length):
                row = {
                    "Feature": data["features"][i] if i < len(data["features"]) else "",
                    "Test_Case": data["cases"][i] if i < len(data["cases"]) else ""
                }
                combined_data.append(row)
            
            combined_df = pd.DataFrame(combined_data)
            combined_csv = combined_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Complete Test Matrix (CSV)",
                data=combined_csv,
                file_name=f"qa_test_matrix_{timestamp}.csv",
                mime="text/csv",
                key="download_matrix"  # Unique key prevents conflicts
            )
        except Exception as e:
            st.warning(f"Error generating export files: {str(e)}")
            