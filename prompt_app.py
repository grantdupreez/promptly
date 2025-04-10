import streamlit as st
import json
import os
import uuid
import datetime
import re
from pathlib import Path
import time

# File path for storing prompts - use Streamlit's session state for persistence
PROMPTS_KEY = "claude_prompts_data"

def load_prompts():
    """Load prompts from session state or initialize with defaults if not present"""
    if PROMPTS_KEY in st.session_state:
        return st.session_state[PROMPTS_KEY]
    
    # Default prompts structure
    default_prompts = {
        "Writing": [
            {
                "id": str(uuid.uuid4()),
                "name": "Essay Outline",
                "description": "Creates a detailed essay outline on any topic",
                "prompt": "Create a detailed essay outline on {topic}. Include introduction, main points with supporting evidence, and conclusion.",
                "tags": ["academic", "writing", "organization"],
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat(),
                "version": 1,
                "favorite": False,
                "usage_count": 0
            }
        ],
        "Analysis": [
            {
                "id": str(uuid.uuid4()),
                "name": "Data Analysis Plan",
                "description": "Helps plan data analysis approach",
                "prompt": "I need to analyze {dataset_description}. Please create a step-by-step plan for analyzing this data, including preprocessing steps, analysis methods, and visualization approaches.",
                "tags": ["data", "planning", "research"],
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat(),
                "version": 1,
                "favorite": False,
                "usage_count": 0
            }
        ],
        "Coding": [
            {
                "id": str(uuid.uuid4()),
                "name": "Code Improvement",
                "description": "Suggests improvements for code",
                "prompt": "Review this code and suggest improvements for readability, efficiency, and best practices:\n\n```\n{code}\n```",
                "tags": ["coding", "review", "optimization"],
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat(),
                "version": 1,
                "favorite": False,
                "usage_count": 0
            }
        ],
        "Claude Specific": [
            {
                "id": str(uuid.uuid4()),
                "name": "XML Tags Structure",
                "description": "Ask Claude to use specific XML tags in responses",
                "prompt": "Please structure your response using the following XML tags: <{tag_name}>. Each section should be clearly marked.",
                "tags": ["claude", "formatting", "structure"],
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat(),
                "version": 1,
                "favorite": False,
                "usage_count": 0
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Step-by-Step Reasoning",
                "description": "Ask Claude to use step-by-step reasoning",
                "prompt": "Please solve this problem using step-by-step reasoning. Think about each part of the problem separately before providing your final answer: {problem}",
                "tags": ["claude", "reasoning", "problem-solving"],
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat(),
                "version": 1,
                "favorite": False,
                "usage_count": 0
            }
        ]
    }
    
    # Store in session state
    st.session_state[PROMPTS_KEY] = default_prompts
    return default_prompts

def save_prompts(prompts):
    """Save prompts to session state"""
    st.session_state[PROMPTS_KEY] = prompts

