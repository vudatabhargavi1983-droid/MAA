import os

class Settings:
    PROJECT_NAME = "Mental Health ML Inference Server"
    VERSION = "1.0.0"
    
    # Paths 
    # Logic: This file is in core/config.py. Parent is core. Parent of that is ml_inference_server.
    SERVER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODEL_DIR = os.path.join(SERVER_ROOT, "models")
    
    # Fallback if ENV override
    if os.getenv("MODEL_DIR"):
        MODEL_DIR = os.getenv("MODEL_DIR")

    FACE_MODEL_PATH = os.path.join(MODEL_DIR, "emotion_model_7class_torchscript.pt")
    VOICE_MODEL_PATH = os.path.join(MODEL_DIR, "wav2vec2_emotion_torchscript.pt")
    TEXT_MODEL_PATH = os.path.join(MODEL_DIR, "roberta_goemotions_torchscript.pt")

    # =========================================================
    # 🧠 THE BRAIN: NORMALIZATION LAYER
    # =========================================================
    
    # 1. THE UNIVERSAL LANGUAGE (Output)
    # Every model's output will be converted to these 5 keys.
    FINAL_EMOTIONS = ["happy", "sad", "angry", "fear", "neutral"]

    # 2. FACE MODEL TRANSLATION (Input: FER2013 7-Class)
    # The Face model speaks: [anger, disgust, fear, happy, neutral, sad, surprise]
    FACE_LABELS = ["anger", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
    
    FACE_MAPPING = {
        "anger": "angry",       # Direct map
        "disgust": "angry",     # Merged (Disgust -> Angry)
        "fear": "fear",         # Direct map
        "happy": "happy",       # Direct map
        "neutral": "neutral",   # Direct map
        "sad": "sad",           # Direct map
        "surprise": "happy",    # Merged (Surprise usually positive here -> Happy)
    }

    # 3. TEXT MODEL TRANSLATION (Input: GoEmotions subset)
    # The Text model speaks: [anger, fear, joy, sadness, surprise]
    TEXT_LABELS = ["anger", "fear", "joy", "sadness", "surprise"]
    
    TEXT_MAPPING = {
        "anger": "angry",
        "fear": "fear",
        "joy": "happy",     # Joy -> Happy
        "sadness": "sad",
        "surprise": "happy" # Merged
    }

    # 4. VOICE MODEL TRANSLATION (Input: LabelEncoder classes)
    # We need to know the exact classes from your dataset. 
    # For now, I am assuming a standard set, but we can update this list.
    # RAVDESS Order: 01=neutral, 02=calm, 03=happy, 04=sad, 05=angry, 06=fear, 07=disgust, 08=surprise
    VOICE_LABELS = ["neutral", "calm", "happy", "sad", "angry", "fear", "disgust", "surprise"] 
    
    VOICE_MAPPING = {
        "angry": "angry",
        "calm": "neutral",  # Calm -> Neutral
        "disgust": "angry", # Merged
        "fear": "fear",
        "happy": "happy",
        "neutral": "neutral",
        "sad": "sad",
        "surprise": "happy"
    }

    # Thresholds for Fusion
    CONFIDENCE_THRESHOLD = 0.4  # If below this, we might ignore the prediction

settings = Settings()
