# Third party imports
from PIL import Image
import numpy as np
from types import MethodType

# rest_framework imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser

# own imports
from .models import FaceEmbedding, CustomUser
from .utils import Functions

import torch
from torchvision.transforms import functional as F
from facenet_pytorch import MTCNN, InceptionResnetV1
from sklearn.metrics.pairwise import cosine_similarity


class RegisterFaceAPIView(APIView):
    permission_classes = (AllowAny,)
    parser_classes = (MultiPartParser, FormParser,)
    def post(self, request, format=None):
        # Load the MTCNN and FaceNet models
        mtcnn, facenet = Functions.load_models()

        # Get the uploaded image
        image_file = request.FILES.get('image')

        # Get the email and use it to retrieve the user
        try:
            email = request.data.get('email')
        except:
            return Response({'message': 'Email not provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Open the uploaded image
        try:
            image = Image.open(image_file)
        except:
            return Response({'message': 'Invalid image file'}, status=status.HTTP_400_BAD_REQUEST)

        # Convert image to RGB
        image = image.convert('RGB')

        # Detect faces in the image
        boxes, _ = mtcnn.detect(image)

        if boxes is None:
            response = {
                'status': 'failed',
                'message': 'No faces detected in image'
                }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)  
        if len(boxes) > 1:
            response = {
                'status': 'failed',
                'message': 'Multiple faces detected in image'
                }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        # Generate the embedding for the detected face
        box = boxes[0]
        x1, y1, x2, y2 = box
        face_image = image.crop((x1, y1, x2, y2))
        face_tensor = F.to_tensor(face_image)
        face_tensor = F.normalize(face_tensor, mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        embedding = facenet(face_tensor.unsqueeze(0)).detach().numpy()[0]


        # Save the embeddings to a binary field in the database
        face_embedding = FaceEmbedding.objects.create(user=user)
        face_embedding.set_embedding(embedding)
        face_embedding.save()


        response = {
            'status': 'success',
            'message': 'Face embeddings saved successfully',
        }

        return Response(response, status=status.HTTP_200_OK)
 
    


class RecognizeCheckAPIView(APIView):
    permission_classes = (AllowAny,)
    parser_classes = (MultiPartParser, FormParser,)
    def post(self, request, format=None):
        # Load the MTCNN and FaceNet models
        mtcnn, facenet = self.load_models()

        # Get the uploaded image
        image_file = request.FILES.get('image')

        # Open the uploaded image
        try:
            image = Image.open(image_file)
        except:
            return Response({'message': 'Invalid image file'}, status=status.HTTP_400_BAD_REQUEST)

        # Convert image to RGB
        image = image.convert('RGB')

        # Resize the image to 160x160 pixels

        # Detect faces in the image
        boxes, _ = mtcnn.detect(image)
        print(len(boxes))

        if boxes is None or len(boxes) == 0:
            return Response({'message': 'No faces detected in image'}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(boxes) > 1:
            return Response({'message': 'Multiple faces detected in image'}, status=status.HTTP_400_BAD_REQUEST)

        
        # Generate the embedding for the captured face
        '''
        Select the first bounding box from a list of bounding boxes
        The bounding box represents the coordinates (x1, y1, x2, y2) of a detected face region in the image.
        '''
        box = boxes[0]
        '''
        Assign the values of the four coordinates of the bounding box to separate variables: 
        x1 (left), y1 (top), x2 (right), and y2 (bottom). 
        These coordinates define the region of the image containing the face.
        '''        
        x1, y1, x2, y2 = box

        '''
        Crop the original image using the coordinates of the bounding box
        This extracts the face region from the image as a separate image 
        '''
        face_image = image.crop((x1, y1, x2, y2))

        '''
        Convert the cropped face image to a PyTorch tensor.
        This converts the image in a format suitable for input to a neural network. 
        '''
        face_tensor = F.to_tensor(face_image)

        '''
        Normalize the pixel values of the face tensor. 
        This operation subtracts the mean value of [0.5, 0.5, 0.5] from each channel 
        and divides by the standard deviation value of [0.5, 0.5, 0.5]. 
        This normalization step ensures that the input has zero mean and unit variance,
        which can improve the performance of the neural network.
        '''
        face_tensor = F.normalize(face_tensor, mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])


        '''
        Pass the normalized face tensor through a neural network model called facenet 
        to obtain the face embedding vector.
        The resulting embedding is then converted to a NumPy array using
        '''
        embedding = facenet(face_tensor.unsqueeze(0)).detach().numpy()[0]


        # Load the face embeddings from the database
        # face_embeddings = FaceEmbedding.objects.all()
        # if not face_embeddings.exists():
        #     return Response({'message': 'No faces in database'}, status=status.HTTP_404_NOT_FOUND)
        from .list import embeddingss
        existing_embedding = embeddingss.reshape(1, -1)
        new_embedding = np.array(embedding).reshape(1, -1)

        # Calculate the cosine similarity between the captured embedding and database embeddings
        # similarities = cosine_similarity([embedding], face_embeddings.values_list('embedding', flat=True))
        similarities = cosine_similarity(new_embedding, existing_embedding)
        print(similarities)

        # Find the index of the highest similarity
        closest_index = np.argmax(similarities)

        # Check if the similarity is above a threshold
        threshold = 0.75  # Adjust the threshold as needed
        if similarities[0, closest_index] > threshold:
            # match = face_embeddings[closest_index].name
            # match = embeddingss[closest_index].name
            return Response({'message': 'Matching face found in database', 'match': "match"})
        else:
            return Response({'message': 'No matching face found in database'}, status=status.HTTP_404_NOT_FOUND)
