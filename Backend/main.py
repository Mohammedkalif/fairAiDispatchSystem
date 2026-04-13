from fastapi import FastAPI, HTTPException
from Backend.runPreprocesses import main as runPreprocessesMain
from Backend.agents.supervisorGraph import run_dispatch
import uvicorn
import json

app = FastAPI()

@app.post("/dispatch/{data_id}")
async def dispatch(data_id: int):
    try:
        runPreprocessesMain(data_id)
        
        data_path = f"data/jsonFiles{data_id}/"
        with open(f"{data_path}finalFeatures.json") as f:
            effort_vectors = json.load(f)
        with open(f"{data_path}driversdata.json") as f:
            driver_data = json.load(f)
        
        result = run_dispatch(effort_vectors, driver_data)
        return result
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Data not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)