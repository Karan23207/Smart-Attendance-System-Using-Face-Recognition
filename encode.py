import cv2
from flask import Flask
import face_recognition
import face_recognition_models
import pickle
import sqlite3
import numpy as np
import os
from database import already_marked, mark_db_attendance , insert_user
import time

filename = 'Storeface'
filepath = os.listdir(filename)
facelist = []
idlist = []
for path in filepath:
    facelist.append(cv2.imread(os.path.join(filename, path)))
    id = os.path.splitext(path)[0]
    idlist.append(id)
# print(idlist)

# encoding part of every stored image after registring
def findencodingfun(facelist):
    encodelist = []
    for img in facelist:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodelist.append(encode)

    return encodelist


encodelistknown = findencodingfun(facelist)
encodelistknownwithids = [encodelistknown, idlist]

file = open('encodefile.pkl', 'wb')
pickle.dump(encodelistknownwithids, file)
file.close()


def onlyregisterface(username, id):
    cam = cv2.VideoCapture(0)

    start_time = time.time()
    TIME_LIMIT = 20

    base_dir = os.getcwd()  # project root
    folder_path = os.path.join(base_dir, "Storeface")

    # create folder if not exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    while True:
        success, img = cam.read()

        if not success:
            break

            # ⏱️ Check time limit
        if time.time() - start_time > TIME_LIMIT:
            print("Time limit reached")
            break

        cv2.imshow("Camera", img)

        key = cv2.waitKey(1) & 0xFF

        imgSmall = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgSmall = cv2.cvtColor(imgSmall, cv2.COLOR_BGR2RGB)

        facecurrframe = face_recognition.face_locations(imgSmall)
        encodeunknowncurrframe = face_recognition.face_encodings(imgSmall, facecurrframe)

        for encodeface, faceloc in zip(encodeunknowncurrframe, facecurrframe):
            matches = face_recognition.compare_faces(encodelistknown, encodeface)
            facedis = face_recognition.face_distance(encodelistknown, encodeface)

            if len(encodelistknown) > 0:
                facedis = face_recognition.face_distance(encodelistknown, encodeface)
                min_dist = np.min(facedis)
                matchidx = np.argmin(facedis)

                # 🚫 Same face already registered
                if min_dist < 0.45:
                    if idlist[matchidx] == id:
                        print("Same user trying again")
                        cam.release()
                        cv2.destroyAllWindows()
                        return "same user"

                    else:
                        print("Face already exists with different ID")
                        cam.release()
                        cv2.destroyAllWindows()
                        return "duplicate face"


        if key == ord('s'):
            file_path = os.path.join(folder_path, f"{id}.png")
            cv2.imwrite(file_path, img)
            print("Saved at:", file_path)
            # ✅ INSERT INTO DATABASE
            try:
                insert_user(id, username)
            except sqlite3.IntegrityError:
                cam.release()
                cv2.destroyAllWindows()
                return "id_exists"  # optional case
            cam.release()
            cv2.destroyAllWindows()
            return "new"


        if key == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
    return "no match found"


### signin + fetch record(face) from databse to match  !!!
def mark_attendance():

    cam = cv2.VideoCapture(0)
    start_time = time.time()
    TIME_LIMIT = 20

    while True:
        success, img = cam.read()

        if not success:
            break

            # ⏱️ Check time limit
        if time.time() - start_time > TIME_LIMIT:
            cam.release()
            cv2.destroyAllWindows()
            return "not marked", None

        cv2.imshow("Camera", img)

        key = cv2.waitKey(1) & 0xFF

        imgSmall = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgSmall = cv2.cvtColor(imgSmall, cv2.COLOR_BGR2RGB)

        facecurrframe = face_recognition.face_locations(imgSmall)
        encodeunknowncurrframe = face_recognition.face_encodings(imgSmall, facecurrframe)

        found_match = False  # ✅ flag
        for encodeface, faceloc in zip(encodeunknowncurrframe, facecurrframe):
            matches = face_recognition.compare_faces(encodelistknown, encodeface)
            facedis = face_recognition.face_distance(encodelistknown, encodeface)

            matchidx = np.argmin(facedis)
            matched_id = idlist[matchidx]

            if facedis[matchidx] < 0.45:
                detected_id = idlist[matchidx]

                if already_marked(detected_id):
                    cam.release()
                    cv2.destroyAllWindows()
                    return "already_marked", detected_id

                # ✅ Insert attendance
                mark_db_attendance(detected_id)

                cam.release()
                cv2.destroyAllWindows()
                return "marked", detected_id

        if key == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
    return "not marked", None



