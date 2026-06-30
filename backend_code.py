from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from query3 import query_section

app = FastAPI()

# Allow CORS for frontend-backend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/get-bail-status")
async def get_bail_status(request: Request):
    try:
        # Extract section from request body
        data = await request.json()
        ipc_section = data.get("charges", "").strip().upper()

        if not ipc_section.startswith("IPC_"):
            return JSONResponse(content={"error": "Invalid IPC section format. Must be IPC_XXX."}, status_code=400)

        # Query the IPC section
        response = query_section(ipc_section)
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
