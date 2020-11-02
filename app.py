import os,json
import numpy as np
import pandas as pd
from datetime import date
from flask import Flask, flash, request, redirect, url_for, session,jsonify
from flask_session import Session
from werkzeug.utils import secure_filename
from flask_cors import CORS, cross_origin


UPLOAD_FOLDER = 'uploads'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
SESSION_TYPE = "filesystem"
PERMANENT_SESSION_LIFETIME = 2000
app.config.update(SECRET_KEY=os.urandom(24))

app.config.from_object(__name__)
Session(app)

@app.route('/api/result', methods=['GET'])
def result():
    file = open('finaldata.json')
    data = json.load(file)
    return jsonify(data)

@app.route('/api/upload', methods=['GET','POST'])
def fileUpload():
    ext_type=['csv','xls','xlsx']
    target=os.path.join(UPLOAD_FOLDER,'end_folder')
    if not os.path.isdir(target):
        os.mkdir(target)
    file = request.files['file'] 
    if file.filename.split('.')[-1] in ext_type:
        filename = secure_filename(file.filename)
        destination="/".join([target, filename])
        file.save(destination)
        session['uploadFilePath']=destination
        path = os.path.join(destination)
        print(path)
        workfunction(path)
    else:
        wrongfilefunction()
    return jsonify({"Uploaded": "True"})

def workfunction(filename):
    file = pd.read_excel(filename)
    data = pd.DataFrame(file)
    result={}
    result['Noi']=int(data.count()[0])
    newData = data.dropna(axis=0)
    newData = newData[pd.to_datetime(data['Doc. Date'], errors='coerce') <= pd.to_datetime('today')]
    newData = newData[pd.to_datetime(data['Pstng Date'], errors='coerce') <= pd.to_datetime('today')]
    newData = newData[pd.to_datetime(data['Net due dt'], errors='coerce') >= pd.to_datetime(data['Pstng Date'])]
    vendordata = {k:v for k,v in zip(newData['Vendor Code'],newData['Vendor name'])}
    for i in newData.index:
        if newData['Vendor Code'][i] in vendordata:
            if newData['Vendor name'][i] != vendordata[newData['Vendor Code'][i]]:
                newData.drop([i])
    vendordata1 = {k:v for k,v in zip(newData['Vendor Code'],newData['Vendor name'])}
    vendordata2 = {k:v for k,v in zip(newData['Vendor name'],newData['Vendor Code'])}

    for i in newData.index:
        if newData['Vendor name'][i] != vendordata1[newData['Vendor Code'][i]]:
                newData.drop([i])

    for i in newData.index:
        if newData['Vendor Code'][i] != vendordata2[newData['Vendor name'][i]]:
                newData.drop([i])
    newData = newData.drop_duplicates(['Invoice Numbers'])
    result['Ts']=float(newData['Amt in loc.cur.'].sum())
    df = newData.drop_duplicates(subset='Vendor name', keep="first")
    result['Nu']=int(df['Vendor name'].count())
    result['I']=int(data.shape[0]-newData.shape[0])
    json_object = json.dumps(result, indent = 4) 
    with open("finaldata.json", "w") as outfile: 
        outfile.write(json_object)
    os.remove(filename)

def wrongfilefunction():
    json_object = json.dumps({}, indent = 4) 
    with open("finaldata.json", "w") as outfile: 
        outfile.write(json_object)

if __name__ == "__main__":
    with app.test_request_context("/"):
        session["key"] = os.urandom(24)
    app.run(debug=True,port=int(os.environ.get('PORT',5000)))
CORS(app, expose_headers='Authorization')
