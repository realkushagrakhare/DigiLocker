from flask import *
import face_recognition
import cv2
import os
import base64
from Crypto import Random
import time
import string
from werkzeug.utils import secure_filename
from encryption import Encryptor
import win32api, win32con

app = Flask(__name__)

master_key = b'[EX\xc8\xd5\xbfI{\xa2$\x05(\xd5\x18\xbf\xc0\x85)\x10nc\x94\x02)j\xdf\xcb\xc4\x94\x9d(\x9e'
enc = Encryptor(master_key)

files = []
known_face_encodings = []
known_face_names = []
known_face_keys = []

current_face_encodings = [0]

@app.route('/')
def index(name=None):
    return render_template('home.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        print("Current New User:", request.form['userID'])
        if(request.form['userID'] in known_face_names):
            return jsonify(status='4')
        str=request.form['file'][23:]
        imgdata = base64.b64decode(str)
        filename = 'check.jpeg'
        with open(filename, 'wb') as f:
            f.write(imgdata)
        status = backend_signup(request.form['userID'], 'check.jpeg')
        return jsonify(status=status)
    return render_template('signup.html')
	
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        str=request.form['file'][23:]
        imgdata = base64.b64decode(str)
        filename = 'check.jpeg'
        with open(filename, 'wb') as f:
            f.write(imgdata)
        res = backend_login('check.jpeg')
        if(res == None):
            return jsonify(status='1')
        if(not os.path.exists('static/'+res[0])):
            os.mkdir('static/'+res[0])
        return jsonify(status='0', user=res[0], key=res[1])
    return render_template('login.html')
    
@app.route('/getAllFiles', methods=['GET','POST'])
def get_all_files():
    if request.method == 'POST':
        userpath =  'static/'+request.form['user']+'/'
        files = []
        for (_,_,f) in os.walk(userpath):
            for file in f:
                files.append(file[:-4])
        return jsonify(status='0', files=files)
    return render_template('usersite.html', files=[])
    
@app.route('/download', methods=['POST'])
def download():
    f=request.form['fname']+".enc"
    print(f)
    return send_from_directory(directory=os.getcwd()+'\\static\\'+request.form['user'], filename=f)
   
@app.route('/upload', methods=['POST'])  
def upload():  
    print('Uploading user:', request.form['user'])
    print(request.files)
    f = request.files['file']
    userpath = 'static/'+request.form['user']+'/'
    f.save(userpath+secure_filename(f.filename))
    print(len(request.form['key']))
    enc.encrypt_file(userpath+f.filename, request.form['key'])
    return jsonify(status='0')

@app.route('/delete', methods=['POST'])	
def delete():
    print('Deleting user:', request.form['user'])
    f=request.form['fname']
    print("Deleting ", f)
    userpath = 'static/'+request.form['user']+'/'
    os.remove(userpath+f+".enc")
    return jsonify(status='0')

@app.route('/encrypt', methods=['POST'])
def encrypt():
    f=request.form['fname']
    userpath = 'static/'+request.form['user']+'/'
    enc.encrypt_file(userpath+f, request.form['key'])
    return jsonify(status='0')

@app.route('/decrypt', methods=['POST'])
def decrypt():
    f=request.form['fname']
    userpath = 'static/'+request.form['user']+'/'
    enc.decrypt_file(userpath+f+".enc", request.form['key'])
    return jsonify(status='0')

def contains_whitespace(str):
    for i in str:
        if i in string.whitespace:
            return True
    return False

def create_random_key():
	temp_key = Random.get_random_bytes(32).decode('cp437')
	if(contains_whitespace(temp_key)):
		return create_random_key()
	else:
		return temp_key

def reload_face_information():
	known_face_names.clear()
	known_face_encodings.clear()
	known_face_keys.clear()
	load_face_information()

def load_face_information():
	if os.path.isfile('data.txt'):
		lines = ''
		with open("data.txt", "r", encoding="cp437") as f:
			lines = f.read().splitlines()
			#print("Users signed up: ", lines[::3])
		for i in range(int(len(lines)/3)):
			known_face_names.append(lines[i*3])
			temp_face_image = face_recognition.load_image_file(lines[i*3 + 1])
			known_face_encodings.append(face_recognition.face_encodings(temp_face_image, num_jitters=100)[0])
			known_face_keys.append(lines[i*3 + 2])
	print("Users signed up:", known_face_names)
			
def save_face_information(new_face_name, new_face_image_filename, new_face_image_encoding):
	with open("data.txt", "a", encoding="cp437") as f:
		f.write(new_face_name + "\n")
		f.write(new_face_image_filename + "\n")
		new_face_key = create_random_key()
		f.write(new_face_key + "\n")
		append_face_information(new_face_name, new_face_image_encoding, new_face_key)
		
def append_face_information(new_face_name, new_face_image_encoding, new_face_key):
	known_face_names.append(new_face_name)
	known_face_encodings.append(new_face_image_encoding)
	known_face_keys.append(new_face_key)

def backend_signup(new_face_name, image_path):
	new_face_image_path = image_path
	new_face_image_status = take_exisitng_photo(new_face_image_path, new_face_name)
	if(new_face_image_status == 1 or new_face_image_status == 2 or new_face_image_status == 3):
		return new_face_image_status
	print('Setting up account. Please wait.')
	new_face_image_filename = new_face_image_status
	new_face_image_encoding = current_face_encodings[0]
	save_face_information(new_face_name, new_face_image_filename, new_face_image_encoding)
	print('Account ready. Trying login now.')
	return 0
	
def take_exisitng_photo(image_path, image_name):
	image = cv2.imread(image_path)
	
	small_frame = image #Not resizing anymore cv2.resize(image, (0, 0), fx=0.25, fy=0.25)
	rgb_small_frame = small_frame[:, :, ::-1]
	face_locations = face_recognition.face_locations(rgb_small_frame)
	face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
	#print(face_encodings)
	
	if(len(face_encodings) == 0):
		print('Unable to detect face. Try another image.')
		return 2
	
	for face_encoding in face_encodings:
		# See if the face is a match for the known face(s)
		matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
		
		# If a match was found in known_face_encodings, then account exists.
		if True in matches:
			print("Account already exists. Try logging in.")
			return 1
	
	if(image_name in known_face_names):
		print("Account name already exists. Try logging in.")
		return 3
	
	cv2.imwrite(image_name + ".jpg", image)
	current_face_encodings[0] = face_encodings[0]
	win32api.SetFileAttributes(image_name + ".jpg", win32con.FILE_ATTRIBUTE_HIDDEN)
	return image_name + ".jpg"

def backend_login(image_path):
	name = None
	key = None
	match_index = None
	logged_in = False
	timeout = time.time() + 15   # 15 seconds from now

	frame = cv2.imread(image_path)
	small_frame = frame #Not resizing at this moment #cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
	# Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
	rgb_small_frame = small_frame[:, :, ::-1]
	
	# Find all the faces and face encodings in the current frame of video
	face_locations = face_recognition.face_locations(rgb_small_frame)
	face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

	for face_encoding in face_encodings:
		# See if the face is a match for the known face(s)
		matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
		# If a match was found in known_face_encodings, just use the first one.
		if True in matches:
			match_index = matches.index(True)
			name = known_face_names[match_index]
			key = known_face_keys[match_index]
			print("Login successful for  " + name)
			logged_in = True
			return (name, key)
	
		if(time.time() > timeout):
			print('Timeout.')
			return None
	return None


if __name__ == '__main__':
    reload_face_information()
    app.config['UPLOAD_FOLDER'] = 'abc'
    app.run()
    app.debug = True
    