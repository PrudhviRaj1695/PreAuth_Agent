import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Configure Streamlit page
st.set_page_config(
    page_title="🏥 Prior Authorization AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE = "http://localhost:8000"

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">🏥 Agentic AI Prior Authorization System</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar for navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["🔍 Process Authorization", "📊 Batch Processing", "📚 Patient History", "📈 Analytics", "⚙️ System Health"]
    )
    
    # Page routing
    if page == "🔍 Process Authorization":
        show_authorization_page()
    elif page == "📊 Batch Processing":
        show_batch_processing_page()
    elif page == "📚 Patient History":
        show_patient_history_page()
    elif page == "📈 Analytics":
        show_analytics_page()
    elif page == "⚙️ System Health":
        show_health_page()

def show_authorization_page():
    """Single patient authorization processing"""
    st.header("🔍 Process Prior Authorization")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Patient Information")
        patient_id = st.number_input("Patient ID", min_value=1, value=1, step=1)
        
        if st.button("🚀 Process Authorization", type="primary", use_container_width=True):
            process_single_authorization(patient_id)
    
    with col2:
        st.subheader("How it works")
        st.info("""
        **Agentic AI Process:**
        1. 📋 Fetch patient data from database
        2. 🔍 Create semantic query from patient context
        3. 📚 Retrieve relevant SOPs using FAISS vector search
        4. 🤖 AI reasoning agent analyzes patient + SOP data
        5. ✅ Generate approval/denial decision with reasoning
        6. 📝 Log complete audit trail
        """)

def process_single_authorization(patient_id):
    """Process authorization for a single patient"""
    try:
        with st.spinner(f"🤖 Processing authorization for Patient {patient_id}..."):
            response = requests.post(f"{API_BASE}/prior-authorization/{patient_id}")
            
        if response.status_code == 200:
            result = response.json()
            display_authorization_result(result)
        else:
            st.error(f"❌ Error: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API. Make sure FastAPI server is running on http://localhost:8000")
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")

def display_authorization_result(result):
    """Display authorization result in a nice format"""
    # Decision badge
    if result['decision'] == 'Approved':
        st.success(f"✅ **APPROVED** - Patient {result['patient_name']}")
    else:
        st.error(f"❌ **DENIED** - Patient {result['patient_name']}")
    
    # Patient info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Patient ID", result['patient_id'])
    with col2:
        st.metric("Diagnosis Code", result['diagnosis_code'])
    with col3:
        st.metric("Procedure Code", result['procedure_code'])
    
    # Detailed results
    st.subheader("📋 Authorization Details")
    
    with st.expander("🤖 AI Reasoning", expanded=True):
        st.write(result['reasoning'])
    
    with st.expander("📚 Retrieved SOP"):
        st.write(f"**SOP Document:** {result['retrieved_sop']}")
        st.write(f"**Similarity Score:** {result['similarity_score']:.4f}")
    
    with st.expander("🕒 Processing Details"):
        st.json({
            "Timestamp": result['timestamp'],
            "Log ID": result.get('log_id', 'N/A'),
            "Status": result['status']
        })

def show_batch_processing_page():
    """Batch processing interface"""
    st.header("📊 Batch Processing")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Input Patient IDs")
        
        # Option 1: Manual input
        patient_ids_text = st.text_area(
            "Enter Patient IDs (comma-separated):",
            value="1,2,3",
            help="Example: 1,2,3,4,5"
        )
        
        # Option 2: Range input
        st.write("**Or use range:**")
        col_start, col_end = st.columns(2)
        with col_start:
            start_id = st.number_input("Start ID", min_value=1, value=1)
        with col_end:
            end_id = st.number_input("End ID", min_value=1, value=3)
        
        use_range = st.checkbox("Use range instead of manual input")
        
        if st.button("🚀 Process Batch", type="primary", use_container_width=True):
            if use_range:
                patient_ids = list(range(start_id, end_id + 1))
            else:
                try:
                    patient_ids = [int(x.strip()) for x in patient_ids_text.split(',') if x.strip()]
                except ValueError:
                    st.error("❌ Invalid patient ID format. Use comma-separated numbers.")
                    return
            
            process_batch_authorization(patient_ids)
    
    with col2:
        st.subheader("Batch Processing Benefits")
        st.info("""
        **Efficient Processing:**
        - Process multiple patients simultaneously
        - Bulk decision making for high-volume scenarios
        - Consistent application of SOPs across patients
        - Comprehensive batch reporting
        """)

