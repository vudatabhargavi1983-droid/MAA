from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
import os
import joblib
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import EmotionJournal
import speech_recognition as sr

import tempfile
from mental_health_backend.services.ml_client import ml_client # ✅ NEW ML CLIENT

from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import EmotionJournal
import speech_recognition as sr

import tempfile
from transformers import pipeline
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import ExtractWeekDay
from django.core.exceptions import ObjectDoesNotExist
import random
from .models import (
    UserProfile, Guardian, Category, MeditationSession, YogaSession,
    UserPreferences, BackgroundMusic, CalmingSession, GroundingSession, 
    PanicSession, StressBusterSession, MoodLog, AffirmationCategory,
    GenericAffirmation, CustomAffirmation, AffirmationTemplate, MusicCategory, MusicTrack,  MusicSession, CBTTopic, CBTSession, Disorder, Article, CopingMethod, RoadmapStep,EmotionJournal,
    TherapySession, TherapyRecord, ReflectionQuestion, TherapyRecordAnswer # ✅ ADDED Therapy Models
)
from .serializers import (
    UserProfileSerializer, GuardianSerializer, CategorySerializer,
    MeditationSessionSerializer, YogaSessionSerializer, UserPreferencesSerializer,
    BackgroundMusicSerializer, CalmingSessionSerializer, GroundingSessionSerializer, 
    PanicSessionSerializer, StressBusterSessionSerializer, MoodLogSerializer,
    AffirmationCategorySerializer, GenericAffirmationSerializer,
    CustomAffirmationSerializer, AffirmationTemplateSerializer, MusicCategorySerializer, MusicTrackSerializer,
    MusicSessionSerializer, CBTTopicSerializer, CBTSessionSerializer, DisorderSerializer, ArticleSerializer, CopingMethodSerializer, RoadmapStepSerializer, EmotionJournalSerializer,
    TherapySessionSerializer, TherapyRecordSerializer # ✅ ADDED Therapy Serializers
)

