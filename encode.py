import cv2
import face_recognition
import pickle
import sqlite3
import numpy as np
import os
import time
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from database import already_marked, mark_db_attendance, insert_user

load_dotenv()  # Loads variables from .env


class FaceRecognitionSystem:
    def __init__(self):
        """Encapsulates the core configuration, encryption, and state."""
        self.encryption_key = os.getenv("ENCRYPTION_KEY")
        if not self.encryption_key:
            raise ValueError("CRITICAL ERROR: ENCRYPTION_KEY not found in environment variables!")

        self.cipher_suite = Fernet(self.encryption_key.encode())

        self.folder_path = 'Storeface'
        self.encode_file_path = 'encodefile.pkl'

        self.encodelistknown = []
        self.idlist = []

        # Automatically load or build encodings on initialization
        self._initialize_encodings()

    def _initialize_encodings(self):
        """Abstraction: Hides the complex loading, decryption, and fallback logic from the caller."""
        if os.path.exists(self.encode_file_path):
            try:
                with open(self.encode_file_path, 'rb') as file:
                    encrypted_data = file.read()

                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                self.encodelistknown, self.idlist = pickle.loads(decrypted_data)
                print("Successfully loaded and decrypted known face encodings from cache.")
                return
            except Exception as e:
                print(f"Error decrypting cache: {e}. Falling back to image folder.")

        # Fallback: Build from folder images if cache doesn't exist or failed
        if os.path.exists(self.folder_path):
            filepath = os.listdir(self.folder_path)
        else:
            filepath = []

        facelist = []
        for path in filepath:
            img_path = os.path.join(self.folder_path, path)
            img = cv2.imread(img_path)
            if img is not None:
                facelist.append(img)
                self.idlist.append(os.path.splitext(path)[0])

        self.encodelistknown = self._generate_encodings(facelist)

        # Encrypt and save cache
        data_to_save = [self.encodelistknown, self.idlist]
        serialized_data = pickle.dumps(data_to_save)
        encrypted_data = self.cipher_suite.encrypt(serialized_data)
        with open(self.encode_file_path, 'wb') as file:
            file.write(encrypted_data)

    def _generate_encodings(self, facelist):
        """Private helper method for vector extraction."""
        encodelist = []
        valid_ids = []

        for img, user_id in zip(facelist, self.idlist):
            if img is None:
                continue
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(img)

            if len(encodings) > 0:
                encodelist.append(encodings[0])
                valid_ids.append(user_id)

        self.idlist = valid_ids
        return encodelist

    def only_register_face(self, username, user_id):
        """Public method to handle user registration securely."""
        cam = cv2.VideoCapture(0)
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        start_time = time.time()
        TIME_LIMIT = 20

        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)

        frame_count = 0

        while True:
            success, img = cam.read()
            if not success:
                break

            if time.time() - start_time > TIME_LIMIT:
                break

            cv2.imshow("Camera", img)
            key = cv2.waitKey(1) & 0xFF

            frame_count += 1
            if frame_count % 3 == 0:  # Performance optimization
                imgSmall = cv2.resize(img, (0, 0), None, 0.25, 0.25)
                imgSmall = cv2.cvtColor(imgSmall, cv2.COLOR_BGR2RGB)

                facecurrframe = face_recognition.face_locations(imgSmall)
                encodeunknowncurrframe = face_recognition.face_encodings(imgSmall, facecurrframe)

                for encodeface in encodeunknowncurrframe:
                    if len(self.encodelistknown) > 0:
                        facedis = face_recognition.face_distance(self.encodelistknown, encodeface)
                        min_dist = np.min(facedis)
                        matchidx = np.argmin(facedis)

                        if min_dist < 0.50:
                            cam.release()
                            cv2.destroyAllWindows()
                            if self.idlist[matchidx] == user_id:
                                return "same user"
                            else:
                                return "duplicate face"

            if key == ord('s'):
                file_path = os.path.join(self.folder_path, f"{user_id}.png")
                cv2.imwrite(file_path, img)
                try:
                    insert_user(user_id, username)
                except sqlite3.IntegrityError:
                    cam.release()
                    cv2.destroyAllWindows()
                    return "id_exists"

                cam.release()
                cv2.destroyAllWindows()
                return "new"

            if key == ord('q'):
                break

        cam.release()
        cv2.destroyAllWindows()
        return "no match found"

    def mark_attendance(self):
        """Public method to handle attendance verification."""
        cam = cv2.VideoCapture(0)
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        start_time = time.time()
        TIME_LIMIT = 20
        frame_count = 0

        while True:
            success, img = cam.read()
            if not success:
                break

            if time.time() - start_time > TIME_LIMIT:
                cam.release()
                cv2.destroyAllWindows()
                return "not marked", None

            cv2.imshow("Camera", img)
            key = cv2.waitKey(1) & 0xFF

            frame_count += 1
            if frame_count % 3 == 0:
                imgSmall = cv2.resize(img, (0, 0), None, 0.25, 0.25)
                imgSmall = cv2.cvtColor(imgSmall, cv2.COLOR_BGR2RGB)

                facecurrframe = face_recognition.face_locations(imgSmall)
                encodeunknowncurrframe = face_recognition.face_encodings(imgSmall, facecurrframe)

                for encodeface in encodeunknowncurrframe:
                    if len(self.encodelistknown) > 0:
                        facedis = face_recognition.face_distance(self.encodelistknown, encodeface)
                        matchidx = np.argmin(facedis)

                        if facedis[matchidx] < 0.50:
                            detected_id = self.idlist[matchidx]
                            cam.release()
                            cv2.destroyAllWindows()

                            if already_marked(detected_id):
                                return "already_marked", detected_id

                            mark_db_attendance(detected_id)
                            return "marked", detected_id

            if key == ord('q'):
                break

        cam.release()
        cv2.destroyAllWindows()
        return "not marked", None
