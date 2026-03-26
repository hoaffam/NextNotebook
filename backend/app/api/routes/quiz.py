"""
Quiz API Routes
Generate and manage quizzes from documents
Quizzes are persisted to MongoDB
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from bson import ObjectId

from app.models.quiz import (
    QuizGenerateRequest,
    QuizResponse,
    QuizQuestion,
    QuizSubmitRequest,
    QuizResultResponse
)
from app.models.user import UserResponse
from app.api.deps import get_mcq_service
from app.services.mcq_generator.mcq_service import MCQGeneratorService
from app.database.mongodb_client import get_mongodb, MongoDBClient
from ..routes.auth import get_current_user
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/generate/", response_model=QuizResponse)
async def generate_quiz(
    request: QuizGenerateRequest,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb),
    mcq_service: MCQGeneratorService = Depends(get_mcq_service)
):
    """
    Generate a quiz from notebook documents using MCQ Generator workflow
    """
    try:
        # Verify notebook belongs to user
        notebook_doc = mongodb.notebooks.find_one({
            "_id": ObjectId(request.notebook_id),
            "user_id": current_user.id
        })
        if not notebook_doc:
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Generate quiz questions using MCQ Generator workflow
        questions = await mcq_service.generate_quiz(
            notebook_id=request.notebook_id,
            num_questions=request.num_questions,
            difficulty=request.difficulty
        )
        
        if not questions:
            raise HTTPException(
                status_code=400,
                detail="Could not generate quiz. Make sure the notebook has documents."
            )
        
        # Create quiz document for MongoDB
        now = datetime.now(timezone.utc)
        quiz_doc = {
            "notebook_id": request.notebook_id,
            "user_id": current_user.id,
            "title": f"Quiz - {notebook_doc['name']}",
            "questions": [q.model_dump() for q in questions],
            "total_questions": len(questions),
            "difficulty": request.difficulty,
            "created_at": now,
            "attempts": 0,
            "best_score": None
        }
        
        # Save to MongoDB
        result = mongodb.db.quizzes.insert_one(quiz_doc)
        quiz_id = str(result.inserted_id)
        
        logger.info(f"Generated and saved quiz {quiz_id} with {len(questions)} questions")
        
        return QuizResponse(
            id=quiz_id,
            notebook_id=request.notebook_id,
            questions=questions,
            total_questions=len(questions),
            difficulty=request.difficulty,
            created_at=now
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quiz generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: str,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb)
):
    """Get a quiz by ID"""
    try:
        quiz_doc = mongodb.db.quizzes.find_one({
            "_id": ObjectId(quiz_id),
            "user_id": current_user.id
        })
    except Exception:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    if not quiz_doc:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return QuizResponse(
        id=str(quiz_doc["_id"]),
        notebook_id=quiz_doc["notebook_id"],
        questions=[QuizQuestion(**q) for q in quiz_doc["questions"]],
        total_questions=quiz_doc["total_questions"],
        difficulty=quiz_doc["difficulty"],
        created_at=quiz_doc["created_at"]
    )


@router.delete("/{quiz_id}")
async def delete_quiz(
    quiz_id: str,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb)
):
    """Delete a quiz"""
    try:
        result = mongodb.db.quizzes.delete_one({
            "_id": ObjectId(quiz_id),
            "user_id": current_user.id
        })
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Quiz not found")
        return {"message": "Quiz deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{quiz_id}/submit", response_model=QuizResultResponse)
async def submit_quiz(
    quiz_id: str,
    submission: QuizSubmitRequest,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb)
):
    """Submit quiz answers and get results"""
    try:
        quiz_doc = mongodb.db.quizzes.find_one({
            "_id": ObjectId(quiz_id),
            "user_id": current_user.id
        })
    except Exception:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    if not quiz_doc:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Grade answers
    correct = 0
    results = []
    
    for question in quiz_doc["questions"]:
        user_answer = submission.answers.get(question["id"])
        is_correct = user_answer == question["correct_answer"]
        
        if is_correct:
            correct += 1
        
        results.append({
            "question_id": question["id"],
            "user_answer": user_answer,
            "correct_answer": question["correct_answer"],
            "is_correct": is_correct,
            "explanation": question["explanation"]
        })
    
    score = (correct / len(quiz_doc["questions"])) * 100 if quiz_doc["questions"] else 0
    
    # Update quiz stats
    current_best = quiz_doc.get("best_score")
    update_data = {"$inc": {"attempts": 1}}
    if current_best is None or score > current_best:
        update_data["$set"] = {"best_score": score}
    
    mongodb.db.quizzes.update_one(
        {"_id": ObjectId(quiz_id)},
        update_data
    )
    
    return QuizResultResponse(
        quiz_id=quiz_id,
        score=score,
        correct_count=correct,
        total_questions=len(quiz_doc["questions"]),
        results=results
    )


@router.get("/notebook/{notebook_id}", response_model=List[QuizResponse])
async def list_quizzes(
    notebook_id: str,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb)
):
    """Get all quizzes for a notebook"""
    quizzes = []
    cursor = mongodb.db.quizzes.find({
        "notebook_id": notebook_id,
        "user_id": current_user.id
    }).sort("created_at", -1)
    
    for doc in cursor:
        quizzes.append(QuizResponse(
            id=str(doc["_id"]),
            notebook_id=doc["notebook_id"],
            questions=[QuizQuestion(**q) for q in doc["questions"]],
            total_questions=doc["total_questions"],
            difficulty=doc["difficulty"],
            created_at=doc["created_at"]
        ))
    
    return quizzes