# ---------------------------
# Authentication Views
# ---------------------------

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        user = authenticate(username=user.username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            }, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class RegisterView(APIView):
    parser_classes = [MultiPartParser, FormParser]  # ✅ Explicitly allow file uploads

    def post(self, request):
        print("📝 Register Endpoint Hit")
        print("Data:", request.data)
        
        name = request.data.get('name')
        age = request.data.get('age')
        phone_number = request.data.get('phone_number')
        email = request.data.get('email')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
        gender = request.data.get('gender')
        medical_history = request.FILES.get('medical_history')
        guardian_name = request.data.get('guardian_name')
        guardian_relationship = request.data.get('guardian_relationship')
        guardian_phone_number = request.data.get('guardian_phone_number')
        guardian_email = request.data.get('guardian_email')

        # Validate required fields
        required_fields = {
            'name': name, 'age': age, 'phone_number': phone_number, 'email': email,
            'password': password, 'confirm_password': confirm_password,
            'guardian_name': guardian_name, 'guardian_relationship': guardian_relationship,
            'guardian_phone_number': guardian_phone_number, 'guardian_email': guardian_email
        }
        for field_name, field_value in required_fields.items():
            if not field_value:
                print(f"❌ Missing field: {field_name}")
                return Response({'error': f'{field_name.replace("_", " ").title()} is required'}, 
                               status=status.HTTP_400_BAD_REQUEST)

        if password != confirm_password:
            return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if email exists
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate medical history file
        if medical_history and not medical_history.name.lower().endswith('.pdf'):
            return Response({'error': 'Medical history must be a PDF file'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create user
            # ✅ FIX: Use email as username to strictly avoid collisions on same-first-name users
            # Or use a more robust unique generator. Using email is standard safe practice.
            username = email 
            
            # Check if this username/email already exists (safety double check)
            if User.objects.filter(username=username).exists():
                 return Response({'error': 'Account with this email already exists'}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.create_user(username=username, email=email, password=password)

            # Create user profile
            user_profile = UserProfile.objects.create(
                user=user, 
                name=name, 
                age=int(age), 
                phone_number=phone_number, 
                email=email,
                gender=gender if gender else None, 
                medical_history=medical_history
            )

            # Create guardian
            Guardian.objects.create(
                user=user, 
                name=guardian_name, 
                relationship=guardian_relationship,
                phone_number=guardian_phone_number, 
                email=guardian_email
            )

            # Generate token
            refresh = RefreshToken.for_user(user)
            print(f"✅ User Registered Successfully: {email}")
            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user_id': user.id,
                'username': user.username,
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)
        
        except ValueError as e:
            print(f"❌ Value Error during registration: {str(e)}")
            return Response({'error': f'Invalid data: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"❌ Critical Error during registration: {str(e)}")
            return Response({'error': f'Registration failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResetPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Use host from request to make it work on any IP (important for mobile)
            host = request.get_host()
            # path should match what's in urls.py
            reset_link = f"http://{host}/api/auth/reset-confirm/{uid}/{token}/"
            
            send_mail(
                'Password Reset Request',
                f'Click this link to reset your password or copy the codes below:\n\n'
                f'Link: {reset_link}\n\n'
                f'Verification Code (UID): {uid}\n'
                f'Verification Token: {token}\n\n'
                f'Paste these into the app if the link doesn\'t open automatically.',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False
            )
            return Response({'message': 'Password reset link sent to your email'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Failed to send email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResetPasswordConfirmView(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                return Response({'message': 'Token is valid', 'uid': uidb64}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, User.DoesNotExist):
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, uidb64, token):
        # Prefer values from body if present, else use from URL
        uid_input = request.data.get('uid', uidb64)
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not all([new_password, confirm_password]):
            return Response({'error': 'Passwords are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_password:
            return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            uid_int = force_str(urlsafe_base64_decode(uid_input))
            user = User.objects.get(pk=uid_int)
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, User.DoesNotExist):
            return Response({'error': 'Invalid token or user'}, status=status.HTTP_400_BAD_REQUEST)

# ---------------------------
# User Profile and Related Views
# ---------------------------

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GuardianView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            guardians = Guardian.objects.filter(user=request.user)
            serializer = GuardianSerializer(guardians, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            guardian, _ = Guardian.objects.get_or_create(user=request.user)
            serializer = GuardianSerializer(guardian, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            categories = Category.objects.all()
            serializer = CategorySerializer(categories, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ---------------------------
# Meditation & Yoga Views
# ---------------------------

class MeditationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            meditations = MeditationSession.objects.all().select_related('category')
            serializer = MeditationSessionSerializer(meditations, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MeditationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            meditation = MeditationSession.objects.get(pk=pk)
            serializer = MeditationSessionSerializer(meditation)
            return Response(serializer.data)
        except MeditationSession.DoesNotExist:
            return Response({'error': 'Meditation not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class YogaListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            yoga_sessions = YogaSession.objects.all().select_related('type')
            serializer = YogaSessionSerializer(yoga_sessions, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class YogaDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            yoga = YogaSession.objects.get(pk=pk)
            serializer = YogaSessionSerializer(yoga)
            return Response(serializer.data)
        except YogaSession.DoesNotExist:
            return Response({'error': 'Yoga session not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ---------------------------
# Audio Upload & Preferences Views
# ---------------------------

class UploadAudioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            audio_file = request.FILES.get('audio_file')
            audio_type = request.data.get('audio_type', 'meditation')
            category_id_str = request.data.get('category_id')
            title = request.data.get('title', f'Untitled {audio_type}')
            description = request.data.get('description', '')
            duration_str = request.data.get('duration', '0')
            emoji = request.data.get('emoji', '')

            if not audio_file:
                return Response({'error': 'Audio file is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Safely convert duration
            try:
                duration = int(duration_str) if duration_str else 0
            except (ValueError, TypeError):
                duration = 0

            if audio_type == 'meditation':
                category = None
                if category_id_str:
                    try:
                        category_id = int(category_id_str)
                        category = Category.objects.get(id=category_id)
                    except (ValueError, Category.DoesNotExist):
                        category = None
                
                meditation_session = MeditationSession.objects.create(
                    title=title,
                    description=description,
                    duration=duration,
                    audio_file=audio_file,
                    category=category,
                    emoji=emoji
                )
                serializer = MeditationSessionSerializer(meditation_session)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            elif audio_type == 'yoga':
                yoga_type = None
                if category_id_str:
                    try:
                        category_id = int(category_id_str)
                        yoga_type = Category.objects.get(id=category_id)
                    except (ValueError, Category.DoesNotExist):
                        yoga_type = None
                
                yoga_session = YogaSession.objects.create(
                    title=title,
                    description=description,
                    duration=duration,
                    audio_file=audio_file,
                    type=yoga_type,
                    emoji=emoji
                )
                serializer = YogaSessionSerializer(yoga_session)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            elif audio_type == 'background':
                background_music = BackgroundMusic.objects.create(
                    title=title,
                    audio_file=audio_file,
                    emoji=emoji
                )
                serializer = BackgroundMusicSerializer(background_music)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            return Response({'error': 'Invalid audio type. Use: meditation, yoga, or background'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'error': f'Upload failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserPreferencesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            preferences, _ = UserPreferences.objects.get_or_create(user=request.user)
            serializer = UserPreferencesSerializer(preferences)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            preferences, _ = UserPreferences.objects.get_or_create(user=request.user)
            serializer = UserPreferencesSerializer(preferences, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BackgroundMusicView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            music = BackgroundMusic.objects.all()
            serializer = BackgroundMusicSerializer(music, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ---------------------------
# Session Logging Views
# ---------------------------

class CalmingSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data.copy()
            data['user'] = request.user.id
            data['end_time'] = timezone.now()
            serializer = CalmingSessionSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GroundingSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data.copy()
            data['user'] = request.user.id
            data['end_time'] = timezone.now()
            serializer = GroundingSessionSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PanicSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data.copy()
            data['user'] = request.user.id
            data['end_time'] = timezone.now()
            serializer = PanicSessionSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StressBusterSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from chatbot.core.generation_layer import GenerationLayer
            from langchain_groq import ChatGroq
            import os
            
            data = request.data.copy()
            data['user'] = request.user.id
            data['end_time'] = timezone.now()
            
            # Handle file upload for voice_file
            if 'voice_file' in request.FILES:
                data['voice_file'] = request.FILES['voice_file']
            
            serializer = StressBusterSessionSerializer(data=data)
            if serializer.is_valid():
                session = serializer.save()
                
                # --- AI ANALYSIS START ---
                try:
                    transcription = ""
                    voice_emotion = "unknown"
                    
                    # 1. Speech-to-Text (STT)
                    if session.voice_file:
                        try:
                            import shutil
                            import os
                            
                            # 0. SETUP ENV BEFORE PYDUB IMPORT
                            # Add current directory to PATH so pydub finds ffmpeg and ffprobe
                            cwd = os.getcwd()
                            if cwd not in os.environ["PATH"]:
                                os.environ["PATH"] += os.pathsep + cwd
                                print(f"🔍 DEBUG: Added {cwd} to PATH")

                            local_ffmpeg = os.path.join(cwd, 'ffmpeg.exe')
                            local_ffprobe = os.path.join(cwd, 'ffprobe.exe')

                            # Verify tools exist
                            has_ffmpeg = shutil.which("ffmpeg") is not None or os.path.exists(local_ffmpeg)
                            has_ffprobe = shutil.which("ffprobe") is not None or os.path.exists(local_ffprobe)
                            
                            file_size = session.voice_file.size
                            print(f"🔍 DEBUG: Voice File Size: {file_size}, FFMPEG: {has_ffmpeg}, FFPROBE: {has_ffprobe}")

                            if not has_ffmpeg and not os.path.exists(local_ffmpeg):
                                error_msg = "FFmpeg not found. Please run the setup script."
                                print(f"❌ {error_msg}")
                                raise Exception(error_msg)
                            
                            # 1. IMPORT PYDUB (Now search path is set)
                            from pydub import AudioSegment
                            if os.path.exists(local_ffmpeg):
                                AudioSegment.converter = local_ffmpeg
                                print(f"🔍 DEBUG: Set AudioSegment.converter = {local_ffmpeg}")
                            if not has_ffprobe:
                                print("⚠️ WARNING: FFprobe not found. Audio conversion might fail.")
                            
                            # Create a recognizer
                            r = sr.Recognizer()
                            
                            # Convert to format SR likes (WAV) using pydub
                            audio_path = session.voice_file.path
                            
                            # Convert to wav in a temp file
                            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                                audio = AudioSegment.from_file(audio_path)
                                audio.export(temp_wav.name, format="wav")
                                temp_wav_path = temp_wav.name
                                print(f"🔍 DEBUG: Converted WAV size: {os.path.getsize(temp_wav_path)}")
                                
                            with sr.AudioFile(temp_wav_path) as source:
                                audio_data = r.record(source)
                                transcription = r.recognize_google(audio_data)
                                print(f"🔍 STT Transcript: {transcription}")
                                
                            # Cleanup temp file
                            os.remove(temp_wav_path)

                        except sr.UnknownValueError:
                            print("❌ STT Error: Google Speech Recognition could not understand audio (UnknownValueError)")
                            transcription = "[Audio was provided but could not be understood. Maybe too quiet?]"
                        except sr.RequestError as e:
                            print(f"❌ STT Error: Could not request results from Google Speech Recognition service; {e}")
                            transcription = "[STT Service Unreachable]"
                        except Exception as stt_e:
                            print(f"❌ STT Error: {repr(stt_e)}") # repr gives type and message
                            transcription = f"[Audio transcription failed: {str(stt_e)}]"
                            # FORCE ERROR VISIBILITY FOR DEBUGGING
                            session.feedback = f"⚠️ Technical Issue: {repr(stt_e)}"
                            session.save()
                            return Response({
                                **serializer.data,
                                'feedback': session.feedback,
                                'transcription': transcription
                            }, status=status.HTTP_201_CREATED)

                    # 2. AI Feedback Generation
                    note_text = session.note_text or ""
                    
                    if note_text or (transcription and not transcription.startswith("[")):
                        prompt = f"""
                        You are a compassionate mental health AI (MAA).
                        
                        USER SESSION:
                        - Type: Stress Buster
                        - User Note: "{note_text}"
                        - Audio Transcript: "{transcription}"
                        
                        TASK:
                        1. ANALYZE: Briefly explain the user's situation and feelings back to them to show deep understanding and validation.
                        2. SOLUTION: Provide a specific, actionable, and tailored coping strategy or solution for their specific problem.
                        
                        TONE: Compassionate, non-judgmental, and practical.
                        FORMAT: Use a clear "Analysis" and "Proposed Solution" structure. Keep it concise but meaningful.
                        """
                        
                        llm = ChatGroq(
                            api_key=settings.GROQ_API_KEY,
                            model_name=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
                            temperature=0.7
                        )
                        
                        response = llm.invoke(prompt)
                        feedback = response.content.strip()
                        
                        # Save feedback
                        session.feedback = feedback
                        session.save()
                        
                        # Return updated data
                        return Response({
                            **serializer.data,
                            'feedback': feedback,
                            'transcription': transcription
                        }, status=status.HTTP_201_CREATED)
                        
                except Exception as ai_e:
                    print(f"❌ AI Analysis Error: {ai_e}")
                    # Fallback: return created session without feedback
                    
                return Response(serializer.data, status=status.HTTP_201_CREATED)
                
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ---------------------------
# SOS Emergency View
# ---------------------------

class SOSView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("🚨 SOS ENDPOINT TRIGGERED")
        try:
            profile = UserProfile.objects.get(user=request.user)
            print(f"👤 User Profile Found: {profile.name}")
            
            guardian = Guardian.objects.filter(user=request.user).first()
            if not guardian:
                print("❌ No guardian found for user")
                return Response({'error': 'No guardian set for this user'}, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"🛡️ Guardian Found: {guardian.name} ({guardian.email})")

            location = request.data.get('location', 'Location not provided')
            print(f"📍 Location: {location}")

            subject = f"🚨 URGENT SOS: {profile.name} needs immediate help!"
            
            # HTML Content for a professional, "smooth" emergency email
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    .container {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        max-width: 600px;
                        margin: 0 auto;
                        border: 2px solid #ff4d4d;
                        border-radius: 12px;
                        overflow: hidden;
                        background-color: #ffffff;
                    }}
                    .header {{
                        background-color: #ff4d4d;
                        color: white;
                        padding: 20px;
                        text-align: center;
                    }}
                    .content {{
                        padding: 30px;
                        color: #333333;
                        line-height: 1.6;
                    }}
                    .alert-box {{
                        background-color: #fff5f5;
                        border-left: 5px solid #ff4d4d;
                        padding: 15px;
                        margin: 20px 0;
                        border-radius: 4px;
                    }}
                    .button {{
                        display: inline-block;
                        padding: 12px 24px;
                        background-color: #ff4d4d;
                        color: white !important;
                        text-decoration: none;
                        border-radius: 8px;
                        font-weight: bold;
                        margin-top: 20px;
                        text-align: center;
                    }}
                    .footer {{
                        background-color: #f8f9fa;
                        padding: 15px;
                        text-align: center;
                        font-size: 12px;
                        color: #777777;
                    }}
                    .detail-label {{
                        font-weight: bold;
                        color: #555555;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin:0;">⚠️ EMERGENCY SOS ⚠️</h1>
                    </div>
                    <div class="content">
                        <p>Dear <strong>{guardian.name}</strong>,</p>
                        <p>This is an automated emergency alert from the <strong>Mental Health Support App</strong>.</p>
                        
                        <div class="alert-box">
                            <h2 style="color:#d93025; margin-top:0;">{profile.name} needs your help!</h2>
                            <p>They have triggered a distress signal and may be in immediate danger or experiencing severe emotional crisis.</p>
                        </div>

                        <p><span class="detail-label">📍 Last Known Location:</span><br>
                        <a href="{location}" style="color:#1a73e8;">{location}</a></p>
                        
                        <p><span class="detail-label">📞 Contact Number:</span><br>
                        {profile.phone_number}</p>
                        
                        <p><span class="detail-label">🕒 Time of Trigger:</span><br>
                        {timezone.now().strftime('%Y-%m-%d %H:%M:%S')} (Server Time)</p>

                        <a href="tel:{profile.phone_number}" class="button">CALL NOW</a>
                        <a href="{location}" class="button" style="background-color:#4285f4; margin-left:10px;">TRACK LOCATION</a>
                    </div>
                    <div class="footer">
                        Sent via MAA Mental Health App Security Protocol.<br>
                        Please do not reply to this automated email.
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Fallback plain text message
            plain_message = (
                f"🚨 URGENT SOS ALERT 🚨\n\n"
                f"Dear {guardian.name},\n"
                f"{profile.name} has triggered an SOS and needs immediate help.\n\n"
                f"📍 Location: {location}\n"
                f"📞 Phone: {profile.phone_number}\n"
                f"🕒 Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"PLEASE ACTION IMMEDIATELY."
            )
            
            print("📧 Attempting to send high-priority HTML email...")
            print(f"From: {settings.EMAIL_HOST_USER}")
            print(f"To: {guardian.email}")
            
            send_mail(
                subject,
                plain_message,
                settings.EMAIL_HOST_USER,
                [guardian.email],
                fail_silently=False,
                html_message=html_message
            )
            print("✅ HTML Email sent successfully")
            
            return Response({
                'message': f'SOS alert sent successfully to {guardian.name} ({guardian.phone_number})',
                'guardian_name': guardian.name,
                'guardian_email': guardian.email
            }, status=status.HTTP_200_OK)
        
        except UserProfile.DoesNotExist:
            print("❌ User profile not found")
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            print("❌ SOS Error Traceback:")
            traceback.print_exc()
            return Response({'error': f'Failed to send SOS: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ---------------------------
# Mood Tracking Views
# ---------------------------

class MoodLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            period = request.query_params.get('period', 'all')
            tag = request.query_params.get('tag')
            mood_logs = MoodLog.objects.filter(user=request.user).order_by('-date_time')

            # Filter by period
            if period == 'week':
                start_date = timezone.now() - timedelta(days=7)
                mood_logs = mood_logs.filter(date_time__gte=start_date)
            elif period == 'month':
                start_date = timezone.now() - timedelta(days=30)
                mood_logs = mood_logs.filter(date_time__gte=start_date)

            # Filter by tag
            if tag:
                mood_logs = mood_logs.filter(tag=tag)

            serializer = MoodLogSerializer(mood_logs, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = MoodLogSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MoodSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            start_date = timezone.now() - timedelta(days=7)
            mood_logs = MoodLog.objects.filter(user=request.user, date_time__gte=start_date)

            if not mood_logs.exists():
                return Response({
                    'summary': 'No mood logs for this week',
                    'mood_counts': {},
                    'suggestions': []
                }, status=status.HTTP_200_OK)

            # Mood Categories for Analysis (Synced with Frontend 10 Moods)
            POSITIVE_MOODS = ['Happy', 'Grateful', 'Loved', 'Excited', 'Productive', 'Creative', 'happy', 'grateful', 'loved', 'excited', 'productive', 'creative']
            CALM_MOODS = ['Calm', 'Relaxed', 'calm', 'relaxed']
            SAD_MOODS = ['Sad', 'Lonely', 'Grief', 'sad', 'lonely', 'grief', 'Tired', 'tired']
            ANGRY_MOODS = ['Angry', 'Frustrated', 'angry', 'frustrated']
            STRESS_MOODS = ['Anxious', 'Stressed', 'Overwhelmed', 'anxious', 'stressed', 'overwhelmed']
            
            # Count moods
            mood_counts = {}
            happiest_hours = []
            
            pos_count = 0
            neg_count = 0 # Sad + Angry + Stress

            for log in mood_logs:
                mood = log.mood_label
                mood_counts[mood] = mood_counts.get(mood, 0) + 1
                
                if mood in POSITIVE_MOODS:
                    happiest_hours.append(log.date_time.hour)
                    pos_count += 1
                elif mood in CALM_MOODS:
                    # Neutral isn't strictly positive but isn't negative
                    pass 
                elif mood in SAD_MOODS or mood in ANGRY_MOODS or mood in STRESS_MOODS:
                    neg_count += 1

            # Calculate happiest time
            happiest_time = 'Unknown'
            if happiest_hours:
                avg_hour = sum(happiest_hours) // len(happiest_hours)
                start_hour = avg_hour % 12 or 12
                start_period = 'AM' if avg_hour < 12 else 'PM'
                end_hour = (avg_hour + 3) % 12 or 12
                end_period = 'AM' if (avg_hour + 3) < 12 else 'PM'
                happiest_time = f"{start_hour} {start_period} - {end_hour} {end_period}"

            # Weekend sadness analysis
            weekend_sad_logs = mood_logs.filter(
                mood_label__in=SAD_MOODS,
                date_time__week_day__in=[6, 7]  # Saturday=6, Sunday=7
            )
            sad_count_weekend = weekend_sad_logs.count()
            total_sad = mood_logs.filter(mood_label__in=SAD_MOODS).count()
            sad_weekends = sad_count_weekend > (total_sad / 2) if total_sad > 0 else False

            # Generate summary
            summary = (
                f"In the past week, you had {pos_count} positive/calm moments "
                f"and {neg_count} challenging moments. "
                f"Your happiest moments were usually between {happiest_time}. "
                f"{'Notice: Sadness tends to increase over weekends.' if sad_weekends else ''}"
            )

            # Generate suggestions
            suggestions = []
            
            # aggregated counts
            total_sad_count = sum(mood_counts.get(m, 0) for m in SAD_MOODS)
            total_angry_count = sum(mood_counts.get(m, 0) for m in ANGRY_MOODS)
            total_stress_count = sum(mood_counts.get(m, 0) for m in STRESS_MOODS)

            if total_sad_count > 2:
                suggestions.append("🌿 Try a calming breathing session, journaling, or music therapy when feeling down.")
            if total_angry_count > 1:
                suggestions.append("💪 Consider stress buster activities or a quick workout to manage excess energy.")
            if total_stress_count > 2:
                suggestions.append("🧘 A grounding exercise or meditation might help reduce anxiety and overwhelm.")
            
            if pos_count > neg_count:
                suggestions.append("🎉 Great job! You're maintaining positive moods more often.")

            # Calculate dominant mood
            dominant_mood = 'Unknown'
            if mood_counts:
                dominant_mood = max(mood_counts, key=mood_counts.get)

            return Response({
                'summary': summary,
                'mood_counts': mood_counts,
                'suggestions': suggestions,
                'dominant_mood': dominant_mood,
                'total_entries': mood_logs.count(),
                'week_period': start_date.strftime('%Y-%m-%d') + ' to ' + timezone.now().strftime('%Y-%m-%d')
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ---------------------------
# AFFIRMATIONS VIEWS (COMPLETE & FIXED)
# ---------------------------

class AffirmationCategoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all affirmation categories with count of active affirmations"""
        try:
            categories = AffirmationCategory.objects.all().prefetch_related('affirmations')
            serializer = AffirmationCategorySerializer(categories, many=True)
            print(f"DEBUG: Returning {len(serializer.data)} categories")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"ERROR in categories: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Admin-only: Create new affirmation category"""
        try:
            serializer = AffirmationCategorySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GenericAffirmationsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, category_id=None, **kwargs):  # ✅ FIXED: Accept **kwargs
        """Get generic affirmations - random or by category"""
        try:
            # ✅ category_id comes from URL kwargs OR is None for all
            if category_id:  # From URL path /affirmations/generic/123/
                affirmations = GenericAffirmation.objects.filter(
                    category_id=category_id, 
                    is_active=True
                ).order_by('?')[:20]  # Random 20 from category
                print(f"DEBUG: Category {category_id} has {affirmations.count()} affirmations")
            else:  # No category_id = /affirmations/generic/ (all categories)
                # Get 3 random from each category
                categories = AffirmationCategory.objects.all()
                all_affirmations = []
                
                for category in categories:
                    cat_affs = GenericAffirmation.objects.filter(
                        category=category, 
                        is_active=True
                    ).order_by('?')[:3]  # 3 random per category
                    all_affirmations.extend(cat_affs)
                
                # Shuffle and limit to 15 total
                random.shuffle(all_affirmations)
                affirmations = all_affirmations[:15]
                print(f"DEBUG: Loaded {len(affirmations)} random affirmations from all categories")
            
            if not affirmations:
                return Response({
                    'message': 'No affirmations found. Check admin for GenericAffirmations.',
                    'affirmations': []
                }, status=status.HTTP_200_OK)
            
            serializer = GenericAffirmationSerializer(affirmations, many=True)
            return Response({
                'count': len(serializer.data),
                'affirmations': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"ERROR in generic affirmations: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Admin-only: Create generic affirmation"""
        try:
            serializer = GenericAffirmationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class CustomAffirmationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's custom affirmations"""
        try:
            affirmations = CustomAffirmation.objects.filter(user=request.user).order_by('-created_at')
            serializer = CustomAffirmationSerializer(affirmations, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create custom affirmation for user - FIXED GENERATION"""
        try:
            data = request.data.copy()
            
            # ✅ VALIDATE INPUT FIELDS
            focus_area = data.get('focus_area', '').strip()
            challenge = data.get('challenge', '').strip()
            positive_direction = data.get('positive_direction', '').strip()
            
            if not all([focus_area, challenge, positive_direction]):
                return Response({
                    'error': 'focus_area, challenge, and positive_direction are all required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ✅ CHECK IF TEXT ALREADY PROVIDED (AI GENERATED)
            if data.get('affirmation_text'):
                 affirmation_text = data.get('affirmation_text')
            else:
                # ✅ IMPROVED AFFIRMATION TEMPLATES
                affirmation_templates = {
                    'calm': "I am finding {focus_area} within myself, gently releasing {challenge} and embracing {positive_direction}.",
                    'confidence': "I am building {focus_area} every day. Even when {challenge}, I choose {positive_direction}.",
                    'self-love': "I deserve {focus_area}. I release {challenge} and welcome {positive_direction} into my heart.",
                    'motivation': "{focus_area} fuels my journey. I transform {challenge} into {positive_direction}.",
                    'peace': "I cultivate {focus_area} amidst {challenge}. My path leads to {positive_direction}.",
                    'strength': "I am strong in {focus_area}. {Challenge} cannot dim my {positive_direction}.",
                    'joy': "{Focus_area} fills my heart. I let go of {challenge} and embrace {positive_direction}.",
                }
                
                # Use template matching focus_area or fallback
                template_key = focus_area.lower()
                template = affirmation_templates.get(template_key)
                
                if template:
                    affirmation_text = template.format(
                        focus_area=focus_area,
                        challenge=challenge,
                        positive_direction=positive_direction
                    )
                else:
                    # Generic fallback with better structure
                    affirmation_text = (
                        f"I am cultivating {focus_area.lower()} within myself. "
                        f"Even when facing {challenge.lower()}, I am moving towards {positive_direction.lower()}. "
                        f"I am strong, capable, and worthy of this journey."
                    )
            
            # ✅ SET ALL FIELDS PROPERLY
            data.update({
                'user': request.user.id,
                'affirmation_text': affirmation_text,
                'focus_area': focus_area,
                'challenge': challenge,
                'positive_direction': positive_direction,
            })
            
            print(f"DEBUG: Creating affirmation...")
            print(f"  Focus: {focus_area}")
            print(f"  Challenge: {challenge}")
            print(f"  Direction: {positive_direction}")
            print(f"  Generated: {affirmation_text[:100]}...")
            
            serializer = CustomAffirmationSerializer(data=data)
            if serializer.is_valid():
                instance = serializer.save()
                print(f"✅ SUCCESS: Created affirmation ID {instance.id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                print(f"❌ SERIALIZER ERRORS: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"❌ ERROR in custom affirmation: {str(e)}")
            return Response({
                'error': f'Failed to create affirmation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, pk):
        """Delete user's custom affirmation"""
        try:
            affirmation = CustomAffirmation.objects.get(id=pk, user=request.user)
            affirmation.delete()
            return Response({'message': 'Affirmation deleted successfully'}, status=status.HTTP_200_OK)
        except CustomAffirmation.DoesNotExist:
            return Response({'error': 'Affirmation not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class GenerateAIAffirmationsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Generate custom affirmations using AI based on chat context"""
        try:
            from chatbot.core.generation_layer import GenerationLayer
            from langchain_groq import ChatGroq
            import os
            
            count = request.data.get('count', 3)
            chat_history = request.data.get('chat_history', '')
            user_context = request.data.get('user_context', '') # Fallback if no chat history
            
            if not chat_history and not user_context:
                return Response({'error': 'Context needed. Please provide chat_history or user_context'}, status=400)
            
            # Construct Prompt
            prompt = f"""
            You are an expert affirmation generator.
            
            USER CONTEXT:
            {chat_history if chat_history else user_context}
            
            TASK:
            Generate {count} specific, powerful, and personalized affirmations for this user based on their context.
            
            RULES:
            1. Return ONLY the affirmations as a numbered list.
            2. Do not include introductory text like "Here are your affirmations".
            3. Each affirmation should be positive, present tense, and empowering.
            4. Keep them concise.
            """
            
            # Call LLM Directly (reuse GenerationLayer settings if possible, or init new)
            llm = ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model_name=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
                temperature=0.7
            )
            
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            # Parse list
            affirmations_list = []
            for line in content.split('\n'):
                clean_line = line.strip()
                # Remove numbering like "1. ", "2. "
                if clean_line and (clean_line[0].isdigit() or clean_line.startswith('-')):
                    parts = clean_line.split(' ', 1)
                    if len(parts) > 1:
                        affirmations_list.append(parts[1].strip('"'))
                    else:
                        affirmations_list.append(clean_line)
                elif clean_line:
                    affirmations_list.append(clean_line)
            
            # Validations
            if not affirmations_list:
                affirmations_list = ["I am good enough.", "I believe in myself.", "I am calm and confident."]
            
            return Response({
                'affirmations': affirmations_list[:int(count)]
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"AI Gen Error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RandomCustomAffirmationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get random custom affirmation for user"""
        try:
            affirmations = CustomAffirmation.objects.filter(user=request.user)
            if affirmations.exists():
                random_aff = random.choice(list(affirmations))
                serializer = CustomAffirmationSerializer(random_aff)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({
                'message': 'No custom affirmations created yet. Create some to get personalized affirmations!'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RandomAffirmationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get a completely random affirmation (generic + custom mix)"""
        try:
            # Get some generic affirmations
            generic_affs = list(GenericAffirmation.objects.filter(is_active=True))
            # Get user's custom affirmations
            custom_affs = list(CustomAffirmation.objects.filter(user=request.user))
            
            all_affs = generic_affs + custom_affs
            
            if not all_affs:
                return Response({
                    'message': 'No affirmations available. Add some categories and affirmations in admin!'
                }, status=status.HTTP_200_OK)
            
            random_aff = random.choice(all_affs)
            
            if isinstance(random_aff, GenericAffirmation):
                serializer = GenericAffirmationSerializer(random_aff)
            else:
                serializer = CustomAffirmationSerializer(random_aff)
            
            return Response({
                'affirmation': serializer.data,
                'type': 'generic' if isinstance(random_aff, GenericAffirmation) else 'custom'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AffirmationTemplatesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get affirmation templates for creating custom affirmations"""
        try:
            templates = AffirmationTemplate.objects.all()
            serializer = AffirmationTemplateSerializer(templates, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class MusicCategoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            categories = MusicCategory.objects.prefetch_related('tracks').all()
            serializer = MusicCategorySerializer(categories, many=True)
            return Response({
                'categories': serializer.data,
                'total_categories': len(serializer.data)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MusicTracksView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, category_id):
        try:
            category = MusicCategory.objects.get(id=category_id)
            tracks = MusicTrack.objects.filter(category=category)
            serializer = MusicTrackSerializer(tracks, many=True)
            return Response({
                'tracks': serializer.data,
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'emoji': category.emoji,
                    'color': category.color
                },
                'total_tracks': len(serializer.data)
            }, status=status.HTTP_200_OK)
        except MusicCategory.DoesNotExist:
            return Response({'error': 'Music category not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MusicSessionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            data = request.data.copy()
            data['user'] = request.user.id
            
            # Validate required fields
            required_fields = ['category', 'mood_change', 'current_emotion']
            for field in required_fields:
                if not data.get(field):
                    return Response({'error': f'{field} is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = MusicSessionSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            sessions = MusicSession.objects.filter(user=request.user).order_by('-created_at')[:10]
            serializer = MusicSessionSerializer(sessions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# CBT THERAPY VIEWS
class CBTTopicView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            topics = CBTTopic.objects.all()
            serializer = CBTTopicSerializer(topics, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DisorderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            disorders = Disorder.objects.all()
            serializer = DisorderSerializer(disorders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"ERROR in DisorderListView: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DisorderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            disorder = Disorder.objects.get(pk=pk)
            serializer = DisorderSerializer(disorder)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Disorder.DoesNotExist:
            return Response({'error': 'Disorder not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"ERROR in DisorderDetailView: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ArticleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, disorder_id):
        try:
            articles = Article.objects.filter(disorder_id=disorder_id)
            serializer = ArticleSerializer(articles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"ERROR in ArticleListView: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CopingMethodListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, disorder_id):
        try:
            methods = CopingMethod.objects.filter(disorder_id=disorder_id)
            serializer = CopingMethodSerializer(methods, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"ERROR in CopingMethodListView: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RoadmapView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, disorder_id):
        try:
            disorder = Disorder.objects.get(pk=disorder_id)
            steps = RoadmapStep.objects.filter(disorder_id=disorder_id).order_by('order')
            
            steps_serializer = RoadmapStepSerializer(steps, many=True, context={'request': request})
            
            roadmap_image_url = None
            if disorder.roadmap_image:
                roadmap_image_url = request.build_absolute_uri(disorder.roadmap_image.url)

            return Response({
                'roadmap_image': roadmap_image_url,
                'steps': steps_serializer.data
            }, status=status.HTTP_200_OK)
        except Disorder.DoesNotExist:
            return Response({'error': 'Disorder not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"ERROR in RoadmapView: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from .models import EmotionLog


from django.apps import apps

# ========================
# VOICE EMOTION
# ========================

class VoiceEmotionView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        try:
            audio_file = request.FILES.get('audio')
            if not audio_file:
                return Response({'error': 'No audio file provided'}, status=status.HTTP_400_BAD_REQUEST)

            emotion, confidence = ml_client.predict_audio(audio_file)
            
            EmotionLog.objects.create(modality="voice", emotion=emotion, confidence=confidence)
            return Response({"emotion": emotion, "confidence": round(confidence, 3)})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ========================
# TEXT EMOTION
# ========================

class TextEmotionView(APIView):
    def post(self, request):
        text = request.data.get('text', '').strip()
        if not text:
            return Response({"error": "No text sent"}, status=400)

        emotion, confidence = ml_client.predict_text(text)

        EmotionLog.objects.create(modality="text", emotion=emotion, confidence=confidence)
        return Response({"emotion": emotion, "confidence": round(confidence, 3)})

# ========================
# FACE EMOTION
# ========================

class FaceEmotionView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        img_file = request.FILES.get('image')
        if not img_file:
             return Response({"error": "No image file"}, status=400)

        emotion, confidence = ml_client.predict_face(img_file)

        EmotionLog.objects.create(modality="face", emotion=emotion, confidence=confidence)
        return Response({"emotion": emotion, "confidence": round(confidence, 3)})
class TriModalJournalView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        user = request.user if request.user.is_authenticated else None

        text = request.data.get("text", "")
        # Frontend sends 'audio' and 'image' keys in saveTriModalJournal
        voice_file = request.FILES.get("audio") or request.FILES.get("voice")
        face_file = request.FILES.get("image") or request.FILES.get("face_image")

        print(f"\n🔍 [Backend] Tri-Modal Request Received")
        print(f"   - Text: {text[:50]}..." if text else "   - Text: None")
        
        if voice_file:
            print(f"   - Voice File: {voice_file.name} ({voice_file.size} bytes)")
        else:
            print(f"   - Voice File: None (Check frontend 'audio' or 'voice' key)")

        if face_file:
            print(f"   - Face File: {face_file.name} ({face_file.size} bytes)")
        else:
            print(f"   - Face File: None (Check frontend 'image' or 'face_image' key)")
        
        # 1. Call Fusion Server
        final_emotion, confidence, components = ml_client.predict_multimodal(
            text=text, 
            voice_file=voice_file, 
            face_file=face_file
        )
        
        print(f"   => ML Server Result: {final_emotion} ({confidence})")

        # 2. Extract component results (optional, for logging)
        voice_emotion = "neutral"
        if components and components.get('voice'):
             voice_emotion = components['voice'].get('dominant_emotion', 'neutral')

        text_emotion = "neutral"
        if components and components.get('text'):
             text_emotion = components['text'].get('dominant_emotion', 'neutral')

        face_emotion = "neutral"
        if components and components.get('face'):
             face_emotion = components['face'].get('dominant_emotion', 'neutral')

        # 3. Save Journal
        # Note: We need to rewind files before saving if ModelField tries to read them, 
        # but django Request files usually handle multiple reads if they are InMemory or TempFile.
        if voice_file: voice_file.seek(0)
        if face_file: face_file.seek(0)

        journal = EmotionJournal.objects.create(
            user=user,
            text=text,
            voice=voice_file,
            face_image=face_file,
            voice_emotion=voice_emotion,
            text_emotion=text_emotion,
            face_emotion=face_emotion,
            final_emotion=final_emotion
        )

        return Response({
            "message": "Journal saved", 
            "emotion": final_emotion,
            "confidence": confidence,
            "components": components
        }, status=status.HTTP_201_CREATED)

# ---------------------------
# THERAPY MODULE VIEWS (Music & Drawing)
# ---------------------------

class TherapySessionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            therapy_type = request.query_params.get('type') # 'Music' or 'Drawing'
            sessions = TherapySession.objects.all()
            if therapy_type:
                sessions = sessions.filter(therapy_type=therapy_type)
            
            serializer = TherapySessionSerializer(sessions, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TherapySessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            session = TherapySession.objects.get(pk=pk)
            serializer = TherapySessionSerializer(session)
            return Response(serializer.data)
        except TherapySession.DoesNotExist:
            return Response({'error': 'Therapy session not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TherapyRecordCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        try:
            data = request.data.copy()
            user = request.user
            
            # Extract basic fields
            session_id = data.get('session_id')
            mood_before = data.get('mood_before')
            mood_after = data.get('mood_after')
            reflection_notes = data.get('reflection_notes')
            drawing_file = request.FILES.get('drawing_file')
            
            if not session_id:
                return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)
                
            try:
                session = TherapySession.objects.get(pk=session_id)
            except TherapySession.DoesNotExist:
                return Response({'error': 'Invalid Session ID'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create Record
            record = TherapyRecord.objects.create(
                user=user,
                session=session,
                mood_before=mood_before,
                mood_after=mood_after,
                reflection_notes=reflection_notes,
                drawing_file=drawing_file
            )
            
            # Parse Answers 
            answers_json = data.get('answers')
            if answers_json:
                import json
                try:
                    answers_list = json.loads(answers_json)
                    for ans in answers_list:
                        q_id = ans.get('question_id')
                        a_text = ans.get('answer_text')
                        if q_id and a_text:
                            question = ReflectionQuestion.objects.get(pk=q_id)
                            TherapyRecordAnswer.objects.create(
                                record=record,
                                question=question,
                                answer_text=a_text
                            )
                except Exception as json_error:
                    print(f"Error parsing answers: {json_error}")
                    pass

            serializer = TherapyRecordSerializer(record)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"Error creating therapy record: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CBTSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data
            user = request.user
            
            topic_id = data.get('topic') # Changed from 'topic_id' to 'topic'
            situation = data.get('situation')
            automatic_thought = data.get('automatic_thought')
            emotions = data.get('emotions')
            evidence_for = data.get('evidence_for')
            evidence_against = data.get('evidence_against')
            balanced_thought = data.get('balanced_thought')
            session_duration = data.get('session_duration', 0)
            
            if not all([topic_id, situation, automatic_thought]):
                 return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

             # Create Session
            topic = CBTTopic.objects.get(pk=topic_id)
            session = CBTSession.objects.create(
                user=user,
                topic=topic,
                situation=situation,
                automatic_thought=automatic_thought,
                emotions=emotions,
                evidence_for=evidence_for,
                evidence_against=evidence_against,
                balanced_thought=balanced_thought,
                session_duration=session_duration
            )
            
            # --- AI ANALYSIS ---
            ai_analysis = ''
            try:
                from langchain_groq import ChatGroq
                import os
                
                settings_api_key = getattr(settings, 'GROQ_API_KEY', None)
                api_key = settings_api_key or os.getenv('GROQ_API_KEY')

                if api_key:
                    prompt = f'''
                    You are an expert, warm, and empathetic CBT Therapist. 
                    The user has just completed a Thought Record to challenge a negative thought.
                    
                    User's Entry:
                    - Situation: {situation}
                    - Negative Thought: {automatic_thought}
                    - Evidence Against: {evidence_against}
                    - New Balanced Thought: {balanced_thought}
                    
                    Your Task:
                    Write a short, supportive response (3-4 sentences) speaking DIRECTLY to the user.
                    1. Warmly validate their effort in reframing this thought.
                    2. Offer a gentle observation on their balanced thought—if it's good, reinforce it; if it could be stronger, gently suggest how.
                    
                    CRITICAL: Do NOT use headers like "Validation" or "Analysis". Do NOT use bullet points. Write as a caring human therapist.
                    '''
                    
                    llm = ChatGroq(
                        api_key=api_key,
                        model_name=os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant'),
                        temperature=0.7
                    )
                    
                    response = llm.invoke(prompt)
                    ai_analysis = response.content.strip()
                    
                    # Store analysis
                    session.ai_analysis = ai_analysis
                    session.save()
            except Exception as e:
                print(f'CBT AI Error: {e}')
                ai_analysis = 'AI Analysis unavailable.'

            return Response({
                'id': session.id,
                'message': 'CBT Session saved',
                'ai_analysis': ai_analysis
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            sessions = CBTSession.objects.filter(user=request.user).order_by('-created_at')[:10]
            serializer = CBTSessionSerializer(sessions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================
# MOOD TRACKING VIEWS
# ========================

class MoodLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Return recent logs
        logs = MoodLog.objects.filter(user=request.user).order_by('-date_time')[:50]
        # Basic serialization
        data = []
        for log in logs:
            data.append({
                'id': log.id,
                'mood_emoji': log.mood_emoji, # ID like 'happy'
                'mood_label': log.mood_label,
                'note': log.note,
                'created_at': log.date_time
            })
        return Response(data)

    def post(self, request):
        try:
            data = request.data
            MoodLog.objects.create(
                user=request.user,
                mood_emoji=data.get('moodEmoji'),
                mood_label=data.get('moodLabel'),
                note=data.get('note'),
                tag=data.get('tag')
            )
            return Response({'message': 'Logged'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class MoodSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # 1. Fetch Logs (Last 14 days)
            two_weeks_ago = timezone.now() - timedelta(days=14)
            logs = MoodLog.objects.filter(user=request.user, date_time__gte=two_weeks_ago).order_by('date_time')
            
            if not logs.exists():
                return Response({
                    'dominant_mood': 'No Data',
                    'total_entries': 0,
                    'summary': "Start logging your moods to get AI insights!",
                    'mood_counts': {},
                    'suggestions': []
                })

            # 2. Prepare Data for AI
            log_strings = []
            counts = {}
            for log in logs:
                # Count
                lbl = log.mood_label or 'Unknown'
                counts[lbl] = counts.get(lbl, 0) + 1
                
                # String for prompt
                date_str = log.date_time.strftime("%a %d")
                note_str = f"({log.note})" if log.note else ""
                log_strings.append(f"- {date_str}: {lbl} {note_str}")
            
            # Dominant Mood
            dominant_mood = max(counts, key=counts.get) if counts else "Neutral"
            
            # 3. Call AI
            from langchain_groq import ChatGroq
            from langchain_core.messages import SystemMessage, HumanMessage
            import os
            import json
            
            # Simple heuristic backup if AI fails
            ai_summary = f"You have logged {len(logs)} entries recently. Your dominant mood is {dominant_mood}."
            ai_suggestions = ["Try a short meditation."]
            
            if os.getenv("GROQ_API_KEY"):
                try:
                    llm = ChatGroq(temperature=0.7, model_name="llama-3.3-70b-versatile")
                    
                    prompt = f"""
                    You are an empathetic mental health companion. Analyze these mood logs for user '{request.user.username}':
                    
                    {chr(10).join(log_strings)}
                    
                    Task:
                    1. Write a warm, friendly summary (max 3 sentences) acknowledging their feelings. Be validating.
                    2. Suggest 2 specific, actionable activities from our app (Options: '4-7-8 Breathing', '5-4-3-2-1 Grounding', 'Music Therapy', 'Journaling', 'Yoga', 'Meditations').

                    Output JSON ONLY:
                    {{
                        "summary": "...",
                        "suggestions": ["...", "..."]
                    }}
                    """
                    
                    response = llm.invoke([HumanMessage(content=prompt)])
                    content = response.content.strip()
                    # Robust JSON extraction
                    start = content.find('{')
                    end = content.rfind('}')
                    if start != -1 and end != -1:
                        content = content[start:end+1]
                    
                    parsed = json.loads(content, strict=False)
                    ai_summary = parsed.get('summary', ai_summary)
                    ai_suggestions = parsed.get('suggestions', ai_suggestions)
                    
                except Exception as e:
                    print(f"AI Generation Failed: {e}")
            
            return Response({
                'dominant_mood': dominant_mood,
                'total_entries': logs.count(),
                'summary': ai_summary,
                'mood_counts': counts,
                'suggestions': ai_suggestions
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

