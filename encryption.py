from Crypto import Random #for Encryption
from Crypto.Cipher import AES
import string
import win32api, win32con
import os

class Encryptor:
	def __init__(self, key):
		self.key = key

	def pad(self, s):
		return s + b"\0" * (AES.block_size - len(s) % AES.block_size)

	def encrypt(self, message, key, key_size=256):
		message = self.pad(message)
		iv = Random.new().read(AES.block_size)
		cipher = AES.new(key, AES.MODE_CBC, iv)
		return iv + cipher.encrypt(message)

	def encrypt_file(self, file_name, key=None):
		if(key == None):
			key = self.key
		key = self.key
		with open(file_name, 'rb') as fo:
			plaintext = fo.read()
		enc = self.encrypt(plaintext, key)
		with open(file_name + ".enc", 'wb') as fo:
			fo.write(enc)
		os.remove(file_name)
		win32api.SetFileAttributes(file_name + ".enc", win32con.FILE_ATTRIBUTE_HIDDEN)

	def decrypt(self, ciphertext, key):
		'''ciphertext = self.pad(ciphertext)'''
		iv = ciphertext[:AES.block_size]
		cipher = AES.new(key, AES.MODE_CBC, iv)
		plaintext = cipher.decrypt(ciphertext[AES.block_size:])
		return plaintext.rstrip(b"\0")

	def decrypt_file(self, file_name, key=None):
		if(key == None):
			key = self.key
		key = self.key
		with open(file_name, 'rb') as fo:
			ciphertext = fo.read()
		dec = self.decrypt(ciphertext, key)
		with open(file_name[:-4], 'wb') as fo:
			fo.write(dec)
		os.remove(file_name)
		win32api.SetFileAttributes(file_name[:-4], win32con.FILE_ATTRIBUTE_NORMAL)

	def getAllFiles(self):
		dir_path = os.path.dirname(os.path.realpath(__file__))
		dirs = []
		for dirName, subdirList, fileList in os.walk(dir_path):
			for fname in fileList:
				if (fname != 'script.py' and fname != 'data.txt.enc'):
					dirs.append(dirName + "\\" + fname)
		return dirs

	def encrypt_all_files(self):
		dirs = self.getAllFiles()
		for file_name in dirs:
			self.encrypt_file(file_name)

	def decrypt_all_files(self):
		dirs = self.getAllFiles()
		for file_name in dirs:
			self.decrypt_file(file_name)