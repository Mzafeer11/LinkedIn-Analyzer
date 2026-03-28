"""Gradio web interface for the Icebreaker Bot."""

import os
import sys
import logging
import uuid
import traceback
import gradio as gr

from modules.data_extraction import extract_linkedin_profile
from modules.data_processing import split_profile_data, create_vector_database, verify_embeddings
from modules.llm_interface import change_llm_model
from modules.query_engine import generate_initial_facts, answer_user_query
import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Dictionary to store active conversations
active_indices = {}


def _format_ui_error(context: str, error: Exception) -> str:
    """Create a detailed, user-visible error message for UI panels."""
    return (
        f"Error while {context}: {str(error)}\n\n"
        "Troubleshooting:\n"
        "- Ensure GITHUB_TOKEN is set and has GitHub Models permission (Models: Read).\n"
        "- Keep 'Use Mock Data' checked if ProxyCurl API key is not configured.\n"
        "- Verify selected model is available for your GitHub token/account.\n\n"
        "Technical details:\n"
        f"{traceback.format_exc()}"
    )

def process_profile(linkedin_url, api_key, use_mock, selected_model):
    """Process a LinkedIn profile and generate initial facts.
    
    Args:
        linkedin_url: LinkedIn profile URL to process.
        api_key: ProxyCurl API key.
        use_mock: Whether to use mock data.
        selected_model: LLM model to use.
        
    Returns:
        Initial facts about the profile and a session ID for this conversation.
    """
    try:
        # Normalize selected model to a safe value if UI/model config drift occurs.
        if not selected_model:
            selected_model = config.LLM_MODEL_ID

        # Change LLM model if needed
        if selected_model != config.LLM_MODEL_ID:
            change_llm_model(selected_model)
            
        # Use a default URL for mock data if none provided
        if use_mock and not linkedin_url:
            linkedin_url = "https://www.linkedin.com/in/leonkatsnelson/"
            
        # Extract profile data
        profile_data = extract_linkedin_profile(
            linkedin_url,
            api_key if not use_mock else None,
            mock=use_mock
        )
        
        if not profile_data:
            return "Failed to retrieve profile data. Please check the URL or API key.", ""
        
        # Split data into nodes
        nodes = split_profile_data(profile_data)
        
        if not nodes:
            return "Failed to process profile data into nodes.", ""
        
        # Create vector database
        index = create_vector_database(nodes)
        
        if not index:
            return "Failed to create vector database.", ""
        
        # Verify embeddings
        if not verify_embeddings(index):
            logger.warning("Some embeddings may be missing or invalid")
        
        # Generate initial facts
        facts = generate_initial_facts(index)
        
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Store the index for this session
        active_indices[session_id] = index
        
        # Return the facts and session ID
        return f"Profile processed successfully!\n\nHere are 3 interesting facts about this person:\n\n{facts}", session_id
    
    except Exception as e:
        logger.exception("Error in process_profile")
        return _format_ui_error("processing profile", e), ""

def chat_with_profile(session_id, user_query, chat_history):
    """Chat with a processed LinkedIn profile.
    
    Args:
        session_id: Session ID for this conversation.
        user_query: User's question.
        chat_history: Chat history.
        
    Returns:
        Updated chat history.
    """
    if not session_id:
        return chat_history + [[user_query, "No profile loaded. Please process a LinkedIn profile first."]]
    
    if session_id not in active_indices:
        return chat_history + [[user_query, "Session expired. Please process the LinkedIn profile again."]]
    
    if not user_query.strip():
        return chat_history
    
    try:
        # Get the index for this session
        index = active_indices[session_id]
        
        # Answer the user's query
        response = answer_user_query(index, user_query)
        bot_reply = response.response if hasattr(response, "response") else str(response)

        # Update chat history
        return chat_history + [[user_query, bot_reply]]
    
    except Exception as e:
        logger.exception("Error in chat_with_profile")
        return chat_history + [[user_query, _format_ui_error("answering your question", e)]]

def create_gradio_interface():
    """Create the Gradio interface for the Icebreaker Bot."""
    # Define available LLM models
    available_models = [
        "gpt-4o-mini",
        "gpt-4.1-mini",
        "gpt-4.1",
    ]
    default_model = config.LLM_MODEL_ID if config.LLM_MODEL_ID in available_models else available_models[0]
    
    with gr.Blocks(title="LinkedIn Icebreaker Bot") as demo:
        gr.Markdown("# LinkedIn Icebreaker Bot")
        gr.Markdown("Generate personalized icebreakers and chat about LinkedIn profiles")
        
        with gr.Tab("Process LinkedIn Profile"):
            with gr.Row():
                with gr.Column():
                    linkedin_url = gr.Textbox(
                        label="LinkedIn Profile URL",
                        placeholder="https://www.linkedin.com/in/username/"
                    )
                    api_key = gr.Textbox(
                        label="Apify API Token (Leave empty to use mock data)",
                        placeholder="Optional: Your Apify API token",
                        type="password",
                        value=""
                    )
                    use_mock = gr.Checkbox(label="Use Mock Data", value=True)
                    model_dropdown = gr.Dropdown(
                        choices=available_models,
                        label="Select GitHub Models LLM",
                        value=default_model
                    )
                    process_btn = gr.Button("Process Profile")
                
                with gr.Column():
                    result_text = gr.Textbox(label="Initial Facts", lines=10)
                    session_id = gr.State(value="")
            
            process_btn.click(
                fn=process_profile,
                inputs=[linkedin_url, api_key, use_mock, model_dropdown],
                outputs=[result_text, session_id]
            )
        
        with gr.Tab("Chat"):
            gr.Markdown("Chat with the processed LinkedIn profile")
            
            chatbot = gr.Chatbot(height=500)
            chat_input = gr.Textbox(
                label="Ask a question about the profile",
                placeholder="What is this person's current job title?"
            )
            
            chat_btn = gr.Button("Send")
            
            chat_btn.click(
                fn=chat_with_profile,
                inputs=[session_id, chat_input, chatbot],
                outputs=[chatbot]
            )
            
            chat_input.submit(
                fn=chat_with_profile,
                inputs=[session_id, chat_input, chatbot],
                outputs=[chatbot]
            )
    
    return demo

if __name__ == "__main__":
    demo = create_gradio_interface()
    # Launch the Gradio interface
    # For Kaggle: uses queue=True and allows all IPs for Kaggle output reachability
    # For local: share=False by default (use share=True only if tunnel is needed)
    
    is_kaggle = os.path.exists("/kaggle")
    share_link = is_kaggle  # Kaggle often needs share=True for output visibility
    
    print("\n" + "="*60)
    if is_kaggle:
        print("Running on Kaggle - configuring for notebook environment...")
        demo.launch(
            server_name="0.0.0.0",  
            server_port=7860,
            share=share_link,
            show_error=True,
            quiet=False
        )
    else:
        print("Running locally - app available at http://127.0.0.1:5000")
        demo.launch(
            server_name="127.0.0.1",  
            server_port=5000,
            share=share_link,
            show_error=True,
            quiet=False
        )
    print("="*60)