"""
FAQ Generation Prompt Templates
Different strategies for generating FAQs
"""

# Topic extraction prompt
TOPIC_EXTRACTION_PROMPT = """Analyze the following content and identify the main topics covered.

Content:
{text}

Respond in JSON format:
{{
    "topics": ["Topic 1", "Topic 2", ...],
    "topic_type": "single" or "multi"
}}

Guidelines:
- If the content focuses on one main subject → topic_type = "single"
- If the content covers multiple distinct subjects → topic_type = "multi"
- List 3-7 specific topics found in the content
- Topics should be concise (1-4 words each)

IMPORTANT: Return only the JSON, no other text."""


# Single-topic FAQ generation prompt
SINGLE_TOPIC_FAQ_PROMPT = """Based on the following content about {main_topic}, generate {num_questions} frequently asked questions (FAQ) with detailed answers.

Content:
{text}

Requirements:
1. Generate exactly {num_questions} FAQ pairs
2. Each FAQ must have:
   - A clear, specific question users might ask
   - A comprehensive answer (2-4 sentences)
   - The answer should be informative and based on the content

3. Questions should:
   - Cover different aspects of the topic
   - Be practical and relevant
   - Use natural language ("How...", "What...", "Why...", "When...")

Respond in JSON array format:
[
  {{
    "question": "Your question here?",
    "answer": "Detailed answer here."
  }},
  ...
]

IMPORTANT:
- Write in the same language as the content
- Answers should be factual and specific
- Return valid JSON array only, no other text"""


# Multi-topic FAQ generation prompt
MULTI_TOPIC_FAQ_PROMPT = """Based on the following content covering multiple topics, generate {num_questions} frequently asked questions (FAQ) with detailed answers.

Detected Topics: {topics}

Content:
{text}

Requirements:
1. Generate exactly {num_questions} FAQ pairs
2. Distribute questions across the different topics
3. Each FAQ must have:
   - A clear, specific question users might ask
   - A comprehensive answer (2-4 sentences)
   - A topic tag indicating which topic it relates to

4. Questions should:
   - Cover all major topics proportionally
   - Be practical and relevant
   - Use natural language

Respond in JSON array format:
[
  {{
    "question": "Your question here?",
    "answer": "Detailed answer here.",
    "topic": "Related topic from the list"
  }},
  ...
]

IMPORTANT:
- Write in the same language as the content
- Ensure diverse coverage of all topics
- Return valid JSON array only, no other text"""


# System prompts
TOPIC_ANALYZER_SYSTEM = """You are an expert content analyst who identifies key topics and themes in documents.
You provide accurate topic classification and help organize information effectively."""

FAQ_GENERATOR_SYSTEM = """You are an expert FAQ creator who understands what questions users commonly ask.
You generate clear, helpful questions with comprehensive answers that accurately reflect the source content."""
