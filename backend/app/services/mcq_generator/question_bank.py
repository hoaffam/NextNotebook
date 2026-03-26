"""
MCQ Generation Prompt Templates
Question generation strategies for different difficulty levels
"""

# Base MCQ generation prompt
MCQ_GENERATION_PROMPT = """Based on the following content, generate {num_questions} multiple-choice questions.

Difficulty level: {difficulty}

Content:
{text}

Requirements:
1. Generate exactly {num_questions} questions
2. Each question must have:
   - A clear, specific question
   - Exactly 4 options (A, B, C, D)
   - One correct answer
   - A brief explanation (1-2 sentences) of why the answer is correct

3. Difficulty guidelines:
   - Easy: Direct recall questions, obvious from the text
   - Medium: Requires understanding and interpretation
   - Hard: Requires analysis, inference, or application

4. Questions should cover different topics from the content
5. Avoid ambiguous or trick questions

Respond in JSON array format:
[
  {{
    "question": "Your question here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "A",
    "explanation": "Brief explanation here"
  }},
  ...
]

IMPORTANT:
- Write questions in the same language as the content
- Ensure all 4 options are plausible
- Correct answer must be one of: A, B, C, or D
- Return valid JSON array only, no other text"""


# Difficulty-specific guidance
DIFFICULTY_GUIDELINES = {
    "easy": """
Easy questions should:
- Test direct recall of facts
- Use simple, straightforward language
- Have one obviously correct answer
- Cover key terms and definitions
Example: "What is X?" "When did Y happen?"
""",
    "medium": """
Medium questions should:
- Test understanding of concepts
- Require interpretation of information
- Have plausible distractors
- Test relationships between ideas
Example: "Why does X lead to Y?" "What is the relationship between A and B?"
""",
    "hard": """
Hard questions should:
- Require analysis or application
- Test critical thinking
- Have subtle differences between options
- May involve hypothetical scenarios
Example: "What would happen if X changed?" "Which approach is best for solving Y?"
"""
}


# System prompts
MCQ_GENERATOR_SYSTEM = """You are an expert educational content creator specializing in multiple-choice questions.
You create clear, fair, and pedagogically sound questions that accurately assess understanding.
Your questions are well-balanced, with plausible distractors and unambiguous correct answers."""


# Validation criteria
VALIDATION_CRITERIA = {
    "required_fields": ["question", "options", "correct_answer", "explanation"],
    "options_count": 4,
    "valid_answers": ["A", "B", "C", "D"],
    "min_question_length": 10,
    "min_explanation_length": 20
}
