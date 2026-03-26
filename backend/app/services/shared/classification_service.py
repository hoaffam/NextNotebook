"""
Document Classification Service
AI-powered document classification using ACM Computing Classification System
Supports multi-label classification with similarity-based matching
"""

from typing import List, Dict, Optional, Tuple
import numpy as np
from app.services.shared.embedding_service import EmbeddingService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


# =============================================================================
# ACM Computing Classification System (Extended)
# =============================================================================

ACM_CATEGORIES = {
    # Level 1: General and reference
    "General and reference": {
        "description": "Tổng quan, sách tham khảo, siêu dữ liệu và các chủ đề chung trong ngành máy tính. General computing literature, surveys, reference works, and cross-cutting concepts.",
        "keywords": ["survey", "overview", "tutorial", "introduction", "handbook", "reference"]
    },

    # Level 1: Hardware
    "Hardware": {
        "description": "Thiết kế, sản xuất và phân tích các thành phần vật lý của máy tính. Computer hardware design, integrated circuits, VLSI, electronic design automation, hardware reliability.",
        "keywords": ["hardware", "circuit", "chip", "VLSI", "processor", "CPU", "GPU", "FPGA", "embedded"]
    },

    # Level 1: Computer systems organization
    "Computer systems organization": {
        "description": "Kiến trúc và tổ chức hệ thống máy tính, bộ xử lý, bộ nhớ, hệ thống song song. Computer architecture, parallel computing, distributed systems, real-time systems.",
        "keywords": ["architecture", "parallel", "distributed", "cluster", "multiprocessor", "memory", "cache", "pipeline"]
    },

    # Level 1: Networks
    "Networks": {
        "description": "Kiến trúc mạng, giao thức, hiệu suất và bảo mật mạng máy tính. Network architecture, protocols, network services, mobile networks, network security.",
        "keywords": ["network", "protocol", "TCP", "IP", "routing", "wireless", "mobile", "5G", "IoT", "internet"]
    },

    # Level 1: Software and its engineering
    "Software and its engineering": {
        "description": "Thiết kế, phát triển, kiểm thử và bảo trì phần mềm. Software development, software engineering, programming languages, compilers, testing, DevOps.",
        "keywords": ["software", "programming", "development", "testing", "agile", "DevOps", "compiler", "IDE", "code", "debugging"]
    },

    # Level 1: Theory of computation
    "Theory of computation": {
        "description": "Mô hình tính toán, thuật toán, độ phức tạp và giới hạn tính toán. Algorithms, computational complexity, automata, formal languages, computability.",
        "keywords": ["algorithm", "complexity", "NP-hard", "automata", "Turing", "optimization", "computational", "theoretical"]
    },

    # Level 1: Mathematics of computing
    "Mathematics of computing": {
        "description": "Toán học ứng dụng trong khoa học máy tính: toán rời rạc, xác suất, thống kê. Discrete mathematics, probability, statistics, numerical analysis, mathematical optimization.",
        "keywords": ["mathematics", "discrete", "probability", "statistics", "numerical", "linear algebra", "calculus", "graph theory"]
    },

    # Level 1: Information systems
    "Information systems": {
        "description": "Hệ thống thu thập, lưu trữ, xử lý và truy xuất thông tin. Database systems, data mining, information retrieval, web systems, data management.",
        "keywords": ["database", "SQL", "NoSQL", "data mining", "information retrieval", "search", "indexing", "warehouse", "ETL"]
    },

    # Level 1: Security and privacy
    "Security and privacy": {
        "description": "Mật mã, bảo mật hệ thống, bảo mật mạng và quyền riêng tư dữ liệu. Cryptography, system security, network security, privacy, authentication, authorization.",
        "keywords": ["security", "cryptography", "encryption", "authentication", "privacy", "malware", "firewall", "vulnerability", "cyber"]
    },

    # Level 1: Human-centered computing
    "Human-centered computing": {
        "description": "Tương tác người-máy, thiết kế giao diện, công nghệ trợ giúp. Human-computer interaction, user interface design, visualization, accessibility, collaborative computing.",
        "keywords": ["HCI", "user interface", "UX", "UI", "visualization", "accessibility", "usability", "interaction", "collaborative"]
    },

    # Level 1: Computing methodologies
    "Computing methodologies": {
        "description": "Phương pháp tính toán: trí tuệ nhân tạo, học máy, đồ họa máy tính, mô phỏng. Artificial intelligence, machine learning, computer graphics, simulation, modeling.",
        "keywords": ["AI", "artificial intelligence", "machine learning", "deep learning", "neural network", "NLP", "computer vision", "graphics", "simulation", "robotics"]
    },

    # Level 1: Applied computing
    "Applied computing": {
        "description": "Ứng dụng khoa học máy tính vào các lĩnh vực khác. Applications in life sciences, physical sciences, business, education, healthcare, e-commerce.",
        "keywords": ["bioinformatics", "healthcare", "e-commerce", "education", "scientific computing", "GIS", "CAD", "digital humanities"]
    },

    # Level 1: Social and professional topics
    "Social and professional topics": {
        "description": "Tác động xã hội, đạo đức, pháp lý và nghề nghiệp của công nghệ. Computing profession, ethics, legal aspects, history of computing, computing education.",
        "keywords": ["ethics", "legal", "profession", "education", "history", "policy", "social impact", "digital divide"]
    }
}


