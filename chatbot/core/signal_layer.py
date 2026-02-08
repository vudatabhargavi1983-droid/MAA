import json
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from django.conf import settings

class SignalLayer:
    def process(self, text: str) -> dict:
        """
        Layer 2: Psychological Signal Extraction (Heuristic/Keyword Optimized).
        Replaced LLM call with fast Keyword Matching to fix 429 Rate Limits.
        """
        text_lower = text.lower()
        
        # 1. Detect Emotion (Keyword Base)
        emotion = "NEUTRAL"
        if any(w in text_lower for w in ["sad", "cry", "tear", "alone", "hurt", "fail", "lost", "grief", "heavy", "pain"]):
            emotion = "SAD"
        elif any(w in text_lower for w in ["anxious", "worry", "panic", "scared", "fear", "afraid", "nervous", "future", "what if"]):
            emotion = "ANXIOUS"
        elif any(w in text_lower for w in ["angry", "mad", "hate", "furious", "annoyed", "unfair", "rage"]):
            emotion = "ANGRY"
        elif any(w in text_lower for w in ["stressed", "tired", "burned out", "busy", "overwhelmed", "pressure"]):
            emotion = "STRESSED"
        elif any(w in text_lower for w in ["happy", "good", "great", "joy", "excited", "love", "thanks", "better"]):
            emotion = "HAPPY"
            
        # 2. Detect Hopelessness & Crisis (Critical)
        hopelessness = False
        crisis_keywords = [
            "die", "kill myself", "suicide", "end it all", "no point", "worthless", "give up",
            "self-harm", "overdose", "end my life", "jump", "hang", "cutting", "better off dead",
            "don't want to live", "kill all", "hurt them", "harm", "kill everyone", "slash", "stab", "poison",
            "kill ", "murder", "hurt others", "want to kill", "violence"
        ]
        
        # Regex check for standalone "kill" to avoid "skill" but catch "kill him", "kill mouli"
        import re
        if any(w in text_lower for w in crisis_keywords) or re.search(r'\bkill\b', text_lower):
            hopelessness = True
            
        # 3. Detect Intensity (Keyword Scoring)
        intensity = 3 # Default Mild
        # Boosters
        if any(w in text_lower for w in ["very", "so", "really", "extremely", "totally", "can't", "never", "always"]):
            intensity += 2
        # Critical words
        if hopelessness or emotion == "ANGRY" or "panic" in text_lower:
            intensity += 2
            
        if intensity > 10: intensity = 10
        
        # 4. Detect Distortion (Simple checks)
        distortion = "none"
        if "always" in text_lower or "never" in text_lower or "everyone" in text_lower:
            distortion = "all_or_nothing"
        elif "fault" in text_lower or "blame" in text_lower:
            distortion = "self_blame"
            
        # 5. Detect Query Type (Feeling vs Question)
        q_type = "FEELING"
        question_words = ["how", "what", "why", "when", "where", "who", "can you", "could you", "should i", "tell me", "help me"]
        if "?" in text_lower or any(text_lower.startswith(w) for w in question_words):
            q_type = "QUESTION"
            
        # 6. Detect Intent (NEW: VENT vs SOLVE)
        intent = "VENT"
        solve_keywords = ["what should i do", "how to fix", "advice", "help me with", "solution", "suggest", "tips", "how do i"]
        if any(kw in text_lower for kw in solve_keywords) or (q_type == "QUESTION" and any(w in text_lower for w in ["how", "should"])):
            intent = "SOLVE"
        
        # 7. Detect Conclude Intent (NEW Step 1: Conclusion Mode)
        conclude_keywords = ["solution", "conclusion", "what now", "final", "summary", "done", "wrap up", "stop", "end"]
        if any(kw in text_lower for kw in conclude_keywords):
            intent = "CONCLUDE"

        return {
            "emotion": emotion,
            "intensity": intensity,
            "type": q_type,
            "distortion": distortion,
            "hopelessness": hopelessness,
            "intent": intent,
            "action_preference": "NONE"
        }
