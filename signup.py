import sqlite3
from pickle import FALSE
import streamlit as st
import pandas as pd
import streamlit as st
from streamlit_webrtc import webrtc_streamer
import av
import cv2
import numpy as np
import mediapipe as mp
from keras.models import load_model
import webbrowser
from IPython.display import HTML
from PIL import Image
import pytube
import os
import pafy
import vlc
import time
import random
import re
import requests
import subprocess
import urllib.parse
import urllib.request

# Security
# passlib,hashlib,bcrypt,scrypt
import hashlib
import keyboard

st.set_page_config(page_icon="🎶",page_title="Jingy Bingy")

def make_clickable(val):
    return '<a href="{}">{}</a>'.format(val,val)

def make_hashes(password):
	return hashlib.sha256(str.encode(password)).hexdigest()


def check_hashes(password, hashed_text):
	if make_hashes(password) == hashed_text:
		return hashed_text
	return False


# DB Management
conn = sqlite3.connect('data.db')
c = conn.cursor()
# DB  Functions


def create_usertable():
	c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT)')

def create_userstatisticstable():
    	c.execute('CREATE TABLE IF NOT EXISTS usersstatisticstable(username TEXT,emotion TEXT,song TEXT,link TEXT,val Text)')


def add_userval(username,emotion,song,link,val):
		c.execute('INSERT INTO usersstatisticstable(username,emotion,song,link,val) VALUES (?,?,?,?,?)',(username,emotion,song,link,val))
		conn.commit()

def add_userdata(username, password):
	c.execute('INSERT INTO userstable(username,password) VALUES (?,?)',
			  (username, password))
	conn.commit()


def login_user(username, password):
	c.execute('SELECT * FROM userstable WHERE username =? AND password = ?',
			  (username, password))
	data = c.fetchall()
	return data


def view_all_users():
	c.execute('SELECT * FROM userstable')
	data = c.fetchall()
	return data

def view_user_val(username):
	c.execute('SELECT * FROM usersstatisticstable where username = ?',(username,))
	dataval = c.fetchall()
	return dataval

def view_user_link(username):
		c.execute('SELECT link FROM usersstatisticstable where username = ?',(username,))
		dataval = c.fetchall()
		return dataval

