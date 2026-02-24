from fastapi import APIRouter,Depends, HTTPException
from pydantic import BaseModel
from database import supabase
from auth import get_current_user


router = APIRouter(tags=["projects"])

class ProjectCreate(BaseModel):
    name: str
    description: str = ""

class ProjectSettings(BaseModel):
    embedding_model: str
    rag_strategy: str
    agent_type: str
    chunks_per_search: int
    final_context_size: int
    similarity_threshold: float
    number_of_queries: int
    reranking_enabled: bool
    reranking_model: str
    vector_weight: float
    keyword_weight: float

@router.get("/api/projects")
def get_projects(clerk_id: str = Depends(get_current_user)):
    try:
        result = supabase.table('projects').select('*').eq('clerk_id',clerk_id).execute()
        
        return{
            "message": "Projects retrieved successfully",
            "data": result.data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Failed to get projects: {str(e)}")
    
@router.post("/api/projects")
def create_project(project: ProjectCreate, clerk_id: str = Depends(get_current_user)):
    try:
        project_result = supabase.table('projects').insert({
            "name": project.name,
            "description": project.description,
            "clerk_id": clerk_id
        }).execute()
        
        if not project_result.data:
            raise HTTPException(status_code=402,detail="failed to create the project")
        
        created_project = project_result.data[0]
        project_id = created_project["id"]
        
        settings_result = supabase.table("project_settings").insert({
            "project_id": project_id, 
            "embedding_model": "text-embedding-3-large",
            "rag_strategy": "basic",
            "agent_type": "agentic",
            "chunks_per_search": 10,
            "final_context_size": 5,
            "similarity_threshold": 0.3,
            "number_of_queries": 5,
            "reranking_enabled": True,
            "reranking_model": "rerank-english-v3.0",
            "vector_weight": 0.7,
            "keyword_weight": 0.3,
        }).execute()
        
        if not settings_result.data:
            supabase.table('projects').delete().eq("id",project_id).execute()
            raise HTTPException(
                status_code=422, 
                detail="Failed to create project settings - project creation rolled back"
            )
        
        return {
            "success": True,
            "message": "Project created successfully", 
            "data": created_project 
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An internal server error occurred while creating project: {str(e)}"
        )
        
        
@router.delete("/api/projects/{project_id}")
def delete_project(project_id:str,clerk_id: str =Depends(get_current_user)):
    try:
        project_result = supabase.table("projects").select("*").eq("id",project_id).eq("clerk_id",clerk_id).execute()

        if not project_result.data:
            raise HTTPException(status_code=404,detail="Project not found or access denied")

        deleted_result = supabase.table("projects").delete().eq("id",project_id).eq("clerk_id",clerk_id).execute()
        
        if not deleted_result.data:
            raise HTTPException(status_code=500,detail="Failed to delete project")
        
        return{
            "message":"Project deleted succesfully",
            "data":deleted_result.data[0]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An internal server error occurred while deleting project: {str(e)}"
        )

    