def process_batch_authorization(patient_ids):
    """Process batch authorization"""
    try:
        with st.spinner(f"🤖 Processing {len(patient_ids)} patients..."):
            response = requests.post(
                f"{API_BASE}/batch-authorization",
                json=patient_ids
            )
        
        if response.status_code == 200:
            result = response.json()
            display_batch_results(result)
        else:
            st.error(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def display_batch_results(result):
    """Display batch processing results"""
    st.subheader("📊 Batch Results Summary")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Processed", result['processed_count'])
    with col2:
        st.metric("Approved", result['summary']['approved'], delta=None)
    with col3:
        st.metric("Denied", result['summary']['denied'], delta=None)
    with col4:
        st.metric("Failed", result['failed_count'], delta=None)
    
    # Results visualization
    if result['processed_count'] > 0:
        # Pie chart of decisions
        fig = px.pie(
            values=[result['summary']['approved'], result['summary']['denied']],
            names=['Approved', 'Denied'],
            title="Authorization Decisions Distribution",
            color_discrete_map={'Approved': '#00CC96', 'Denied': '#EF553B'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed results table
        if st.checkbox("Show detailed results"):
            df = pd.DataFrame(result['results'])
            st.dataframe(df, use_container_width=True)

def show_patient_history_page():
    """Patient history interface"""
    st.header("📚 Patient Authorization History")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        patient_id = st.number_input("Patient ID for History", min_value=1, value=1, step=1)
        
        if st.button("📖 Get History", type="primary", use_container_width=True):
            get_patient_history(patient_id)
    
    with col2:
        st.info("""
        **Patient History Features:**
        - Complete authorization timeline
        - Decision patterns and trends
        - SOP usage analysis
        - Compliance tracking
        """)

def get_patient_history(patient_id):
    """Fetch and display patient history"""
    try:
        with st.spinner(f"📖 Fetching history for Patient {patient_id}..."):
            response = requests.get(f"{API_BASE}/patient/{patient_id}/history")
        
        if response.status_code == 200:
            result = response.json()
            display_patient_history(result)
        else:
            st.error(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def display_patient_history(result):
    """Display patient history"""
    st.subheader(f"📋 History for Patient {result['patient_id']}")
    
    if result['authorization_count'] == 0:
        st.warning("No authorization history found for this patient.")
        return
    
    st.metric("Total Authorizations", result['authorization_count'])
    
    # History timeline
    df = pd.DataFrame(result['history'])
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Timeline chart
        fig = px.timeline(
            df,
            x_start='timestamp',
            x_end='timestamp',
            y='decision',
            color='decision',
            title="Authorization Timeline"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed history table
        st.dataframe(df, use_container_width=True)

def show_analytics_page():
    """System analytics dashboard"""
    st.header("📈 System Analytics")
    
    if st.button("🔄 Refresh Analytics", type="primary"):
        get_system_analytics()

def get_system_analytics():
    """Fetch and display system analytics"""
    try:
        with st.spinner("📊 Loading analytics..."):
            response = requests.get(f"{API_BASE}/analytics/decisions")
        
        if response.status_code == 200:
            result = response.json()
            display_analytics(result)
        else:
            st.error(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def display_analytics(result):
    """Display system analytics"""
    stats = result['decision_statistics']
    
    # Key metrics
    st.subheader("📊 System Performance")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Decisions", stats.get('total', 0))
    with col2:
        st.metric("Approval Rate", f"{(stats.get('Approved', 0) / max(stats.get('total', 1), 1) * 100):.1f}%")
    with col3:
        st.metric("Denial Rate", f"{(stats.get('Denied', 0) / max(stats.get('total', 1), 1) * 100):.1f}%")
    
    # Charts
    if stats.get('total', 0) > 0:
        # Decision distribution
        fig = go.Figure(data=[
            go.Bar(
                x=['Approved', 'Denied'],
                y=[stats.get('Approved', 0), stats.get('Denied', 0)],
                marker_color=['#00CC96', '#EF553B']
            )
        ])
        fig.update_layout(title="Decision Distribution")
        st.plotly_chart(fig, use_container_width=True)

def show_health_page():
    """System health check"""
    st.header("⚙️ System Health")
    
    if st.button("🔍 Check System Health", type="primary"):
        check_system_health()

def check_system_health():
    """Check system health"""
    try:
        with st.spinner("🔍 Checking system health..."):
            response = requests.get(f"{API_BASE}/health")
        
        if response.status_code == 200:
            result = response.json()
            st.success("✅ System is healthy!")
            st.json(result)
        else:
            st.error(f"❌ System health check failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to FastAPI backend. Please ensure it's running on http://localhost:8000")
    except Exception as e:
        st.error(f"❌ Health check error: {str(e)}")

if __name__ == "__main__":
    main()
