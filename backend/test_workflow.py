"""Test workflow để debug"""
import asyncio
import sys
sys.path.insert(0, '.')

async def test_workflow():
    print("Testing CRAG workflow...")
    
    try:
        from app.graph.workflow import create_rag_workflow
        from app.api.deps import get_milvus_service, get_embedding_service, get_llm_service
        from app.services.web_search_service import get_web_search_service
        
        milvus = get_milvus_service()
        embedding = get_embedding_service()
        llm = get_llm_service()
        web_search = get_web_search_service()
        
        print(f"Milvus: {type(milvus)}")
        print(f"Embedding: {type(embedding)}")
        print(f"LLM: {type(llm)}")
        print(f"WebSearch: {type(web_search)}")
        print(f"WebSearch enabled: {web_search.is_enabled()}")
        
        print("\nCreating workflow...")
        workflow = create_rag_workflow(
            milvus_service=milvus,
            embedding_service=embedding,
            llm_service=llm,
            web_search_service=web_search
        )
        print(f"Workflow type: {type(workflow)}")
        print("Workflow created successfully!")
        
        # Test invocation
        print("\nTesting invocation...")
        result = await workflow.ainvoke({
            "question": "test",
            "notebook_id": "test123",
            "chat_history": []
        })
        print(f"Result: {result.keys() if result else 'None'}")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow())
