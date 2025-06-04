import streamlit as st
import requests

st.set_page_config(page_title="QA Assistant – Review Test Plans", layout="wide")

st.title("🧪 QA Assistant – Review Test Plans and Cases")

# Input: Confluence Page ID
page_id = st.text_input("Enter Confluence Page ID")

ngrok_base_url = "https://9517-2409-40c2-301d-d786-9dab-e442-c408-23aa.ngrok-free.app"

if st.button("🚀 Generate from PRD"):
    with st.spinner("Fetching and parsing PRD..."):
        try:
            res = requests.get(f"{ngrok_base_url}/prd/parse_prd/?page_id={page_id}")
            res.raise_for_status()
            data = res.json()

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

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
