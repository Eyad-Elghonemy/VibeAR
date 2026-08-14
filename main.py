from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from src.helpers.config import APP_NAME, VERSION, SECRET_KEY_TOKEN
from src.controlers.NLPTrainer import NLPTrainer
from src.models.request import TestingData, TrainingData, QueryText
from src.models.response import StatusObject, PredictionObject, PredictionObjects


# Intialize An App And Trainer
trainer = NLPTrainer()

app = FastAPI(title=APP_NAME, version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authorization
api_key_header = APIKeyHeader(name='X-API-Key')
async def verify_api_key(api_key: str=Depends(api_key_header)):
    
    if api_key != SECRET_KEY_TOKEN :
        raise HTTPException(status_code=403, detail='You are not authorized')
    
    return api_key


# Healthy
@app.get("/", tags=["Healthy"], description="Health Check")
async def home(api_key: str=Depends(verify_api_key)):
    
    return{
        'App_Name': APP_NAME,
        'Version': VERSION
    }
    
    
# Status
@app.get('/status', tags=['Status'])
async def get_status(api_key: str=Depends(verify_api_key)):
    
    status = trainer.get_status()
    return StatusObject(**status)


# Training
@app.post('/train', tags=['Training'], description='Train a new model')
async def train(training_data: TrainingData, api_key: str=Depends(verify_api_key)):
    try:
        trainer.train(texts=training_data.texts, labels=training_data.labels)
        status = trainer.get_status()
        return StatusObject(**status)
    
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    
    

# Switch back to the default (pre-trained) model after training a custom one
@app.post('/use-default-model', tags=['Training'], description='Switch back to the default pre-trained model')
async def use_default_model(api_key: str=Depends(verify_api_key)):
    
    try:
        trainer.use_default_model()
        status = trainer.get_status()
        return StatusObject(**status)
    
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


# Predict a single input
@app.post('/predict', tags=['Prediction'], description='Predict single input')
async def predict(query_text: QueryText, api_key: str=Depends(verify_api_key)):
    
    try:
        prediction = trainer.predict(texts=[query_text.text])[0]
        return PredictionObject(**prediction)

    except Exception as e:
        raise HTTPException(status_code=503, detail=(str(e)))
    
    

# Predict a batch of inputs
@app.post('/predict-batch', tags=['Prediction'], description='Predict a batch of sentences')
async def predict_batch(testing_data: TestingData, api_key: str=Depends(verify_api_key)):
    
    try:
        predictions = trainer.predict(texts=testing_data.texts)
        return PredictionObjects(predictions=predictions)

    except Exception as e:
        raise HTTPException(status_code=503, detail=(str(e)))