def prompt_library():
    """Main function for the prompt library component"""
    
    # Initialize session state for the prompt library
    if 'prompts' not in st.session_state:
        st.session_state.prompts = load_prompts()
    
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = list(st.session_state.prompts.keys())[0] if st.session_state.prompts else None
    
    if 'current_prompt' not in st.session_state:
        st.session_state.current_prompt = None
    
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    
    if 'filter_favorites' not in st.session_state:
        st.session_state.filter_favorites = False
    
    if 'filter_tags' not in st.session_state:
        st.session_state.filter_tags = []
        
    if 'all_tags' not in st.session_state:
        # Generate a list of all unique tags across all prompts
        all_tags = set()
        for category, prompts in st.session_state.prompts.items():
            for prompt in prompts:
                if 'tags' in prompt:
                    all_tags.update(prompt['tags'])
        st.session_state.all_tags = list(all_tags)
    
    # Add the prompt library to the sidebar
    with st.sidebar:
        st.header("📚 Prompt Library")
        
        # Add tabs for browsing and managing prompts
        tab1, tab2, tab3 = st.tabs(["Browse", "Manage", "Import/Export"])
        
        with tab1:
            if not st.session_state.prompts:
                st.info("No prompts available. Add some in the Manage tab.")
            else:
                # Search and filter
                st.subheader("Search & Filter")
                search_col1, search_col2 = st.columns([3, 1])
                
                with search_col1:
                    search_query = st.text_input("Search prompts", value=st.session_state.search_query)
                    st.session_state.search_query = search_query
                
                with search_col2:
                    st.session_state.filter_favorites = st.checkbox("Favorites", value=st.session_state.filter_favorites)
                
                # Tag filtering
                with st.expander("Filter by Tags"):
                    selected_tags = st.multiselect("Select tags", options=st.session_state.all_tags, default=st.session_state.filter_tags)
                    st.session_state.filter_tags = selected_tags
                
                # Category selection
                categories = list(st.session_state.prompts.keys())
                selected_category = st.selectbox("Category", ["All Categories"] + categories, 
                                                index=categories.index(st.session_state.selected_category)+1 if st.session_state.selected_category in categories else 0)
                
                if selected_category != "All Categories":
                    st.session_state.selected_category = selected_category
                
                # Filtered prompts
                filtered_prompts = []
                
                # Get prompts from selected category or all categories
                categories_to_search = [st.session_state.selected_category] if selected_category != "All Categories" else categories
                
                for category in categories_to_search:
                    if category in st.session_state.prompts:
                        for prompt in st.session_state.prompts[category]:
                            # Apply filters
                            search_match = (not search_query or 
                                            search_query.lower() in prompt['name'].lower() or 
                                            search_query.lower() in prompt['description'].lower() or
                                            any(search_query.lower() in tag.lower() for tag in prompt.get('tags', [])))
                            
                            favorite_match = not st.session_state.filter_favorites or prompt.get('favorite', False)
                            
                            tag_match = (not st.session_state.filter_tags or 
                                        any(tag in st.session_state.filter_tags for tag in prompt.get('tags', [])))
                            
                            if search_match and favorite_match and tag_match:
                                # Add category info to each prompt for display
                                prompt_with_category = prompt.copy()
                                prompt_with_category['category'] = category
                                filtered_prompts.append(prompt_with_category)
                
                # Sort prompts: favorites first, then by usage count
                filtered_prompts.sort(key=lambda p: (not p.get('favorite', False), -p.get('usage_count', 0)))
                
                # Display filtered prompts
                if filtered_prompts:
                    for prompt in filtered_prompts:
                        # Create a colored border for favorites
                        favorite_style = "border-left: 4px solid #f5b041;" if prompt.get('favorite', False) else ""
                        
                        # Display prompt in an expander
                        with st.expander(f"{'⭐ ' if prompt.get('favorite', False) else ''}{prompt['name']} ({prompt['category']})"):
                            st.markdown(f"**Description:** {prompt['description']}")
                            
                            # Display version and usage info
                            st.markdown(f"**Version:** {prompt.get('version', 1)} | **Used:** {prompt.get('usage_count', 0)} times")
                            
                            # Display tags
                            if 'tags' in prompt and prompt['tags']:
                                st.markdown("**Tags:** " + ", ".join([f"`{tag}`" for tag in prompt['tags']]))
                            
                            # Action buttons in columns
                            col1, col2, col3 = st.columns([1, 1, 1])
                            
                            with col1:
                                if st.button("Use Prompt", key=f"use_{prompt['id']}"):
                                    st.session_state.current_prompt = prompt["prompt"]
                                    
                                    # Update usage count
                                    for p in st.session_state.prompts[prompt['category']]:
                                        if p['id'] == prompt['id']:
                                            p['usage_count'] = p.get('usage_count', 0) + 1
                                            save_prompts(st.session_state.prompts)
                                            break
                                    
                                    st.toast(f"Prompt '{prompt['name']}' selected")
                            
                            with col2:
                                favorite_state = prompt.get('favorite', False)
                                favorite_label = "♥ Unfavorite" if favorite_state else "♡ Favorite"
                                
                                if st.button(favorite_label, key=f"fav_{prompt['id']}"):
                                    # Toggle favorite status
                                    for p in st.session_state.prompts[prompt['category']]:
                                        if p['id'] == prompt['id']:
                                            p['favorite'] = not p.get('favorite', False)
                                            save_prompts(st.session_state.prompts)
                                            st.experimental_rerun()
                                            break
                            
                            with col3:
                                if st.button("Edit", key=f"edit_{prompt['id']}"):
                                    st.session_state.edit_prompt = prompt
                                    st.session_state.edit_prompt_category = prompt['category']
                                    st.experimental_rerun()  # This triggers a rerun
                else:
                    st.info("No prompts match your search and filters")
        
        with tab2:
            # Check if we're editing a prompt
            if 'edit_prompt' in st.session_state:
                st.subheader(f"Edit Prompt: {st.session_state.edit_prompt['name']}")
                
                with st.form("edit_prompt_form"):
                    edit_name = st.text_input("Prompt Name", value=st.session_state.edit_prompt['name'])
                    edit_description = st.text_area("Description", value=st.session_state.edit_prompt['description'], height=60)
                    edit_prompt = st.text_area("Prompt Template", value=st.session_state.edit_prompt['prompt'], height=150)
                    
                    # Tags
                    current_tags = st.session_state.edit_prompt.get('tags', [])
                    tags_string = ", ".join(current_tags)
                    edit_tags = st.text_input("Tags (comma separated)", value=tags_string)
                    
                    # Category selection
                    existing_categories = list(st.session_state.prompts.keys())
                    edit_category = st.selectbox("Category", existing_categories, index=existing_categories.index(st.session_state.edit_prompt_category))
                    
                    # Version information display
                    current_version = st.session_state.edit_prompt.get('version', 1)
                    st.info(f"Current version: {current_version}")
                    
                    # Versioning option
                    increment_version = st.checkbox("Create new version", value=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        save_button = st.form_submit_button("Save Changes")
                    
                    with col2:
                        cancel_button = st.form_submit_button("Cancel")
                    
                    if save_button:
                        if not edit_name or not edit_prompt:
                            st.error("Name and prompt are required")
                        else:
                            # Parse tags
                            parsed_tags = [tag.strip() for tag in edit_tags.split(",") if tag.strip()]
                            
                            # Find and update the prompt
                            original_category = st.session_state.edit_prompt_category
                            prompt_id = st.session_state.edit_prompt['id']
                            
                            # Remove from original category
                            st.session_state.prompts[original_category] = [p for p in st.session_state.prompts[original_category] if p['id'] != prompt_id]
                            
                            # Create updated prompt
                            updated_prompt = {
                                "id": prompt_id,
                                "name": edit_name,
                                "description": edit_description,
                                "prompt": edit_prompt,
                                "tags": parsed_tags,
                                "updated_at": datetime.datetime.now().isoformat(),
                                "favorite": st.session_state.edit_prompt.get('favorite', False),
                                "usage_count": st.session_state.edit_prompt.get('usage_count', 0)
                            }
                            
                            # Handle versioning
                            if increment_version:
                                updated_prompt["version"] = current_version + 1
                                updated_prompt["created_at"] = datetime.datetime.now().isoformat()
                            else:
                                updated_prompt["version"] = current_version
                                updated_prompt["created_at"] = st.session_state.edit_prompt.get('created_at', datetime.datetime.now().isoformat())
                            
                            # Create category if needed
                            if edit_category not in st.session_state.prompts:
                                st.session_state.prompts[edit_category] = []
                            
                            # Add to selected category
                            st.session_state.prompts[edit_category].append(updated_prompt)
                            
                            # Clean up empty categories
                            for category in list(st.session_state.prompts.keys()):
                                if not st.session_state.prompts[category]:
                                    del st.session_state.prompts[category]
                            
                            # Update all tags list
                            all_tags = set()
                            for category, prompts in st.session_state.prompts.items():
                                for p in prompts:
                                    if 'tags' in p:
                                        all_tags.update(p['tags'])
                            st.session_state.all_tags = list(all_tags)
                            
                            # Save and clear edit state
                            save_prompts(st.session_state.prompts)
                            del st.session_state.edit_prompt
                            del st.session_state.edit_prompt_category
                            st.success("Prompt updated successfully")
                            st.experimental_rerun()
                    
                    if cancel_button:
                        del st.session_state.edit_prompt
                        del st.session_state.edit_prompt_category
                        st.experimental_rerun()
            else:
                st.subheader("Add New Prompt")
                
                # Form for adding new prompts
                with st.form("add_prompt_form"):
                    new_name = st.text_input("Prompt Name")
                    new_description = st.text_area("Description", height=60)
                    new_prompt = st.text_area("Prompt Template", height=150, help="Use {placeholders} for dynamic content")
                    
                    # Tags input
                    new_tags = st.text_input("Tags (comma separated)", help="e.g. claude, writing, academic")
                    
                    # Category selection or creation
                    existing_categories = list(st.session_state.prompts.keys())
                    category_option = st.radio("Category", ["Existing Category", "New Category"])
                    
                    if category_option == "Existing Category" and existing_categories:
                        new_category = st.selectbox("Select Category", existing_categories)
                    else:
                        new_category = st.text_input("New Category Name")
                    
                    # Favorite option
                    favorite = st.checkbox("Add to Favorites")
                    
                    submitted = st.form_submit_button("Add Prompt")
                    
                    if submitted:
                        if not new_name or not new_prompt:
                            st.error("Name and prompt are required")
                        else:
                            # Create category if it doesn't exist
                            if new_category not in st.session_state.prompts:
                                st.session_state.prompts[new_category] = []
                            
                            # Parse tags
                            parsed_tags = [tag.strip() for tag in new_tags.split(",") if tag.strip()]
                            
                            # Add new prompt
                            new_prompt_obj = {
                                "id": str(uuid.uuid4()),
                                "name": new_name,
                                "description": new_description,
                                "prompt": new_prompt,
                                "tags": parsed_tags,
                                "created_at": datetime.datetime.now().isoformat(),
                                "updated_at": datetime.datetime.now().isoformat(),
                                "version": 1,
                                "favorite": favorite,
                                "usage_count": 0
                            }
                            
                            st.session_state.prompts[new_category].append(new_prompt_obj)
                            
                            # Update all tags
                            all_tags = set(st.session_state.all_tags)
                            all_tags.update(parsed_tags)
                            st.session_state.all_tags = list(all_tags)
                            
                            # Save prompts
                            save_prompts(st.session_state.prompts)
                            st.success(f"Added '{new_name}' to {new_category}")
                
                # Delete prompt functionality
                st.subheader("Delete Prompt")
                
                # Get flat list of all prompts for deletion dropdown
                all_prompts = []
                for category, prompts in st.session_state.prompts.items():
                    for prompt in prompts:
                        all_prompts.append((f"{prompt['name']} ({category})", category, prompt['id']))
                
                if all_prompts:
                    # Sort by name
                    all_prompts.sort(key=lambda x: x[0])
                    
                    prompt_names = [p[0] for p in all_prompts]
                    selected_prompt_index = st.selectbox("Select prompt to delete", range(len(prompt_names)), format_func=lambda i: prompt_names[i])
                    
                    if st.button("Delete Prompt", type="primary"):
                        category, prompt_id = all_prompts[selected_prompt_index][1], all_prompts[selected_prompt_index][2]
                        
                        # Remove the prompt
                        st.session_state.prompts[category] = [p for p in st.session_state.prompts[category] if p['id'] != prompt_id]
                        
                        # Clean up empty categories
                        if not st.session_state.prompts[category]:
                            del st.session_state.prompts[category]
                        
                        # Regenerate all tags
                        all_tags = set()
                        for cat, prompts in st.session_state.prompts.items():
                            for p in prompts:
                                if 'tags' in p:
                                    all_tags.update(p['tags'])
                        st.session_state.all_tags = list(all_tags)
                        
                        save_prompts(st.session_state.prompts)
                        st.success(f"Deleted {prompt_names[selected_prompt_index]}")
                        time.sleep(1)  # Brief pause to show the success message
                        st.experimental_rerun()
                else:
                    st.info("No prompts available to delete")
        
        with tab3:
            st.subheader("Import/Export")
            
            # Export functionality
            if st.button("Export Prompts"):
                # Convert prompts to JSON string for download
                json_str = json.dumps(st.session_state.prompts, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name="claude_prompts_export.json",
                    mime="application/json"
                )
            
            # Import functionality
            st.subheader("Import Prompts")
            uploaded_file = st.file_uploader("Upload prompts JSON file", type="json")
            if uploaded_file is not None:
                try:
                    imported_prompts = json.load(uploaded_file)
                    
                    # Validate the structure (basic check)
                    if isinstance(imported_prompts, dict):
                        # Validate and update each prompt structure if needed
                        for category, prompts in imported_prompts.items():
                            for i, prompt in enumerate(prompts):
                                # Ensure all required fields are present
                                if 'id' not in prompt:
                                    prompt['id'] = str(uuid.uuid4())
                                if 'created_at' not in prompt:
                                    prompt['created_at'] = datetime.datetime.now().isoformat()
                                if 'updated_at' not in prompt:
                                    prompt['updated_at'] = datetime.datetime.now().isoformat()
                                if 'version' not in prompt:
                                    prompt['version'] = 1
                                if 'tags' not in prompt:
                                    prompt['tags'] = []
                                if 'favorite' not in prompt:
                                    prompt['favorite'] = False
                                if 'usage_count' not in prompt:
                                    prompt['usage_count'] = 0
                        
                        st.session_state.prompts = imported_prompts
                        
                        # Regenerate all tags
                        all_tags = set()
                        for category, prompts in st.session_state.prompts.items():
                            for p in prompts:
                                if 'tags' in p:
                                    all_tags.update(p['tags'])
                        st.session_state.all_tags = list(all_tags)
                        
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

    # Add a message history section
    if 'message_history' not in st.session_state:
        st.session_state.message_history = []
    
    # Display message history if any
    if st.session_state.message_history:
        st.subheader("Conversation History")
        for i, (role, message) in enumerate(st.session_state.message_history):
            with st.container():
                st.markdown(f"**{role}**:")
                st.write(message)
                st.divider()

if __name__ == "__main__":
    main()
