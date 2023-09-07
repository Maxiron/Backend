# Third party imports
from PIL import Image, ImageDraw
import numpy as np
from types import MethodType
import base64
import six

# rest_framework imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser

# own imports
from .models import FaceEmbedding, CustomUser
from .utils import Functions
from .serializers import UpdateUserSerializer

import torch
from torchvision.transforms import functional as F
from facenet_pytorch import extract_face
from sklearn.metrics.pairwise import cosine_similarity


class RegisterFaceAPIView(APIView):
    permission_classes = (AllowAny,)
    parser_classes = (MultiPartParser, FormParser,)
    def post(self, request, format=None):
        try:
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

            # Check if a similar embedding already exists in the database using cosine similarity

            # 1. Get all the face_embeddings 
            face_embeddings = FaceEmbedding.objects.all()           

            # Convert the byte embeddings from the database to NumPy arrays
            existing_embeddings = [np.frombuffer(face_embedding.embedding, dtype=np.float32).reshape(1, -1) for face_embedding in face_embeddings]

            # Concatenate the array of arrays into a single 2D array
            existing_embeddings = np.concatenate(existing_embeddings, axis=0)

            new_embedding = np.array(embedding).reshape(1, -1)

            # Calculate the cosine similarity between the captured embedding and database embeddings
            similarities = cosine_similarity(new_embedding, existing_embeddings)

            # Find the index of the highest similarity
            closest_index = np.argmax(similarities)
            # print(closest_index)

            # Check if the similarity is above a threshold
            threshold = 0.65  # Adjust the threshold as needed
            if similarities[0, closest_index] > threshold:
                # Get the user corresponding to the highest similarity in the database
                user_high = face_embeddings[closest_index.item()].user
                print(user)
                print(user_high)

                # Get similarity score
                similarity_score = similarities[0, closest_index].item()

                # Convert the similarity score to a percentage
                similarity_score_percentage = round(similarity_score * 100, 2)

                # if user_high exists, and is not the same as the user, return a message
                if user_high and user_high != user:
                    response = {
                        'status': 'failed',
                        'message': 'Face already exists in database',
                        'similarity_score': f"{similarity_score_percentage}%"
                    }
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
                

            # Save the embeddings to a binary field in the database
            face_embedding = FaceEmbedding.objects.create(user=user)
            face_embedding.set_embedding(embedding)
            face_embedding.save()

            # Verify user
            user.is_verified = True
            user.save()


            response = {
                'status': 'success',
                'message': 'Face embeddings saved successfully',
            }

            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response = {
                "status": False,
                "message": str(e)
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST) 
 
    


class RecognizeCheckAPIView(APIView):
    permission_classes = (AllowAny,)
    parser_classes = (MultiPartParser, FormParser,)
    def post(self, request, format=None):
        try:
            # Load the MTCNN and FaceNet models
            mtcnn, facenet = Functions.load_models()

            # Get the uploaded image
            image_file = request.FILES.get('image')

            # Get the user level
            level = request.data.get('level')

            # Open the uploaded image
            try:
                image = Image.open(image_file)
            except:
                return Response({'message': 'Invalid image file'}, status=status.HTTP_400_BAD_REQUEST)

            
            # Convert image to RGB
            image = image.convert('RGB')

            '''
            # Save the image to a temporary file
            image.save('temp1.jpg')
            '''

            # Detect faces in the image
            boxes, _ = mtcnn.detect(image)

            '''
            boxes, probs, points = mtcnn.detect(image, landmarks=True)
            # Draw boxes and save faces
            img_draw = image.copy()
            draw = ImageDraw.Draw(img_draw)
            for i, (box, point) in enumerate(zip(boxes, points)):
                draw.rectangle(box.tolist(), width=5)
                for p in point:
                    draw.rectangle((p - 10).tolist() + (p + 10).tolist(), width=10)
                extract_face(image, box, save_path='detected_face_{}.png'.format(i))
            img_draw.save('annotated_faces.png')
            '''
            

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
            # Draw the bounding box around the detected face region and save the image
            draw = ImageDraw.Draw(image)
            draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=2)

            # Save the image with the bounding box
            image_with_box_path = 'image_with_box.jpg'
            image.save(image_with_box_path)
            '''


            '''
            Crop the original image using the coordinates of the bounding box
            This extracts the face region from the image as a separate image 
            '''
            face_image = image.crop((x1, y1, x2, y2))

            '''
            # Save the cropped face image
            face_image_path = 'face_image.jpg'
            face_image.save(face_image_path)
            '''

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


            # Filter the Face embedding database table by Level and get the embeddings of all users in that level
            face_embeddings = FaceEmbedding.objects.filter(user__level=level)

            # If there are no embeddings in the database, return a message
            if not face_embeddings:
                response = {
                    'status': 'failed',
                    'message': 'No face embeddings found for this level'
                    }
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            # Convert the byte embeddings from the database to NumPy arrays
            existing_embeddings = [np.frombuffer(face_embedding.embedding, dtype=np.float32).reshape(1, -1) for face_embedding in face_embeddings]
            
            # Concatenate the array of arrays into a single 2D array
            existing_embeddings = np.concatenate(existing_embeddings, axis=0)

            new_embedding = np.array(embedding).reshape(1, -1)

            # Calculate the cosine similarity between the captured embedding and database embeddings
            similarities = cosine_similarity(new_embedding, existing_embeddings)

            # Find the index of the highest similarity
            closest_index = np.argmax(similarities)
            # print(closest_index)

            # Check if the similarity is above a threshold
            threshold = 0.75  # Adjust the threshold as needed
            if similarities[0, closest_index] > threshold:
                # Get the user corresponding to the highest similarity in the database
                user = face_embeddings[closest_index.item()].user

                # Get similarity score
                similarity_score = similarities[0, closest_index].item()

                # Convert the similarity score to a percentage
                similarity_score_percentage = round(similarity_score * 100, 2)

                # Return the user details
                user = UpdateUserSerializer(user).data

                response = {
                    'status': 'success',
                    'message': 'Matching face found in database',
                    'similarity_score': f"{similarity_score_percentage}%",
                    'user': user
                }

                return Response(response, status=status.HTTP_200_OK)
            else:
                # Get similarity score
                similarity_score = similarities[0, closest_index].item()

                # Convert the similarity score to a percentage
                similarity_score_percentage = round(similarity_score * 100, 2)
                response = {
                    'status': 'failed',
                    'message': 'No matching face found in database',
                    'similarity_score': f"{similarity_score_percentage}%",
                }
                return Response(response, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response = {
                "status": False,
                "message": str(e)
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST) 