# Extended categories for non-CS domains
EXTENDED_CATEGORIES = {
    "Business and Management": {
        "description": "Quản trị kinh doanh, tài chính, marketing, chiến lược. Business administration, finance, marketing, strategy, operations management, entrepreneurship.",
        "keywords": ["business", "management", "finance", "marketing", "strategy", "leadership", "entrepreneurship", "MBA", "ROI", "KPI"]
    },

    "Natural Sciences": {
        "description": "Khoa học tự nhiên: vật lý, hóa học, sinh học, khoa học môi trường. Physics, chemistry, biology, environmental science, earth sciences.",
        "keywords": ["physics", "chemistry", "biology", "environment", "ecology", "genetics", "molecular", "quantum", "organic"]
    },

    "Engineering": {
        "description": "Các ngành kỹ thuật khác: cơ khí, điện, xây dựng, hóa học. Mechanical, electrical, civil, chemical engineering, materials science.",
        "keywords": ["mechanical", "electrical", "civil", "chemical engineering", "materials", "manufacturing", "structural", "thermodynamics"]
    },

    "Social Sciences": {
        "description": "Khoa học xã hội: tâm lý học, xã hội học, kinh tế học, khoa học chính trị. Psychology, sociology, economics, political science, anthropology.",
        "keywords": ["psychology", "sociology", "economics", "political", "anthropology", "behavior", "social", "cultural", "demographic"]
    },

    "Arts and Humanities": {
        "description": "Nghệ thuật và nhân văn: văn học, lịch sử, triết học, ngôn ngữ. Literature, history, philosophy, languages, arts, music, cultural studies.",
        "keywords": ["literature", "history", "philosophy", "language", "art", "music", "culture", "humanities", "literary"]
    },

    "Health and Medicine": {
        "description": "Y tế và y học: chẩn đoán, điều trị, sức khỏe cộng đồng. Medicine, healthcare, diagnosis, treatment, public health, clinical research.",
        "keywords": ["medical", "health", "clinical", "diagnosis", "treatment", "patient", "hospital", "pharmaceutical", "disease"]
    },

    "Law and Legal": {
        "description": "Pháp luật và luật học: luật dân sự, luật hình sự, luật quốc tế. Civil law, criminal law, international law, contracts, regulations, compliance.",
        "keywords": ["law", "legal", "court", "contract", "regulation", "compliance", "litigation", "attorney", "jurisdiction"]
    },

    "Education and Pedagogy": {
        "description": "Giáo dục và sư phạm: phương pháp giảng dạy, chương trình đào tạo, đánh giá. Teaching methods, curriculum design, assessment, e-learning, educational research.",
        "keywords": ["education", "teaching", "learning", "curriculum", "pedagogy", "student", "classroom", "assessment", "e-learning"]
    }
}

# Combine all categories
ALL_CATEGORIES = {**ACM_CATEGORIES, **EXTENDED_CATEGORIES}


