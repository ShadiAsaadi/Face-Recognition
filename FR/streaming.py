import os
import time
import numpy as np
import pandas as pd
import cv2
import shutil
from deepface import DeepFace
import random
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance
from deepface.models.FacialRecognition import FacialRecognition
from deepface.commons.logger import Logger
# from dbcsv import save_csv
logger = Logger(module="commons.realtime")

# dependency configuration
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# pylint: disable=too-many-nested-blocks

models = [
  "VGG-Face", 
  "Facenet", 
  "Facenet512", 
  "OpenFace", 
  "DeepFace", 
  "DeepID", 
  "ArcFace", 
  "Dlib", 
  "SFace",
  "GhostFaceNet",
]
backends = [
  'oepencv', 
  'ssd', 
  'dlib', 
  'mtcnn', 
  'fastmtcnn',
  'retinaface', 
  'mediapipe',
  'yolov8',
  'yunet',
  'centerface',
]
def analysis(
    db_path,
    model_name=models[2],
    detector_backend=backends[0],
    distance_metric="cosine",
    enable_face_analysis=False,
    source=0,
    time_threshold=0,
    frame_threshold=0,
):
    # global variables
    text_color = (255, 255, 255)
    check_del= False
    check_save = False
    pivot_img_size = 112  # face recognition result image
    # ------------------------
    # build models once to store them in the memory
    # otherwise, they will be built after cam started and this will cause delays
    model: FacialRecognition = DeepFace.build_model(model_name=model_name)

    # find custom values for this input set
    target_size = model.input_shape

    logger.info(f"facial recognition model {model_name} is just built")

    if enable_face_analysis:
        DeepFace.build_model(model_name="Age")
        logger.info("Age model is just built")
        DeepFace.build_model(model_name="Gender")
        logger.info("Gender model is just built")
        DeepFace.build_model(model_name="Emotion")
        logger.info("Emotion model is just built")
    # -----------------------
    # call a dummy find function for db_path once to create embeddings in the initialization
    DeepFace.find(
        img_path=np.zeros([224, 224, 3]),
        db_path=db_path,
        model_name=model_name,
        detector_backend=detector_backend,
        distance_metric=distance_metric,
        enforce_detection=False,
    )
    # -----------------------
    # visualization
    # Getting the list of directories 
    # tem_dir = os.listdir("/home/ubuntu/Downloads/Telegram Desktop/image_temporary") 
    cap = cv2.VideoCapture(source)  # webcam
    while True:
        status, img = cap.read()
        img = cv2.flip(img, 1)
        if not status:
            break
        
        toc_ = time.time()
        toc = time.time()
        raw_img = img.copy()
        resolution_x = img.shape[1]
        resolution_y = img.shape[0]
        
        try:
            
            # just extract the regions to highlight in webcam
            face_objs = DeepFace.extract_faces(
                img_path=img,
                target_size=target_size,
                detector_backend=detector_backend,
                enforce_detection=False,
            )
           
            faces = []
            for face_obj in face_objs:
                facial_area = face_obj["facial_area"]
                confidence = face_obj['confidence']
                if facial_area["w"] <= 60:  # discard small detected faces
                    continue
                faces.append(
                    (
                        facial_area["x"],
                        facial_area["y"],
                        facial_area["w"],
                        facial_area["h"],
                    )
                )
             #confidence: Optional threshold for filtering week face detections.
   
        except:  # to avoid exception if no face detected
            faces = []

        # if len(faces) == 0:
        #     # face_included_frames = 0
        #     pass
        # else:
        #     faces = []
        # try:
        if (confidence < 0.01) and (len(os.listdir("/home/ubuntu/Downloads/Telegram Desktop/image_temporary")) != 0) and (check_del == False):
            tic = time.time()
            check_del = True

        if (confidence < 0.01) and (len(os.listdir("/home/ubuntu/Downloads/Telegram Desktop/image_temporary")) != 0) and (check_del == True):
        # while check_del == True:
            # toc = time.time()
            if (toc - tic) >= 3:
                # true_result_found = False
            # cv2.imshow("img", img)
        # # directory of our database
                database_path = "/home/ubuntu/Downloads/Telegram Desktop/FR/database/Shadi"
                csv_path = "/home/ubuntu/Downloads/Telegram Desktop/FR/FR_db.csv"
                temporary_path = "/home/ubuntu/Downloads/Telegram Desktop/image_temporary"
                image_dataset = pd.read_csv(csv_path)
                image_dataset.columns = image_dataset.columns.str.strip()

                for tem_img in os.listdir(temporary_path):
                    tem_img_ = cv2.imread(os.path.join(temporary_path, tem_img))
                    dfs_ = DeepFace.find(img_path=tem_img_, db_path = db_path, model_name = models[2], enforce_detection=False, silent=True)
                    
                    if len(dfs_[0]) > 0:
                        # true_result_found = True  
                        df_ = dfs_[0]
                        candidate_ = df_.iloc[0]
                        img_db = candidate_["identity"].split("/")[-1]
                        # img_db = df_.loc[df_["distance"] == min(df_["distance"])]["identity"][0].split('/')[-1].split('.')[0]
                        image_dataset.loc[image_dataset["Image_Name"] == int(img_db.split(".")[0]), 'Crossing_Time'] = image_dataset.loc[image_dataset["Image_Name"] == int(img_db.split(".")[0]), 'Crossing_Time'].iloc[0] + 1
                        os.remove(os.path.join(temporary_path, tem_img))
                        

                    # if not true_result_found:
                    else:
                        # new_row = {"Image_Name": tem_img.split('.')[0], "Crossing_Time": 1}
                        # image_dataset.iloc[len(image_dataset)] = new_row # only use with a RangeIndex!
                        # image_dataset = image_dataset.append(new_row, ignore_index=True)             
                        image_dataset.loc[len(image_dataset.index)] = [tem_img.split('.')[0], 1]
                        shutil.move(os.path.join(temporary_path, tem_img), database_path)
                # image_dataset = image_dataset.reset_index(drop=True) 
                image_dataset.to_csv(csv_path, index=False)
                check_del = False

            else:
                continue
            # cv2.imshow("img", img)
            # save_csv(csv_path="/home/ubuntu/Downloads/Telegram Desktop/FR/FR_db.csv", db_path="/home/ubuntu/Downloads/Telegram Desktop/FR/database/Shadi", saving_path="/home/ubuntu/Downloads/Telegram Desktop/image_temporary")
         
        # except KeyError:
        detected_faces = []
        face_index = 0
        for x, y, w, h in faces:
          
            if face_index == 0:
                
                cv2.rectangle(img, (x, y), (x + w, y + h), (67, 67, 67), 1)  # draw rectangle to main image  
                
                detected_faces.append((x, y, w, h))
                detected_face = img[int(y) : int(y + h), int(x) : int(x + w)]  # crop detected face
                
                # Checking if the list is empty or not 
                
        face_index = face_index + 1  

        if (confidence >= 0.94) and (len(os.listdir("/home/ubuntu/Downloads/Telegram Desktop/image_temporary")) == 0) and (check_save == False):
            tic_ = time.time()
            check_save = True

        # while check_save == True:
        if (confidence >= 0.94) and (len(os.listdir("/home/ubuntu/Downloads/Telegram Desktop/image_temporary")) == 0) and (check_save == True):
            
            if (toc_ - tic_) >= 1:
                # detected_face = Image.open(r"detected_face")  
                cv2.imwrite((f"/home/ubuntu/Downloads/Telegram Desktop/image_temporary/{random.randint(1, 1000)}.jpg"), detected_face) 
                # detected_face = ImageEnhance.Sharpness(detected_face)
                check_save = False 
            else:
                continue

        

        if len(os.listdir("/home/ubuntu/Downloads/Telegram Desktop/image_temporary")) != 0:
            base_img = raw_img.copy()
            freeze_img = base_img.copy()
            detected_faces_final = detected_faces.copy()

            for detected_face in detected_faces_final:
                x = detected_face[0]
                y = detected_face[1]
                w = detected_face[2]
                h = detected_face[3]

                cv2.rectangle(freeze_img, (x, y), (x + w, y + h), (67, 67, 67), 1)  # draw rectangle to main image   
               
                # extract detected face
                custom_face = base_img[y : y + h, x : x + w]
        
                
                dfs = DeepFace.find(
                    img_path=custom_face,
                    db_path=db_path,
                    model_name=model_name,
                    detector_backend="skip",
                    distance_metric=distance_metric,
                    enforce_detection=False,
                    silent=True,
                )
                df = dfs[0]
                if len(df) > 0:
                    # directly access 1st item because custom face is extracted already
                    # df = dfs[0]

                    if df.shape[0] > 0:
                        candidate = df.iloc[0]
                        label = candidate["identity"]
                        # label = df.loc[df["distance"] == min(df["distance"])]["identity"][0]
                        # to use this source image as is
                        display_img = cv2.imread(label)
                        # to use extracted face
                        source_objs = DeepFace.extract_faces(
                            img_path=display_img,
                            target_size=(pivot_img_size, pivot_img_size),
                            detector_backend=detector_backend,
                            enforce_detection=False,
                            align=False,
                        )
                        if len(source_objs) > 0:
                            # extract 1st item directly
                            source_obj = source_objs[0]
                            display_img = source_obj["face"]
                            display_img *= 255
                            display_img = display_img[:, :, ::-1]
                        # --------------------
                        label = label.split("/")[-1]
                        # customize source code:
                        query_FR_csv = pd.read_csv("/home/ubuntu/Downloads/Telegram Desktop/FR/FR_db.csv")
                        crossing_times = f"This is the {query_FR_csv.loc[query_FR_csv['Image_Name'] == int(label.split('.')[0]), 'Crossing_Time'].iloc[0] + 1}nd time that you pass in front of the camera!"
                        
                        try:
                            if (
                                y - pivot_img_size > 0
                                and x + w + pivot_img_size < resolution_x
                            ):
                                # top right
                                freeze_img[
                                    y - pivot_img_size : y,
                                    x + w : x + w + pivot_img_size,
                                ] = display_img

                                overlay = freeze_img.copy()
                                opacity = 0.4
                                cv2.rectangle(
                                    freeze_img,
                                    (x + w, y),
                                    (x + w + pivot_img_size, y + 20),
                                    (46, 200, 255),
                                    cv2.FILLED,
                                )
                                cv2.addWeighted(
                                    overlay,
                                    opacity,
                                    freeze_img,
                                    1 - opacity,
                                    0,
                                    freeze_img,
                                )

                                cv2.putText(
                                    freeze_img,
                                    crossing_times,
                                    (x + w, y + 10),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5,
                                    text_color,
                                    2,
                                )

                                # connect face and text
                                cv2.line(
                                    freeze_img,
                                    (x + int(w / 2), y),
                                    (x + 3 * int(w / 4), y - int(pivot_img_size / 2)),
                                    (67, 67, 67),
                                    1,
                                )
                                cv2.line(
                                    freeze_img,
                                    (x + 3 * int(w / 4), y - int(pivot_img_size / 2)),
                                    (x + w, y - int(pivot_img_size / 2)),
                                    (67, 67, 67),
                                    1,
                                )

                            elif (
                                y + h + pivot_img_size < resolution_y
                                and x - pivot_img_size > 0
                            ):
                                # bottom left
                                freeze_img[
                                    y + h : y + h + pivot_img_size,
                                    x - pivot_img_size : x,
                                ] = display_img

                                overlay = freeze_img.copy()
                                opacity = 0.4
                                cv2.rectangle(
                                    freeze_img,
                                    (x - pivot_img_size, y + h - 20),
                                    (x, y + h),
                                    (46, 200, 255),
                                    cv2.FILLED,
                                )
                                cv2.addWeighted(
                                    overlay,
                                    opacity,
                                    freeze_img,
                                    1 - opacity,
                                    0,
                                    freeze_img,
                                )

                                cv2.putText(
                                    freeze_img,
                                    crossing_times,
                                    (x - pivot_img_size, y + h - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5,
                                    text_color,
                                    2,
                                )

                                # connect face and text
                                cv2.line(
                                    freeze_img,
                                    (x + int(w / 2), y + h),
                                    (
                                        x + int(w / 2) - int(w / 4),
                                        y + h + int(pivot_img_size / 2),
                                    ),
                                    (67, 67, 67),
                                    1,
                                )
                                cv2.line(
                                    freeze_img,
                                    (
                                        x + int(w / 2) - int(w / 4),
                                        y + h + int(pivot_img_size / 2),
                                    ),
                                    (x, y + h + int(pivot_img_size / 2)),
                                    (67, 67, 67),
                                    1,
                                )

                            elif y - pivot_img_size > 0 and x - pivot_img_size > 0:
                                # top left
                                freeze_img[
                                    y - pivot_img_size : y, x - pivot_img_size : x
                                ] = display_img

                                overlay = freeze_img.copy()
                                opacity = 0.4
                                cv2.rectangle(
                                    freeze_img,
                                    (x - pivot_img_size, y),
                                    (x, y + 20),
                                    (46, 200, 255),
                                    cv2.FILLED,
                                )
                                cv2.addWeighted(
                                    overlay,
                                    opacity,
                                    freeze_img,
                                    1 - opacity,
                                    0,
                                    freeze_img,
                                )

                                cv2.putText(
                                    freeze_img,
                                    crossing_times,
                                    (x - pivot_img_size, y + 10),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5,
                                    text_color,
                                    2,
                                )

                                # connect face and text
                                cv2.line(
                                    freeze_img,
                                    (x + int(w / 2), y),
                                    (
                                        x + int(w / 2) - int(w / 4),
                                        y - int(pivot_img_size / 2),
                                    ),
                                    (67, 67, 67),
                                    1,
                                )
                                cv2.line(
                                    freeze_img,
                                    (
                                        x + int(w / 2) - int(w / 4),
                                        y - int(pivot_img_size / 2),
                                    ),
                                    (x, y - int(pivot_img_size / 2)),
                                    (67, 67, 67),
                                    1,
                                )

                            elif (
                                x + w + pivot_img_size < resolution_x
                                and y + h + pivot_img_size < resolution_y
                            ):
                                # bottom righ
                                freeze_img[
                                    y + h : y + h + pivot_img_size,
                                    x + w : x + w + pivot_img_size,
                                ] = display_img

                                overlay = freeze_img.copy()
                                opacity = 0.4
                                cv2.rectangle(
                                    freeze_img,
                                    (x + w, y + h - 20),
                                    (x + w + pivot_img_size, y + h),
                                    (46, 200, 255),
                                    cv2.FILLED,
                                )
                                cv2.addWeighted(
                                    overlay,
                                    opacity,
                                    freeze_img,
                                    1 - opacity,
                                    0,
                                    freeze_img,
                                )

                                cv2.putText(
                                    freeze_img,
                                    crossing_times,
                                    (x + w, y + h - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5,
                                    text_color,
                                    2,
                                )

                                # connect face and text
                                cv2.line(
                                    freeze_img,
                                    (x + int(w / 2), y + h),
                                    (
                                        x + int(w / 2) + int(w / 4),
                                        y + h + int(pivot_img_size / 2),
                                    ),
                                    (67, 67, 67),
                                    1,
                                )
                                cv2.line(
                                    freeze_img,
                                    (
                                        x + int(w / 2) + int(w / 4),
                                        y + h + int(pivot_img_size / 2),
                                    ),
                                    (x + w, y + h + int(pivot_img_size / 2)),
                                    (67, 67, 67),
                                    1,
                                )
                        except Exception as err:  # pylint: disable=broad-except
                            logger.error(str(err))


                else:
                    custom_test = "This is the first time that you pass!"
                    cv2.putText(freeze_img, custom_test,(20, 20),cv2.FONT_HERSHEY_SIMPLEX,1,text_color, 2)
    

        
     
            cv2.imshow("img", freeze_img)

        else:        
            cv2.imshow("img", img)          

        if cv2.waitKey(1) & 0xFF == ord("q"):  # press q to quit
            break

    # kill open cv things
    cap.release()
    # cv2.destroyAllWindows()