def main():
	
	"""Welcome to Jingy Bingy"""

	st.title("Welcome to Jingy Bingy")

	menu = ["Home", "Login", "SignUp"]
	choice = st.sidebar.selectbox("Menu", menu)

	if choice == "Home":
    		
		image = Image.open('emotion.jpg')
		st.image(image)
		st.subheader("Home")

	elif choice == "Login":
		st.subheader("Login Section")

		username = st.sidebar.text_input("User Name")
		password = st.sidebar.text_input("Password", type='password')
		if st.sidebar.checkbox("Login"):
			# if password == '12345':
			create_usertable()
			create_userstatisticstable()
			#c.execute('DROP TABLE usersstatisticstable;')
			hashed_pswd = make_hashes(password)

			result = login_user(username, check_hashes(password, hashed_pswd))
			if result:

				st.success("Logged In as {}".format(username))

				task = st.selectbox(
					"Task", ["Profiles", "Check your Emotions","Statistics"])
				if task == "Check your Emotions":
					model = load_model("model.h5")
					label = np.load("labels.npy")
					holistic = mp.solutions.holistic
					hands = mp.solutions.hands
					holis = holistic.Holistic()
					drawing = mp.solutions.drawing_utils
					st.header("Emotion Based Music Recommender")
					if "run" not in st.session_state:
						st.session_state["run"] = "true"
					try:
						emotion = np.load("emotion.npy")[0]
						np.save("emotion.npy", np.array([""]))
					except:
						emotion = ""
					if not(emotion):
						st.session_state["run"] = "true"
					else:
						st.session_state["run"] = "false"

					class EmotionProcessor:
						def recv(self, frame):
							frm = frame.to_ndarray(format="bgr24")
							##############################

							frm = cv2.flip(frm, 1)
							res = holis.process(
								cv2.cvtColor(frm, cv2.COLOR_BGR2RGB))
							lst = []
							if res.face_landmarks:
								for i in res.face_landmarks.landmark:
									lst.append(
										i.x - res.face_landmarks.landmark[1].x)
									lst.append(
										i.y - res.face_landmarks.landmark[1].y)
								if res.left_hand_landmarks:
									for i in res.left_hand_landmarks.landmark:
										lst.append(
											i.x - res.left_hand_landmarks.landmark[8].x)
										lst.append(
											i.y - res.left_hand_landmarks.landmark[8].y)
								else:
									for i in range(42):
										lst.append(0.0)
								if res.right_hand_landmarks:
									for i in res.right_hand_landmarks.landmark:
										lst.append(
											i.x - res.right_hand_landmarks.landmark[8].x)
										lst.append(
											i.y - res.right_hand_landmarks.landmark[8].y)
								else:
									for i in range(42):
										lst.append(0.0)
								lst = np.array(lst).reshape(1, -1)
								pred = label[np.argmax(model.predict(lst))]
								print(pred)
								cv2.putText(frm, pred, (50, 50),
											cv2.FONT_ITALIC, 1, (255, 0, 0), 2)
								np.save("emotion.npy", np.array([pred]))
							drawing.draw_landmarks(frm, res.face_landmarks, holistic.FACEMESH_TESSELATION,
												   landmark_drawing_spec=drawing.DrawingSpec(
													   color=(0, 0, 255), thickness=-1, circle_radius=1),
												   connection_drawing_spec=drawing.DrawingSpec(thickness=1))
							drawing.draw_landmarks(
								frm, res.left_hand_landmarks, hands.HAND_CONNECTIONS)
							drawing.draw_landmarks(
								frm, res.right_hand_landmarks, hands.HAND_CONNECTIONS)
							##############################
							return av.VideoFrame.from_ndarray(frm, format="bgr24")

					lang = st.text_input("Language")
					singer = st.text_input("Singer")
					st.text("Don't forget to come back and like/dislike the song")
					st.text("Use ,up arrow, down arrow, left arrow, right arrow to play, stop, next, previous song")
					st.text("Use l, d, esc, to like, dislike, exite the song")

					if lang and singer and st.session_state["run"] != "false":
						webrtc_streamer(key="key", desired_playing_state=True,
										video_processor_factory=EmotionProcessor)
					btn = st.button("Recommend me songs")
					print(emotion)
				
					if btn:
						
						if not(emotion):
							st.warning(
								"Please let me capture your emotion first")
							st.session_state["run"] = "true"

						else:
							is_playing = False

							name = lang+"+"+emotion+"+"+"song"+"+"+singer
							query_string = urllib.parse.urlencode(
								{"search_query": name})
							formatUrl = urllib.request.urlopen(
								"https://www.youtube.com/results?" + query_string)
							search_results = re.findall(
								r"watch\?v=(\S{11})", formatUrl.read().decode())
							search_results = search_results[:10]
							clips = []
							clips_titles = []
							clips_redirection=[]
							for search_result in search_results:
								path = "https://www.youtube.com/watch?v=" + \
									"{}".format(search_result)
								clips_redirection.append(path)
								video = pafy.new(path)
								video_link = video.getbestaudio()
								clips_titles.append(video.title)
								if video_link:
									clips.append(video_link.url)

							vlc_instance = vlc.Instance()
							player = vlc_instance.media_list_player_new()
							player.play()
							Media = vlc_instance.media_list_new(clips)
							player.set_media_list(Media)
							player.play_item_at_index(0)
							print('video title :'+ video.title)
							print('*******************************************')
							print(clips)
							print('*******************************************')
							print('*******************************************')
							print(clips_titles)
							print('*******************************************')
							count=0
							while True:
								time.sleep(0.25)
								k = keyboard.read_key()
								if k == "right":  # Next
									count=count+1
									player.next()
								elif k == "left":  # Previous
									count=count-1
									player.previous()
								elif k == "l":  # Like
									add_userval(username,emotion,clips_titles[count],clips_redirection[count],"Like")
								elif k == "d":  # Dislike
									add_userval(username,emotion,clips_titles[count],clips_redirection[count],"Dislike")
								elif k == "up": 
									player.play() 
								elif k == "down":
									player.pause()
								elif k == "esc":  # Quit
									player.stop()
									break
								else:
									continue

							np.save("emotion.npy", np.array([""]))
						st.session_state["run"] = "false"

				elif task == "Profiles":
					st.subheader("User Profiles")
					user_result = view_all_users()
					clean_db = pd.DataFrame(user_result, columns = [
						"Username", "Password"])
					st.dataframe(clean_db)
				
				elif task == "Statistics":
					col1,col2 = st.columns([3,1])
					with col1:
						st.subheader("User Statistics")
						user_statistics = view_user_val(username)
						clean_db = pd.DataFrame(user_statistics, columns = [
							"Username","Emotion", "Song", "URL","Value"])
						#clean_db.style.format({'Song' : make_clickable})
						st.dataframe(clean_db)
						#print(clean_db)
					with col2:
						st.subheader("Songs Links")
					
						#user_songs = view_user_song(username)
						count_button=0
						for row in view_user_link(username):
							#link = '[Play](row)'
							#reduced_string = re.sub(r'.', '', str(row), count = 24)
							##link='<a href="'+str(row)+'"> Play </a>'
							##st.markdown(link, unsafe_allow_html=True)
							if st.button('Play Song '+str(count_button),key=count_button):
								print(str(row))
								reduced_string = re.sub(r'.', '', str(row), count = 2)
								print(reduced_string)
								webbrowser.get('C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s').open(reduced_string)
							count_button=count_button+1	

						# for i in range(0,len(user_songs)):
						# 	link = '[Play](user_songs)'
						# 	st.markdown(link, unsafe_allow_html=True)
			else:
				st.warning("Incorrect Username/Password")

	elif choice == "SignUp":
		st.subheader("Create New Account")
		new_user = st.text_input("Username")
		new_password = st.text_input("Password", type= 'password')

		if st.button("Signup"):
			create_usertable()
			add_userdata(new_user, make_hashes(new_password))
			st.success("You have successfully created a valid Account")
			st.info("Go to Login Menu to login")


if __name__ == '__main__':
	main()
