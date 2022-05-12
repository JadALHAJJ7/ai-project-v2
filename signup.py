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



import os
import pafy 
import vlc 
import time
import random
import re, requests, subprocess, urllib.parse, urllib.request

# Security
#passlib,hashlib,bcrypt,scrypt
import hashlib
def make_hashes(password):
	return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password,hashed_text):
	if make_hashes(password) == hashed_text:
		return hashed_text
	return False
# DB Management
import sqlite3 
conn = sqlite3.connect('data.db')
c = conn.cursor()
# DB  Functions
def create_usertable():
	c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT)')


def add_userdata(username,password):
	c.execute('INSERT INTO userstable(username,password) VALUES (?,?)',(username,password))
	conn.commit()

def login_user(username,password):
	c.execute('SELECT * FROM userstable WHERE username =? AND password = ?',(username,password))
	data = c.fetchall()
	return data


def view_all_users():
	c.execute('SELECT * FROM userstable')
	data = c.fetchall()
	return data



def main():
	"""Simple Login App"""

	st.title("Simple Login App")

	menu = ["Home","Login","SignUp"]
	choice = st.sidebar.selectbox("Menu",menu)

	if choice == "Home":
		st.subheader("Home")

	elif choice == "Login":
		st.subheader("Login Section")

		username = st.sidebar.text_input("User Name")
		password = st.sidebar.text_input("Password",type='password')
		if st.sidebar.checkbox("Login"):
			# if password == '12345':
			create_usertable()
			hashed_pswd = make_hashes(password)

			result = login_user(username,check_hashes(password,hashed_pswd))
			if result:

				st.success("Logged In as {}".format(username))

				task = st.selectbox("Task",["Profiles","Check your Emotions"])
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
							res = holis.process(cv2.cvtColor(frm, cv2.COLOR_BGR2RGB))
							lst = []
							if res.face_landmarks:
								for i in res.face_landmarks.landmark:
									lst.append(i.x - res.face_landmarks.landmark[1].x)
									lst.append(i.y - res.face_landmarks.landmark[1].y)
								if res.left_hand_landmarks:
									for i in res.left_hand_landmarks.landmark:
										lst.append(i.x - res.left_hand_landmarks.landmark[8].x)
										lst.append(i.y - res.left_hand_landmarks.landmark[8].y)
								else:
									for i in range(42):
										lst.append(0.0)
								if res.right_hand_landmarks:
									for i in res.right_hand_landmarks.landmark:
										lst.append(i.x - res.right_hand_landmarks.landmark[8].x)
										lst.append(i.y - res.right_hand_landmarks.landmark[8].y)
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
					like, dislike = st.columns([0.02,0.25])
					like.button("Like")
					dislike.button("Dislike")

					if lang and singer and st.session_state["run"] != "false":
						webrtc_streamer(key="key", desired_playing_state=True,
										video_processor_factory=EmotionProcessor)
					btn = st.button("Recommend me songs")
					print(emotion)
					if btn:
						if not(emotion):
							st.warning("Please let me capture your emotion first")
							st.session_state["run"] = "true"
							
						else:
							
							name=lang+"+"+emotion+"+"+"song"+"+"+singer
							query_string = urllib.parse.urlencode({"search_query":name })
							formatUrl = urllib.request.urlopen("https://www.youtube.com/results?" + query_string)
							search_results = re.findall(r"watch\?v=(\S{11})", formatUrl.read().decode())
							clip2 = "https://www.youtube.com/watch?v=" + "{}".format(search_results[0])
							video = pafy.new(clip2) 
							videolink =video.getbestaudio()  
							print("audio is playing")  
							media = vlc.MediaPlayer(videolink.url)  
							media.play()
							time.sleep(30)
							media.stop()

							# webbrowser.open(
							# 	f"https://music.youtube.com/search?q={lang}+{emotion}+song+{singer}")
							np.save("emotion.npy", np.array([""]))
							like.form_submit_button("Like",onclick=st.text("You like this song"),disable=False)
							dislike.form_submit_button("Dislike",onclick=st.text("You like this song"),disable=False)
						st.session_state["run"] = "false"
        


				elif task == "Profiles":
					st.subheader("User Profiles")
					user_result = view_all_users()
					clean_db = pd.DataFrame(user_result,columns=["Username","Password"])
					st.dataframe(clean_db)
			else:
				st.warning("Incorrect Username/Password")





	elif choice == "SignUp":
		st.subheader("Create New Account")
		new_user = st.text_input("Username")
		new_password = st.text_input("Password",type='password')

		if st.button("Signup"):
			create_usertable()
			add_userdata(new_user,make_hashes(new_password))
			st.success("You have successfully created a valid Account")
			st.info("Go to Login Menu to login")



if __name__ == '__main__':
	main()