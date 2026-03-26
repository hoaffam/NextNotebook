"""Test imports of new services"""

print("Testing imports...")

try:
    from app.services.summary_service import SummaryService
    print("✓ SummaryService imported")
except Exception as e:
    print(f"✗ SummaryService error: {e}")

try:
    from app.services.classification_service import ClassificationService
    print("✓ ClassificationService imported")
except Exception as e:
    print(f"✗ ClassificationService error: {e}")

try:
    from app.services.web_search_service import WebSearchService
    print("✓ WebSearchService imported")
except Exception as e:
    print(f"✗ WebSearchService error: {e}")

try:
    from app.models.category import CategoryInfo, CategoryAssignment
    print("✓ Category models imported")
except Exception as e:
    print(f"✗ Category models error: {e}")

try:
    from app.graph.workflow import create_rag_workflow
    print("✓ RAG workflow imported")
except Exception as e:
    print(f"✗ RAG workflow error: {e}")

print("\nAll tests completed!")
