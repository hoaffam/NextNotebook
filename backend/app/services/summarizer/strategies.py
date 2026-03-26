"""
Summarization Prompt Templates
Different strategies for generating summaries
"""

# Document Summary Prompt
DOCUMENT_SUMMARY_PROMPT = """Analyze the following document and provide:
1. A comprehensive summary (1 paragraph, about 150-200 words) that captures:
   - Main purpose/objective of the document
   - Key concepts and topics covered
   - Important findings or conclusions

2. Extract 5-8 key topics/keywords that best represent this document.

Document filename: {filename}

Document content:
{text}

Respond in JSON format:
{{
    "summary": "Your detailed summary here...",
    "key_topics": ["topic1", "topic2", "topic3", ...]
}}

IMPORTANT:
- Write the summary in the same language as the document
- Make the summary informative and specific, not generic
- Key topics should be specific terms from the document"""


# Notebook Overview Prompt
NOTEBOOK_OVERVIEW_PROMPT = """Based on the following document summaries from notebook "{notebook_name}", create:

1. A cohesive overview (1-2 paragraphs) that:
   - Describes what this notebook contains
   - Identifies common themes across documents
   - Highlights the main purpose/use case

2. Generate 4-5 suggested questions users could ask about these documents.

Document Summaries:
{summaries_text}

Respond in JSON format:
{{
    "overview": "Your cohesive overview here...",
    "suggested_questions": ["Question 1?", "Question 2?", ...]
}}

Write in the same language as the documents."""


# System prompts
DOCUMENT_ANALYZER_SYSTEM = "You are a document analysis expert. Analyze documents and provide accurate, informative summaries."

RESEARCH_ASSISTANT_SYSTEM = "You are a research assistant helping users understand their document collections."