class ClassificationService:
    """Service for AI-powered document classification"""

    def __init__(self):
        """Initialize service and pre-compute category embeddings"""
        self.embedding_service = EmbeddingService()
        self.category_embeddings: Dict[str, List[float]] = {}
        self.categories = ALL_CATEGORIES
        self._initialized = False

        # Configuration
        self.similarity_threshold = 0.45  # Minimum similarity to assign label
        self.max_labels = 3  # Maximum labels per document
        self.confidence_levels = {
            "high": 0.65,    # >= 0.65: Rất chắc chắn
            "medium": 0.55,  # 0.55-0.65: Khá chắc chắn
            "low": 0.45      # 0.45-0.55: Có thể đúng
        }

    async def initialize(self):
        """Pre-compute embeddings for all categories"""
        if self._initialized:
            return

        try:
            logger.info("Initializing category embeddings...")

            for cat_name, cat_info in self.categories.items():
                # Create rich text representation for category
                description = cat_info["description"]
                keywords = ", ".join(cat_info["keywords"])
                category_text = f"{cat_name}: {description} Keywords: {keywords}"

                # Generate embedding
                embedding = await self.embedding_service.embed_text(category_text)
                self.category_embeddings[cat_name] = embedding

            self._initialized = True
            logger.info(f"Initialized embeddings for {len(self.category_embeddings)} categories")

        except Exception as e:
            logger.error(f"Failed to initialize category embeddings: {e}")
            raise

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        a = np.array(vec1)
        b = np.array(vec2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    async def classify_document(
        self,
        summary_embedding: List[float],
        summary_text: str = "",
        key_topics: List[str] = None
    ) -> List[Dict]:
        """
        Classify a document based on its summary embedding

        Args:
            summary_embedding: Embedding vector of document summary
            summary_text: Optional summary text for better matching
            key_topics: Optional list of key topics

        Returns:
            List of category assignments with confidence scores
        """
        try:
            # Ensure categories are initialized
            await self.initialize()

            # Calculate similarity with each category
            similarities = {}
            for cat_name, cat_embedding in self.category_embeddings.items():
                similarity = self._cosine_similarity(summary_embedding, cat_embedding)
                similarities[cat_name] = similarity

            # Sort by similarity
            sorted_categories = sorted(
                similarities.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # Select top categories above threshold
            assigned_categories = []
            for cat_name, score in sorted_categories:
                if score >= self.similarity_threshold and len(assigned_categories) < self.max_labels:
                    # Determine confidence level
                    if score >= self.confidence_levels["high"]:
                        confidence = "high"
                    elif score >= self.confidence_levels["medium"]:
                        confidence = "medium"
                    else:
                        confidence = "low"

                    assigned_categories.append({
                        "category": cat_name,
                        "score": round(score, 4),
                        "confidence": confidence,
                        "is_auto": True  # Automatically assigned
                    })

            # If no categories above threshold, mark as uncategorized
            if not assigned_categories:
                # Still return best match with "uncategorized" flag
                if sorted_categories:
                    best_cat, best_score = sorted_categories[0]
                    assigned_categories.append({
                        "category": "Uncategorized",
                        "score": round(best_score, 4),
                        "confidence": "low",
                        "is_auto": True,
                        "suggested": best_cat  # Suggest the best match
                    })

            logger.info(f"Classified document: {[c['category'] for c in assigned_categories]}")
            return assigned_categories

        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return [{
                "category": "Uncategorized",
                "score": 0,
                "confidence": "low",
                "is_auto": True
            }]

    def get_all_categories(self) -> List[Dict]:
        """Get list of all available categories"""
        categories = []

        # ACM Categories
        for name, info in ACM_CATEGORIES.items():
            categories.append({
                "name": name,
                "description": info["description"],
                "type": "ACM",
                "keywords": info["keywords"]
            })

        # Extended Categories
        for name, info in EXTENDED_CATEGORIES.items():
            categories.append({
                "name": name,
                "description": info["description"],
                "type": "Extended",
                "keywords": info["keywords"]
            })

        return categories

    async def update_document_category(
        self,
        document_id: str,
        categories: List[str],
        mongodb_client
    ) -> bool:
        """
        Update document categories (user override)

        Args:
            document_id: Document ID
            categories: List of category names
            mongodb_client: MongoDB client instance
        """
        try:
            # Validate categories
            valid_categories = []
            for cat in categories:
                if cat in self.categories or cat == "Uncategorized":
                    valid_categories.append({
                        "category": cat,
                        "score": 1.0,  # User assigned = full confidence
                        "confidence": "high",
                        "is_auto": False
                    })

            # Update in MongoDB
            result = mongodb_client.documents.update_one(
                {"_id": document_id},
                {"$set": {"categories": valid_categories}}
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Failed to update categories: {e}")
            return False


# Singleton instance
_classification_service = None

def get_classification_service() -> ClassificationService:
    """Get singleton ClassificationService instance"""
    global _classification_service
    if _classification_service is None:
        _classification_service = ClassificationService()
    return _classification_service
