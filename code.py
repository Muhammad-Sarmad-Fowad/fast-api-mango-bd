from fastapi import FastAPI, Form, HTTPException
from typing import Optional
from pymongo import MongoClient
from bson.objectid import ObjectId

app = FastAPI()

# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client["task_db"]
users_collection = db["users"]
tasks_collection = db["tasks"]

# ----------------------- User Signup/Login -----------------------

@app.post("/signup")
def signup(username: str = Form(...), password: str = Form(...)):
    if users_collection.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="User already exists")

    users_collection.insert_one({"username": username, "password": password})
    return {"message": "Signup successful!"}

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = users_collection.find_one({"username": username})
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Wrong username or password")
    return {"message": "Login successful!"}

# ----------------------- Task Management -----------------------

@app.post("/add-task")
def add_task(
    username: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    status: Optional[str] = Form("pending")
):
    if not users_collection.find_one({"username": username}):
        raise HTTPException(status_code=404, detail="User not found")

    new_task = {
        "username": username,
        "title": title,
        "description": description,
        "status": status
    }
    result = tasks_collection.insert_one(new_task)
    new_task["_id"] = str(result.inserted_id)
    return {"message": "Task added", "task": new_task}

@app.get("/tasks")
def get_tasks(username: str):
    user_tasks = list(tasks_collection.find({"username": username}))
    for task in user_tasks:
        task["_id"] = str(task["_id"])  # Convert ObjectId to str
    return {"tasks": user_tasks}

@app.put("/edit-task/{task_id}")
def edit_task(
    task_id: str,
    username: str = Form(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    status: Optional[str] = Form(None)
):
    task = tasks_collection.find_one({"_id": ObjectId(task_id), "username": username})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    updates = {}
    if title: updates["title"] = title
    if description: updates["description"] = description
    if status: updates["status"] = status

    tasks_collection.update_one({"_id": ObjectId(task_id)}, {"$set": updates})
    updated_task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    updated_task["_id"] = str(updated_task["_id"])
    return {"message": "Task updated", "task": updated_task}

@app.delete("/delete-task/{task_id}")
def delete_task(task_id: str, username: str = Form(...)):
    result = tasks_collection.delete_one({"_id": ObjectId(task_id), "username": username})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}
