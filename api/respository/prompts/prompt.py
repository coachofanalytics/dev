from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.db.database import get_db
from models import OpenaiPrompt

from settings import get_db_connection


# Establish a database connection
conn = get_db_connection()
cursor = conn.cursor()


def create_prompt(prompt: OpenaiPrompt):
    try:
        print("am here")
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO getdata_openaiprompt (category, subcategory, topic, expert_question, role) 
                              VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (
                    prompt.category,
                    prompt.subcategory,
                    prompt.topic,
                    prompt.expert_question,
                    prompt.role,
                ),
            )
            new_prompt = cursor.fetchone()

        return {"data": new_prompt}

    except prompt.DOESNOTEXIST:
        print(f"An error occurred: {e}")
        return {"error": str(e)}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}


def get_all_prompts():
    try:
        # Execute the query
        cursor.execute("""SELECT * FROM getdata_openaiprompt""")
        print("Call the method with parentheses")
        my_prompts = cursor.fetchall()  # Call the method with parentheses
        return my_prompts

    except Exception as e:
        # Log the error or print it

        message = "An error occurred"
        print(f"An error occurred: {e}")
        # Return an HTTP exception with a 500 status code
        raise HTTPException(status_code=500, detail="Internal Server Error")


# def create_prompt(new_prompt:Inventory):
#     inventory_prompts=[]
#     prompt_dict=new_prompt.dict()
#     prompt_dict['id']=randrange(0,1000000)
#     inventory_prompts.append(prompt_dict)
#     message=f'prompt_name:{new_prompt.name},prompt_price:{new_prompt.price},prompt_price:{new_item.brand},item_price:{new_item.status}'
#     return {"data":prompts}


# def get_by_id(prompt_id:int):
#     if prompt_id not in inventory_list:
#         raise HTTPException(status_code=404)
#     else:
#         prompt =inventory_list[prompt_id]
#     return {"data":prompt}

router = APIRouter()


@router.get("/")
async def get_prompts(db: Session = Depends(get_db)):
    try:
        # Your prompt logic here
        return {"message": "Prompts endpoint"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_prompt(db: Session = Depends(get_db)):
    try:
        # Your prompt creation logic here
        return {"message": "Prompt created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
