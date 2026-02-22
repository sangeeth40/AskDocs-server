from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import supabase

router = APIRouter(tags=["users"])
    
@router.post("/create-user")
async def clerk_webhook(webhook_data:dict):
    try:
        if not isinstance(webhook_data, dict):
            raise HTTPException(
                status_code=400, 
                detail="Invalid webhook payload format"
            )
        
        event_type = webhook_data.get("type")
        if event_type != "user.created":
            # Return success for other events (don't retry)
            return {
                "success": True,
                "message": f"Event type '{event_type}' ignored"
            }
        
        user_data = webhook_data.get("data")
        if not user_data or not isinstance(user_data, dict):
            raise HTTPException(
                status_code=400,
                detail="Missing or invalid user data in webhook payload"
            )


        clerk_id = user_data.get("id")
        if not clerk_id or not isinstance(clerk_id, str):
            raise HTTPException(
                status_code=400, 
                detail="Missing or invalid clerk_id in user data"
            )
            
        existing_user = (
            supabase.table("users")
            .select("clerk_id")
            .eq("clerk_id", clerk_id)
            .execute()
        )
        
        if existing_user.data:
            # User already exists - return success (don't retry webhook)
            return {
                "success": True,
                "message": "User already exists",
                "clerk_id": clerk_id
            }
            
        result = supabase.table("users").insert({
            "clerk_id": clerk_id
        }).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=500, 
                detail="Failed to create user in database"
            )
        
        return {
            "success": True,
            "message": "User created successfully",
            "user": result.data[0]
        }



    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Webhook processing failed:{str(e)}")
        
    