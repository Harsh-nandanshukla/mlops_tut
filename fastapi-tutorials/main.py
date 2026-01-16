from fastapi import FastAPI,Path,HTTPException, Query
from pydantic import BaseModel,Field,computed_field
from fastapi.responses import JSONResponse
from typing import Annotated,Literal,Optional
import json

class Patient(BaseModel):
    id: Annotated [str,Field(...,description='id of the patient',example='P001') ]
    name:Annotated[str,Field(...,description='ame of the patient',example='Harsh')]
    gender:Annotated[Literal['male','female','others'],Field(...,description='gender of the patient')]
    city:Annotated [str,Field(...,description='city whwere patient is living ',example='gurgaon') ]
    age: Annotated[int,Field(...,gt=0,lt=120,description='age of the patient')]
    height:Annotated[float,Field(...,gt=0,description='weight of the patient in kgs')]
    weight:Annotated[float,Field(...,gt=0,description='height of the patient in meters')]
    
    @computed_field
    @property
    def bmi(self)-> float:
        bmi=round(self.weight/(self.height**2),2)
        return bmi
    @computed_field
    @property
    def verdict(self)->str:
        if self.bmi<18.5:
            return 'Underweight'
        elif self.bmi<25:
            return 'Normal'
        elif self.bmi<30:
            return 'Normal'
        else : 
            return 'Obese'


class PatientUpdate(BaseModel):
    name:Annotated[Optional[str],Field(default=None)]
    gender:Annotated[Optional[Literal['male','female','others']],Field(default=None)]
    city:Annotated [Optional[str],Field(default=None) ]
    age: Annotated[Optional[int],Field(default=None,gt=0,)]
    height:Annotated[Optional[float],Field(default=None,gt=0)]
    weight:Annotated[Optional[float],Field(default=None,gt=0)]
    


app = FastAPI()# app is fastapi app

def load_data():
    with open('patients.json','r') as f:
        data=json.load(f)

    return data    
def save_data(data):
    with open('patients.json','w') as f:
        json.dump(data,f)

@app.get("/")# end point ke liye route/URL/path define krr rhe 
def hello(): # above endpoint ke liye function
    return {'message':'Patient managemnt system api'}
@app.get('/about')
def about():
    return {'message': "Fully functional api to manage patient's record"}

@app.get('/view')
def view():
    data=load_data()

    return data 
@app.get('/patient/{patient_id}')  
def view_patient(patient_id:str=Path(...,description='Id of the patient', examples='P001')):
    #load all the data
    data=load_data() 
    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404, detail='patient not found')# to get the HTTP Status Code
@app.get('/sort')
def sort_patients(sort_by:str=Query (...,description='Sort on the basis of height , weight and bmi'), order : str= Query ('asc',)):
    valid_fields=['height','weight','bmi']
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail='Invalid field selected ,select from {valid_fields}')
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail='Invalid order select between asc or desc')
    data=load_data()
    sort_order= True if order =='desc' else False
    sorted_data=sorted(data.values(),key=lambda x: x.get(sort_by,0),reverse=sort_order)

    return sorted_data



@app.post('/create')
def create_patient(patient:Patient):
    #load data
    # check if patient already exist 
    # if new opatient then we add into the db 
    data=load_data()

    if patient.id in data:
        raise HTTPException(status_code=400,detail='patient already exist')
    
    data[patient.id]=patient.model_dump(exclude=['id'])
    #save this dictionary into db in json format
    save_data(data)

    return JSONResponse(status_code=200,content={'message':'patient created successfully'})


@app.put('/edit/{patient_id}')
def update_patient(patient_id:str,patient_update:PatientUpdate):
    data=load_data()
    if patient_id not in data:
        return HTTPException(status_code=404,detail='patient not found')
    existing_patient_info=data[patient_id]
    updated_patient_info=patient_update.model_dump(exclude_unset=True)
    for key,value in updated_patient_info.items():
        existing_patient_info[key]=value 

    # now in this dictionary we have the update values of the socific field we wamnted along with un altered field but the fields like height and weight can alter bmi which is a computed field so whatw e do is thet we : 
    # dict(existing_patient_info)->pydantic object of class patient-so it gets bmi and other computed_field right->then conver it into dictionary agin then update finally in db (json file ) by->    data[patient_id]=existing_patient_info 
    
    # curently this dict don;t have id field in it we need thta to convert it into pydantic field 
    existing_patient_info['id']=patient_id
    patient_pydantic_object=Patient(**existing_patient_info)
    existing_patient_info=patient_pydantic_object.model_dump(exclude='id') 

    data[patient_id]=existing_patient_info
    save_data(data)
    return JSONResponse(status_code=200,content={'message':'pateint updated successfully'})

@app.delete('/delet/{patient_id}')
def delete(patient_id:str):
    data=load_data()
    if patient_id not in data:
        raise HTTPException(status_code=400,detail='patient does nit exist')
    del data[patient_id]
    save_data(data)
    return JSONResponse(status_code=200,content={'message':'patient deleted'})