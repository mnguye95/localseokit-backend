from msilib.schema import Error
import os
import io
from pkgutil import extend_path
from helpers.geotag import set_latlng
from flask import Flask, flash, request, redirect, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
import shutil
from seoanalyzer import analyze
from flask_cors import CORS

application = Flask(__name__)
CORS(application)

application.secret_key = 'some key for now'
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

# Format seo audit report
def seo_report(output):
    page = output['pages'][0]
    details = {}
    warnings = {}
    for warning in page['warnings']:
        tokenized = [w.strip() for w in warning.split(':', 1)]
        if tokenized[0] in warnings:
            warnings[tokenized[0]]['count'] += 1
            warnings[tokenized[0]]['result'].append(tokenized[1])
        else:
            if len(tokenized) > 1:
                warnings[tokenized[0]] = {}
                warnings[tokenized[0]]['count'] = 1
                warnings[tokenized[0]]['result'] = []
                warnings[tokenized[0]]['result'].append(tokenized[1])
            else:
                warnings[tokenized[0]] = {}
                warnings[tokenized[0]]['count'] = 1
                warnings[tokenized[0]]['result'] = []

    details['url'] = page['url']
    details['title'] = page['title']
    details['description'] = page['description']
    details['word_count'] = page['word_count']
    details['error_count'] = len(page['warnings'])
    details['keywords'] = page['keywords'][:10]
    details['warnings'] = warnings

    return details

# Front end to test POST route
@application.route('/')
def upload_form():
    return render_template('upload.html')

@application.route('/audit')
def audit_form():
    return render_template('audit.html')

# Receives and processes POST request for site auditing
@application.route('/audit', methods=['POST'])
def audit():
    dictToReturn = {}
    try:
        if request.method == 'POST':
            if request.form.get("url"):
                site = request.form.get("url")
                output = analyze(site, follow_links=False)
                dictToReturn = seo_report(output)
                print(output)
            else:
                input_json = request.get_json(force=True) 
                output = analyze(input_json['url'], follow_links=False)
                dictToReturn = seo_report(output)
    except Error:
        print(Error)
    return jsonify(dictToReturn)

# Handles image upload, adds geolocation meta data
@application.route('/', methods=['POST'])
def upload_file():
    if request.method == 'POST':

        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)

        files = request.files.getlist('files[]')
        city = request.form.get("city")
        file_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(application.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                file_paths.append(file_path)
                set_latlng(file_path, city)
                flash('{} successfully uploaded'.format(file.filename))
            else:
                flash('{} is not allowed.'.format(file.filename.rsplit('.', 1)[1].lower()))
        

        file_path = ''
        ext = '.jpg'
        if len(files) > 1: # If multiple files, zip it. Else, leave as JPG
            shutil.make_archive('geotagged', 'zip', application.config['UPLOAD_FOLDER'])
            file_path = "geotagged.zip"
            ext = '.zip'
        else:
            file_path = os.path.join(application.config['UPLOAD_FOLDER'], secure_filename(files[0].filename))
        
        # Store the new image in memory then delete the file.
        return_data = io.BytesIO()
        with open(file_path, 'rb') as fo:
            return_data.write(fo.read())
        return_data.seek(0)

        for p in file_paths:
            os.remove(p)
        
        # Serve the image in memory in response
        return send_file(return_data, mimetype='application/{}'.format(secure_filename(files[0].filename),ext),
                        download_name='{}{}'.format('geotagged',ext))

# Start application on PORT 8000
if __name__ == "__main__":
    application.debug = True
    application.run(port=8000)