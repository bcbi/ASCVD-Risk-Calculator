import os
import requests
from flask import Flask, request, render_template
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

FHIR_SERVER_BASE_URL = os.getenv("FHIR_SERVER_BASE_URL")
username = os.getenv("FHIR_USERNAME")
password = os.getenv("FHIR_PASSWORD")

def request_patient(patient_id, credentials):
    req = requests.get(FHIR_SERVER_BASE_URL + "/Patient/" + str(patient_id), auth=credentials)
    if req.status_code == 200:
        return req.json()
    else:
        return None

def request_observations(patient_id, credentials):
    req = requests.get(FHIR_SERVER_BASE_URL + f"/Observation?patient={patient_id}", auth=credentials)
    if req.status_code == 200:
        return req.json()
    else:
        return None

def extract_patient_data(patient, observations):
    data = {}
    data['age'] = 2024 - int(patient['birthDate'][:4])  # Simplified age calculation
    data['gender'] = patient['gender']
    data['race'] = 'unknown'  # Default value
    
    for entry in observations.get('entry', []):
        resource = entry['resource']
        code = resource['code']['coding'][0]['code']
        value = resource['valueQuantity']['value']
        
        if code == '2093-3':  # Total Cholesterol
            data['total_cholesterol'] = value
        elif code == '2085-9':  # HDL Cholesterol
            data['hdl_cholesterol'] = value
        elif code == '18262-6':  # LDL Cholesterol
            data['ldl_cholesterol'] = value
        elif code == '8480-6':  # Systolic Blood Pressure
            data['systolic_bp'] = value
        elif code == '8462-4':  # Diastolic Blood Pressure
            data['diastolic_bp'] = value

    return data

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    patient_data = {}
    credentials = (username, password)

    if request.method == 'POST':
        try:
            patient_id = request.form.get('patient_id')
            if patient_id:
                patient = request_patient(patient_id, credentials)
                observations = request_observations(patient_id, credentials)

                if patient and observations:
                    patient_data = extract_patient_data(patient, observations)
            
            age = request.form.get('age', type=int)
            gender = request.form.get('gender')
            race = request.form.get('race')
            systolic_bp = request.form.get('systolic_bp', type=int)
            diastolic_bp = request.form.get('diastolic_bp', type=int)
            total_cholesterol = request.form.get('total_cholesterol', type=int)
            hdl_cholesterol = request.form.get('hdl_cholesterol', type=int)
            ldl_cholesterol = request.form.get('ldl_cholesterol', type=int)
            diabetes = request.form.get('diabetes') == 'yes'
            smoker = request.form.get('smoker') == 'yes'
            on_bp_meds = request.form.get('on_bp_meds') == 'yes'
            on_statin = request.form.get('on_statin') == 'yes'
            on_aspirin = request.form.get('on_aspirin') == 'yes'
            refine_risk = request.form.get('refine_risk') == 'yes'
            
            # Use the fetched data if available, otherwise use user input
            age = patient_data.get('age', age)
            gender = patient_data.get('gender', gender)
            race = patient_data.get('race', race)
            systolic_bp = patient_data.get('systolic_bp', systolic_bp)
            diastolic_bp = patient_data.get('diastolic_bp', diastolic_bp)
            total_cholesterol = patient_data.get('total_cholesterol', total_cholesterol)
            hdl_cholesterol = patient_data.get('hdl_cholesterol', hdl_cholesterol)
            ldl_cholesterol = patient_data.get('ldl_cholesterol', ldl_cholesterol)
            
            if None in [age, gender, race, systolic_bp, diastolic_bp, total_cholesterol, hdl_cholesterol, ldl_cholesterol]:
                result = 'Incomplete input. Please enter all required fields.'
            else:
                risk_score = calculate_ascvd_risk(
                    age, gender, race, systolic_bp, diastolic_bp, total_cholesterol, hdl_cholesterol, ldl_cholesterol,
                    diabetes, smoker, on_bp_meds, on_statin, on_aspirin, refine_risk
                )
                result = f"Estimated 10-year ASCVD Risk: {risk_score:.2f}%"
        except ValueError:
            result = 'Invalid input. Please enter valid values for all fields.'

    return render_template('index.html', result=result, patient_data=patient_data)

def calculate_ascvd_risk(age, gender, race, systolic_bp, diastolic_bp, total_cholesterol, hdl_cholesterol, ldl_cholesterol,
                         diabetes, smoker, on_bp_meds, on_statin, on_aspirin, refine_risk):
    # Simplified calculation for demonstration purposes
    risk_score = (age * 0.1 + total_cholesterol * 0.2 + hdl_cholesterol * -0.1 +
                  systolic_bp * 0.2 + diastolic_bp * 0.1 +
                  (10 if on_bp_meds else 0) + (10 if on_statin else 0) + (5 if on_aspirin else 0) +
                  (20 if smoker else 0) + (30 if diabetes else 0))
    if refine_risk:
        risk_score *= 0.9  # Example refinement factor
    return risk_score

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, port=port)
