from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.agent.routes import router as agent_router

app = FastAPI(
    title="AgentX API",
    description="智能体管理 API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "AgentX API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
