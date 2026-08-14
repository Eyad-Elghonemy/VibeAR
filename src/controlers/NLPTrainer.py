import os
import json
import copy
from datetime import datetime
import joblib
from threading import Thread, get_ident
from src.helpers.config import STORAGE_FOLDER_PATH
from typing import List, Dict, Union
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline


class NLPTrainer:
    def __init__(self) -> None:
        
        self._storage_path = STORAGE_FOLDER_PATH
        if not os.path.exists(self._storage_path):
            os.makedirs(self._storage_path)
            
        self._status_path = os.path.join(self._storage_path, "model_status.json")
        self._model_path = os.path.join(self._storage_path, "model_pickle.joblib")
        
        ## ================= NEW: default (pre-trained) model =================
        ## This is a separate file from model_pickle.joblib, and it should never
        ## be overwritten. If the user trains their own model later, they can
        ## always switch back to this one.
        
        self._default_model_path = os.path.join(self._storage_path, "default_model_pickle.joblib")
        self._default_status_path = os.path.join(self._storage_path, "default_model_status.json")
        
        if os.path.exists(self._default_model_path):
            self._default_model = joblib.load(self._default_model_path)
        else:
            self._default_model = None
        
        if os.path.exists(self._default_status_path):
            with open(self._default_status_path) as f:
                self._default_status = json.load(f)
        else:
            self._default_status = None
        ## ======================================================================
        
        
        ## Check for status file
        if os.path.exists(self._status_path):
            with open(self._status_path) as f:
                self._model_status = json.load(f)
                
        else:
            
            self._model_status = {
                'status' : 'No Model Found',
                'timestamp': datetime.now().isoformat(),
                'classes': [],
                'evaluation': {}
            }
            
        ## check model file
        if os.path.exists(self._model_path):
            self._model = joblib.load(self._model_path)
            
        elif self._default_model is not None:
            ## No trained ("active") model exists yet, so start up using the
            ## default model instead (so the user doesn't have to train
            ## something first just to try the project).
            
            self._model = self._default_model
            if self._default_status is not None:
                ## deepcopy is important here: without it, self._model_status and
                ## self._default_status would point to the SAME dictionary in memory.
                ## Any change to one (e.g. train() calling self._update_status) would
                ## accidentally change the other too.
                
                self._model_status = copy.deepcopy(self._default_status)
            
        else:
            self._model = None
    

        self._running_threads = []
        self._pipeline = None


    def _update_status(self, status: str, classes: List[str] = [], evaluation: Dict = {}) -> None :
        
        self._model_status['status'] = status
        self._model_status['classes'] = classes
        self._model_status['evaluation'] = evaluation
        self._model_status['timestamp'] = datetime.now().isoformat()
        
        with open(self._status_path, 'w') as f:
            json.dump(self._model_status, f, indent=2)
            
            
    
    def _train_job(self, X_train: List[str], y_train: List[Union[str, int]], X_test: List[str], y_test: List[Union[str, int]]):
        
        self._pipeline.fit(X_train, y_train)
        report = classification_report(y_test, self._pipeline.predict(X_test), output_dict=True, zero_division=0)
        classes = self._pipeline.classes_.tolist()
        
        self._update_status('Model Ready', classes, report)
        
        joblib.dump(self._pipeline, self._model_path, compress=9)
        
        self._model = self._pipeline
        self._pipeline = None
        
        ## Remove Completed Thread
        thread_id = get_ident()
        for i, t in enumerate(self._running_threads):
            if t.ident == thread_id:
                self._running_threads.pop(i)
                break
            
    
    def train(self, texts: List[str], labels: List[Union[str, int]]) -> None: 
        
        ## Split & Train
        X_train, X_test, y_train, y_test = train_test_split(texts, labels)
        
        clf = LogisticRegression()
        vec = TfidfVectorizer(min_df=2, max_df=0.9, ngram_range=(1, 2))
        
        self._pipeline = make_pipeline(vec, clf)
        self._model = None
        self._update_status('Training')
        
        
        t = Thread(target=self._train_job, args=(X_train, y_train, X_test, y_test))
        self._running_threads.append(t)
        t.start()
        
        
        
    def predict(self, texts: List[str]) -> List[Dict]:
        
        response = []
        if self._model:
            probs = self._model.predict_proba(texts)
            for i, row in enumerate(probs):
                row_pred = {}
                row_pred['text'] = texts[i]
                row_pred['predictions'] = {cls: round(float(prob), 3) for cls, prob in zip(self._model_status['classes'], row)}
                response.append(row_pred)
                
        else:
            raise Exception("No Trained Model Was Found.")
        
        return response
    
    
    
    def use_default_model(self) -> None:
        ## ================= NEW: switch back to the default model =================
        ## This does NOT retrain or download anything. It just replaces the
        ## "active" model (self._model) with the default one, which was saved
        ## in a separate file that nothing else ever writes to.
        
        if self._default_model is None:
            raise Exception("No Default Model Was Found.")
        
        self._model = self._default_model
        
        if self._default_status is not None:
            ## Same reason as above: take an independent copy, not the same
            ## dict reference.
            self._model_status = copy.deepcopy(self._default_status)
        else:
            self._update_status('Model Ready')
        
        ## Save this new state to the normal active files, so if the server
        ## restarts later, it remembers it's on the default model (instead of
        ## loading whatever was last trained).
        
        joblib.dump(self._model, self._model_path, compress=9)
        with open(self._status_path, 'w') as f:
            json.dump(self._model_status, f, indent=2)
        ## ============================================================================
    
    
    
    def get_status(self) -> Dict:
        return self._model_status