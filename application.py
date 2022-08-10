from flask import Flask, flash, request, redirect, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
from werkzeug.datastructures import ImmutableMultiDict
import shutil
import os
import io
from flask_cors import CORS

from helpers.geotag import set_latlng
from helpers.audit import seo_audit
from helpers.suggest import description

from dotenv import load_dotenv
load_dotenv()

application = Flask(__name__)
CORS(application)

application.secret_key = os.getenv("FLASK_KEY")
application.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# Get current path
path = os.getcwd()
# file Upload
UPLOAD_FOLDER = os.path.join(path, 'uploads')

# Make directory if uploads is not exists
if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed extension you can set your own
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg'])

# Check if the filetype is .JPG
def allowed_file(filename):
    valid = '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    print("{} is {}".format(filename,valid))
    return valid

# Front end to test POST route
@application.route('/')
def upload_form():
    return render_template('upload.html')

@application.route('/audit')
def audit_form():
    return render_template('audit.html')

@application.route('/suggest')
def suggest_form():
    return render_template('suggest.html')

@application.route('/suggest', methods=['POST'])
def suggest_idea():
    dictToReturn = {}
    try:
        if request.method == 'POST':
            if request.form.get("niche"):
                site = request.form.get("niche")
                dictToReturn = description(site)
                print(dictToReturn)
            else:
                input_json = request.get_json(force=True) 
                dictToReturn = description(input_json['niche'])
    except Exception as e:
        print(e)
    return jsonify(dictToReturn)

# Receives and processes POST request for site auditing
@application.route('/audit', methods=['POST'])
def audit():
    dictToReturn = {}
    try:
        if request.method == 'POST':
            if request.form.get("url"):
                site = request.form.get("url")
                dictToReturn = seo_audit(site)
                print(dictToReturn)
            else:
                input_json = request.get_json(force=True) 
                dictToReturn = seo_audit(input_json['url'])
    except Exception as e:
        print(e)
    return jsonify(dictToReturn)

# Handles image upload, adds geolocation meta data
@application.route('/geotag', methods=['GET', 'POST'])
def upload_file():
    file_paths = []
    if request.method == 'POST':
        file = request.files['image']
        name = file.filename.replace(' ', '')
        file_path = os.path.join(application.config['UPLOAD_FOLDER'], name)
        file.save(file_path)
        set_latlng(file_path, float(request.form['lat']), float(request.form['lng']))
        file_path = ''
        ext = '.jpg'
        if len(request.files) > 1: # If multiple files, zip it. Else, leave as JPG
            shutil.make_archive('geotagged', 'zip', application.config['UPLOAD_FOLDER'])
            file_path = "geotagged.zip"
            ext = '.zip'
        else:
            file_path = os.path.join(application.config['UPLOAD_FOLDER'], secure_filename(name))
        file_paths.append(file_path)
        # Store the new image in memory then delete the file.
        return_data = io.BytesIO()
        with open(file_path, 'rb') as fo:
            return_data.write(fo.read())
        return_data.seek(0)

        for p in file_paths:
            os.remove(p)
        
        # Serve the image in memory in response
        return send_file(return_data, mimetype='application/{}'.format(secure_filename(name),ext),
                        download_name='{}{}'.format('geotagged',ext))

# Start application on PORT 8000
if __name__ == "__main__":
    application.debug = True
    application.run(host='0.0.0.0', port=8000)
    # application.run(port=8000)