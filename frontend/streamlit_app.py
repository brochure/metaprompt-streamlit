# frontend/streamlit_app.py
import asyncio
import re
from typing import Set

import streamlit as st
from loguru import logger

from app.main import optimize_prompt

# Page configuration
st.set_page_config(
    page_title="Metaprompt App",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_prompt' not in st.session_state:
    st.session_state.current_prompt = ""
if 'prompt_template' not in st.session_state:
    st.session_state.prompt_template = ""
if 'field_values' not in st.session_state:
    st.session_state.field_values = {}


def extract_field_names(text: str) -> Set[str]:
    """
    Extract all field names from text, supporting:
    - Characters from all languages (including Chinese, Japanese, Korean, Arabic, Cyrillic, etc.)
    - Numbers
    - Underscores
    """
    pattern = r'\{\$([^\}]+)\}'  # Match all non-} characters between {$ and }
    return set(re.findall(pattern, text))


def update_prompt():
    """Update current prompt based on input values"""
    updated_prompt = st.session_state.prompt_template
    for field, value in st.session_state.field_values.items():
        if value:  # Only replace fields with values
            updated_prompt = updated_prompt.replace(f"{{${field}}}", value)
    st.session_state.current_prompt = updated_prompt


def handle_field_input(field_name: str):
    """Callback function for field input handling"""
    st.session_state.field_values[field_name] = st.session_state[f"input_{field_name}"]
    update_prompt()


def handle_template_edit():
    """Callback function for template editing"""
    # Get new template
    new_template = st.session_state.editable_template

    # If template has changed
    if new_template != st.session_state.prompt_template:
        # Get fields from old and new templates
        old_fields = extract_field_names(st.session_state.prompt_template)
        new_fields = extract_field_names(new_template)

        # Update field values dictionary
        st.session_state.field_values = {
            field: st.session_state.field_values.get(field, "")
            for field in new_fields
        }

        # Update template
        st.session_state.prompt_template = new_template

        # Update current prompt
        update_prompt()


# Sidebar
with st.sidebar:
    st.header("Prompt Generator")

    # Original prompt input area
    original_prompt = st.text_area("Enter your request briefly and clearly", height=80)
    if st.button("Generate Prompt"):
        if original_prompt:
            # Call optimize_prompt function
            result = asyncio.run(optimize_prompt(original_prompt))
            logger.info(f"result: {result}")

            if result.get('success') and result.get('data', {}).get('optimized_prompt'):
                optimized_prompt = result['data']['optimized_prompt']
                logger.info(f"optimized_prompt: {optimized_prompt}")
                # Save template and current prompt
                st.session_state.prompt_template = optimized_prompt
                st.session_state.current_prompt = optimized_prompt
                # Reset field values
                st.session_state.field_values = {}
            else:
                error_msg = result.get('error',
                                       'Prompt optimization failed. Please check input or contact administrator.')
                st.error(error_msg)

    # Display editable template and variable inputs if template exists
    if st.session_state.prompt_template:
        st.markdown("---")

        # 1. Editable prompt template
        st.markdown("### 💡 Prompt Template")
        st.caption("You can edit the template directly. Variable format: {$VARIABLE_NAME}")
        edited_template = st.text_area(
            label="Editable Prompt Template",
            value=st.session_state.prompt_template,
            height=200,
            key="editable_template",
            on_change=handle_template_edit
        )

        # st.markdown("---")

        # 2. Dynamic template variable input fields
        current_fields = extract_field_names(st.session_state.prompt_template)
        if current_fields:
            st.markdown("### ⚙️ Template Variables")
            for field in current_fields:
                st.text_input(
                    field,
                    key=f"input_{field}",
                    value=st.session_state.field_values.get(field, ""),
                    on_change=handle_field_input,
                    args=(field,)
                )

            st.markdown("---")

        # 3. Final generated complete prompt
        st.markdown("### 📝 Complete Prompt")
        # st.caption("")
        final_prompt = st.text_area(
            label="This is the final prompt with variables replaced. You can continue editing.",
            value=st.session_state.current_prompt,
            height=200,
            key="final_prompt"
        )

        # Update current prompt if final prompt is edited
        if final_prompt != st.session_state.current_prompt:
            st.session_state.current_prompt = final_prompt

# Main interface
st.title("Chat Assistant")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
prompt = st.chat_input("Enter your question here")
if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    logger.info("sample response 1")
    print("sample response 2")
    # Add backend API call logic here
    response = "This is a sample response"
    with st.chat_message("assistant"):
        st.write(response)
    st.session_state.chat_history.append({"role": "assistant", "content": response})
