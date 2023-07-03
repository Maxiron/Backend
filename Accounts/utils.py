# Author: Nwokoro Aaron Nnamdi
# Date created: Thursday, 29th June 2023

# Python imports
import os
import threading

# Third party imports
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1


class Util:
    
    @staticmethod
    # Check if email ends with @futo.edu.ng
    def validate_email(email: str) -> bool:
        if email.endswith("@futo.edu.ng"):
            return True
        else:
            return False
        
class Functions:

    @staticmethod
    def load_models():
        # Load the MTCNN and FaceNet models
        mtcnn = MTCNN(image_size=160, margin=0, min_face_size=20)
        facenet = InceptionResnetV1(pretrained='vggface2').eval()
        return mtcnn, facenet
    
    @staticmethod
    def pre_process_image(image: Image) -> Image:
        # Convert image to RGB
        image = image.convert('RGB')
        return image
    

class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send(fail_silently=True)


           



