import streamlit as st
import json
import os
from pathlib import Path
import uuid

# File path for storing prompts
PROMPTS_FILE = "claude_prompts.json"

def load_prompts():
    """Load prompts from JSON file"""
    if not os.path.exists(PROMPTS_FILE):
        # Initialize with some default prompts
        default_prompts = {
            "Writing": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Essay Outline",
                    "description": "Creates a detailed essay outline on any topic",
                    "prompt": "Create a detailed essay outline on {topic}. Include introduction, main points with supporting evidence, and conclusion."
                }
            ],
            "Analysis": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Data Analysis Plan",
                    "description": "Helps plan data analysis approach",
                    "prompt": "I need to analyze {dataset_description}. Please create a step-by-step plan for analyzing this data, including preprocessing steps, analysis methods, and visualization approaches."
                }
            ],
            "Coding": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Code Improvement",
                    "description": "Suggests improvements for code",
                    "prompt": "Review this code and suggest improvements for readability, efficiency, and best practices:\n\n```\n{code}\n```"
                }
            ]
        }
        save_prompts(default_prompts)
        return default_prompts
    
    try:
        with open(PROMPTS_FILE, 'r') as f:
            return json.load(f)
    except:
        st.error("Error loading prompts file. Creating a new one.")
        return {}

def save_prompts(prompts):
    """Save prompts to JSON file"""
    with open(PROMPTS_FILE, 'w') as f:
        json.dump(prompts, f, indent=2)

def prompt_library():
    """Main function for the prompt library component"""
    
    # Initialize session state for the prompt library
    if 'prompts' not in st.session_state:
        st.session_state.prompts = load_prompts()
    
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = list(st.session_state.prompts.keys())[0] if st.session_state.prompts else None
    
    if 'current_prompt' not in st.session_state:
        st.session_state.current_prompt = None
    
    # Add the prompt library to the sidebar
    with st.sidebar:
        st.header("📚 Prompt Library")
        
        # Add tabs for browsing and managing prompts
        tab1, tab2 = st.tabs(["Browse", "Manage"])
        
        with tab1:
            if not st.session_state.prompts:
                st.info("No prompts available. Add some in the Manage tab.")
            else:
                # Category selection
                categories = list(st.session_state.prompts.keys())
                selected_category = st.selectbox("Category", categories, index=categories.index(st.session_state.selected_category) if st.session_state.selected_category in categories else 0)
                st.session_state.selected_category = selected_category
                
                # Show prompts in the selected category
                if selected_category in st.session_state.prompts:
                    category_prompts = st.session_state.prompts[selected_category]
                    for prompt in category_prompts:
                        with st.expander(f"**{prompt['name']}**"):
                            st.write(prompt["description"])
                            if st.button("Use Prompt", key=f"use_{prompt['id']}"):
                                st.session_state.current_prompt = prompt["prompt"]
                                # This will be used in the main app to set the prompt
                                st.toast(f"Prompt '{prompt['name']}' selected")
        
        with tab2:
            st.subheader("Add New Prompt")
            
            # Form for adding new prompts
            with st.form("add_prompt_form"):
                new_name = st.text_input("Prompt Name")
                new_description = st.text_area("Description", height=68)
                new_prompt = st.text_area("Prompt Template", height=150, help="Use {placeholders} for dynamic content")
                
                # Category selection or creation
                existing_categories = list(st.session_state.prompts.keys())
                category_option = st.radio("Category", ["Existing Category", "New Category"])
                
                if category_option == "Existing Category" and existing_categories:
                    new_category = st.selectbox("Select Category", existing_categories)
                else:
                    new_category = st.text_input("New Category Name")
                
                submitted = st.form_submit_button("Add Prompt")
                
                if submitted:
                    if not new_name or not new_prompt:
                        st.error("Name and prompt are required")
                    else:
                        # Create category if it doesn't exist
                        if new_category not in st.session_state.prompts:
                            st.session_state.prompts[new_category] = []
                        
                        # Add new prompt
                        st.session_state.prompts[new_category].append({
                            "id": str(uuid.uuid4()),
                            "name": new_name,
                            "description": new_description,
                            "prompt": new_prompt
                        })
                        
                        # Save prompts to file
                        save_prompts(st.session_state.prompts)
                        st.success(f"Added '{new_name}' to {new_category}")
            
            # Import/Export functionality
            st.subheader("Import/Export")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Export Prompts"):
                    # Convert prompts to JSON string for download
                    json_str = json.dumps(st.session_state.prompts, indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name="claude_prompts_export.json",
                        mime="application/json"
                    )
            
            with col2:
                uploaded_file = st.file_uploader("Import Prompts", type="json")
                if uploaded_file is not None:
                    try:
                        imported_prompts = json.load(uploaded_file)
                        # Validate the structure (basic check)
                        if isinstance(imported_prompts, dict):
                            st.session_state.prompts = imported_prompts
                            save_prompts(imported_prompts)
                            st.success("Prompts imported successfully!")
                        else:
                            st.error("Invalid prompts file format")
                    except Exception as e:
                        st.error(f"Error importing prompts: {e}")

def get_current_prompt():
    """Get the currently selected prompt"""
    if 'current_prompt' in st.session_state:
        return st.session_state.current_prompt
    return None

def main():
    st.title("AI Assistant with Prompt Library")
    
    # Initialize the prompt library in the sidebar
    prompt_library()
    
    # Main chat interface
    st.header("Chat with Claude")
    
    # Get the selected prompt if any
    current_prompt = get_current_prompt()
    
    # Text area for user input, prepopulated with the selected prompt
    user_input = st.text_area("Your message", value=current_prompt if current_prompt else "", height=150)
    
    # If the prompt has placeholders, provide fields to fill them
    if current_prompt and "{" in current_prompt and "}" in current_prompt:
        st.subheader("Fill in the placeholders")
        placeholders = {}
        import re
        # Extract placeholders like {name}
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, current_prompt)
        
        # Create input fields for each placeholder
        for placeholder in matches:
            placeholders[placeholder] = st.text_input(f"{placeholder}")
        
        # Replace placeholders in the prompt
        if st.button("Update Prompt with Placeholders"):
            filled_prompt = current_prompt
            for placeholder, value in placeholders.items():
                filled_prompt = filled_prompt.replace(f"{{{placeholder}}}", value)
            
            # Update the text area with the filled prompt
            st.session_state.current_prompt = filled_prompt
            st.experimental_rerun()
    
    # Send button
    if st.button("Send"):
        if user_input:
            # Here you would typically send the message to Claude
            # and get a response
            st.write("User:")
            st.write(user_input)
            
            # Placeholder for Claude's response
            st.write("Claude:")
            st.write("This is where Claude's response would appear.")

if __name__ == "__main__":
    main()
