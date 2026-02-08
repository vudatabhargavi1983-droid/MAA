import re
import os
from enum import Enum
import time
from langchain_groq import ChatGroq
from django.conf import settings

class State(Enum):
    CHECK_IN = "CHECK_IN"
    VALIDATION = "VALIDATION"
    CHOICE = "CHOICE"  # New state for "Talk or Calm?"
    EXPLORATION = "EXPLORATION"
    INTERVENTION = "INTERVENTION"
    REFLECTION = "REFLECTION"
    CONCLUSION = "CONCLUSION"
    CLOSURE = "CLOSURE"

class SessionFSM:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state = State.CHECK_IN
        self.history = []
        self.last_updated = time.time()
        self.locked_help_mode = False # Step 1: Lock after advice
        
        # MEANING MEMORY (The Core Brain Fix)
        self.core_context = {
            "trigger_event": None,
            "core_fear": None,
            "primary_emotion": None,
            "secondary_emotion": None,
            "story": None, # Semantic summary
            "mode": None
        }
        
        # Fast summarizer for memory
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name="llama-3.1-8b-instant",
            temperature=0.1 # Low temp for factual summary
        )

        # FIX: Question cooldown for Friend mode
        self.friend_question_cooldown = 0
        self.explore_count = 0
        
    def update_context(self, text: str, signals: dict):
        """
        Extracts and Persists Meaning (Semantic Story, Trigger, Fear, Emotion).
        """
        text_lower = text.lower()
        
        # 1. Check if short reply (Don't overwrite context)
        is_short = len(text.split()) < 4
        if is_short and self.core_context["primary_emotion"]:
            if signals["emotion"] != "NEUTRAL":
                 self.core_context["primary_emotion"] = signals["emotion"]
            return
            
        # 2. Semantic Memory Extraction (NEW: Fixes keyword fragility)
        if not is_short:
            try:
                summary_prompt = f"Summarize the user's core psychological issue or event in ONE short sentence: \"{text}\""
                summary = self.llm.predict(summary_prompt).strip()
                self.core_context["story"] = summary
            except Exception as e:
                print(f"Memory update error: {e}")

        # 3. Extract Trigger (Heuristic backup)
        if "when" in text_lower or "because" in text_lower or "after" in text_lower:
             try:
                 parts = re.split(r'when|because|after', text_lower, 1)
                 if len(parts) > 1:
                     self.core_context["trigger_event"] = parts[1].strip()
             except: pass
        elif "failed" in text_lower:
             self.core_context["trigger_event"] = "failed test"
             self.core_context["core_fear"] = "judgment"

        # 4. Extract Fear
        if any(w in text_lower for w in ["judge", "hate", "laugh", "think", "stupid", "failure"]):
            self.core_context["core_fear"] = "judgment/rejection"
        elif any(w in text_lower for w in ["alone", "leave", "abandon"]):
            self.core_context["core_fear"] = "abandonment"
            
        # 5. Update Emotion
        if signals["emotion"] != "NEUTRAL":
            self.core_context["primary_emotion"] = signals["emotion"]
            
    def update_state(self, signals: dict, risk: str, mode: str = 'friend'):
        """
        Layer 4: State Machine Logic.
        """
        # 1. Safety Override
        if risk in ["CRITICAL", "HIGH"] and self.state != State.INTERVENTION:
            self.state = State.INTERVENTION
            return self.state

        # 2. Turn Count Logic (Fix 1: Stop looping forever)
        # We check the length of history (each pair is 1 turn)
        # We move to intervention if we've been talking too long without action
        turn_count = len([m for m in self.history if m == "user_msg"]) 
        
        # 3. Intent Logic (Fix 3: Jump to solution if asked)
        user_wants_solution = signals.get("intent") == "SOLVE"
        
        if user_wants_solution and self.state not in [State.INTERVENTION, State.REFLECTION]:
            self.state = State.INTERVENTION
            return self.state

        # Step 3: Respect the Help Lock
        if self.locked_help_mode and signals.get("intent") != "CONCLUDE":
            # Check for unlock signals (thanks, feeling better)
            unlock_keywords = ["okay", "thanks", "thank you", "that helped", "feel better", "good", "clear"]
            if any(kw in str(signals.get("text", "")).lower() for kw in unlock_keywords):
                self.locked_help_mode = False
                self.state = State.CONCLUSION
                return self.state
            
            self.state = State.INTERVENTION
            return self.state

        # Step 4: Handle Conclusion Intent
        if signals.get("intent") == "CONCLUDE":
            self.locked_help_mode = False
            self.state = State.CONCLUSION
            return self.state

        # 4. Normal Flow Logic
        if self.state == State.CHECK_IN:
            if signals.get("type") == "FEELING" or signals.get("emotion") != "NEUTRAL":
                self.previous_state = self.state
                self.state = State.VALIDATION
                
        elif self.state == State.VALIDATION:
            self.previous_state = self.state
            if mode == 'guide':
                self.state = State.EXPLORATION # Guide: Validation -> Exploration
            else:
                self.state = State.EXPLORATION
            
        elif self.state == State.CHOICE:
            pref = signals.get("action_preference", "NONE")
            self.previous_state = self.state
            if pref == "CALM" or user_wants_solution:
                self.state = State.INTERVENTION
            else:
                self.state = State.EXPLORATION

        elif self.state == State.EXPLORATION:
            self.explore_count += 1
            # FIX: If turns > 2 (or explore_count >= 2) go to Intervention
            if turn_count >= 2 or self.explore_count >= 2 or user_wants_solution or signals.get("distortion") != "none":
                self.previous_state = self.state
                self.state = State.INTERVENTION
            
        elif self.state == State.INTERVENTION:
            self.history.append("intervention_step")
            # Always move forward: Intervention -> Reflection
            if len([x for x in self.history if x == "intervention_step"]) > 2: 
                self.previous_state = self.state
                self.state = State.REFLECTION
            
        elif self.state == State.REFLECTION:
            self.previous_state = self.state
            self.state = State.CONCLUSION
            
        elif self.state == State.CONCLUSION:
            self.previous_state = self.state
            self.state = State.CLOSURE
            
        elif self.state == State.CLOSURE:
            self.state = State.CHECK_IN
            
        return self.state

# Simple in-memory storage for FSMs
# In production, use Redis or Django Session
_sessions = {}

def get_session(session_id: str) -> SessionFSM:
    if session_id not in _sessions:
        _sessions[session_id] = SessionFSM(session_id)
    return _sessions[session_id]
