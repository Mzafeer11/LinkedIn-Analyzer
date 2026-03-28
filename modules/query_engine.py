"""Module for querying indexed LinkedIn profile data."""

import logging
from typing import Any, Dict, Optional

from llama_index.core import VectorStoreIndex, PromptTemplate

from modules.llm_interface import create_github_llm, explain_model_error
import config

logger = logging.getLogger(__name__)

def generate_initial_facts(index: VectorStoreIndex) -> str:
    """Generates interesting facts about the person's career or education.
    
    Args:
        index: VectorStoreIndex containing the LinkedIn profile data.
        
    Returns:
        String containing interesting facts about the person.
    """
    try:
        # Create LLM for generating facts
        llm_client = create_github_llm(
            temperature=0.0,
            max_new_tokens=500,
            decoding_method="sample"
        )
        
        # Create prompt template
        facts_prompt = PromptTemplate(template=config.INITIAL_FACTS_TEMPLATE)
        
        # Create query engine
        query_engine = index.as_query_engine(
            streaming=False,
            similarity_top_k=config.SIMILARITY_TOP_K,
            llm=llm_client,
            text_qa_template=facts_prompt
        )
        
        # Execute the query
        query = "Provide three interesting facts about this person's career or education."
        response = query_engine.query(query)
        
        # Format facts with markdown for pretty display
        facts_text = response.response.strip()
        
        # If facts are numbered, keep them; otherwise format as bullet points
        if not any(line.strip().startswith(str(i)) for i in range(1, 5) for line in facts_text.split('\n')):
            # Not numbered, let's format nicely
            formatted = facts_text
        else:
            formatted = facts_text
        
        return f"📌 **Career & Education Insights:**\n\n{formatted}"
    except Exception as e:
        logger.error(f"Error in generate_initial_facts: {e}")
        return f"Failed to generate initial facts. {explain_model_error(e)}"

def answer_user_query(index: VectorStoreIndex, user_query: str) -> Any:
    """Answers the user's question using the vector database and the LLM.
    
    Args:
        index: VectorStoreIndex containing the LinkedIn profile data.
        user_query: The user's question.
        
    Returns:
        Response object containing the answer to the user's question.
    """
    try:
        # Create LLM for answering questions
        llm_client = create_github_llm(
            temperature=0.0,
            max_new_tokens=250,
            decoding_method="greedy"
        )
        
        # Create prompt template
        question_prompt = PromptTemplate(template=config.USER_QUESTION_TEMPLATE)
        
        # Retrieve relevant nodes
        base_retriever = index.as_retriever(similarity_top_k=config.SIMILARITY_TOP_K)
        source_nodes = base_retriever.retrieve(user_query)
        
        # Build context string
        context_str = "\n\n".join([node.node.get_text() for node in source_nodes])
        
        # Create query engine
        query_engine = index.as_query_engine(
            streaming=False,
            similarity_top_k=config.SIMILARITY_TOP_K,
            llm=llm_client,
            text_qa_template=question_prompt
        )
        
        # Execute the query
        answer = query_engine.query(user_query)
        
        # Format answer with markdown
        answer_text = answer.response.strip() if hasattr(answer, 'response') else str(answer)
        formatted_answer = f"💡 **Response:**\n\n{answer_text}"
        
        # Return formatted response
        class FormattedResponse:
            def __init__(self, text):
                self.response = formatted_answer
        
        return FormattedResponse(formatted_answer)
    except Exception as e:
        logger.error(f"Error in answer_user_query: {e}")
        return f"Failed to get an answer. {explain_model_error(e)}"