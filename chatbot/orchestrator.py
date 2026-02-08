from chatbot.core.input_layer import InputLayer
from chatbot.core.signal_layer import SignalLayer
from chatbot.core.safety_layer import SafetyLayer
from chatbot.core.session_manager import get_session
from chatbot.core.decision_layer import DecisionLayer
from chatbot.core.rag_layer import RAGLayer
from chatbot.core.generation_layer import GenerationLayer

class Orchestrator:
    def __init__(self):
        self.signal_layer = SignalLayer()
        self.generation_layer = GenerationLayer()
        
    def process_message(self, session_id: str, text: str, mode: str = 'friend') -> str:
        """
        Executes the 7-Layer Cognitive Architecture.
        """
        # --- PRE-LAYER: History Retrieval ---
        from chatbot.models import ChatMessage
        history_msgs = ChatMessage.objects.filter(session__session_id=session_id).order_by('-timestamp')[:10]
        # Reverse to get chronological order
        history_msgs = reversed(history_msgs)
        formatted_history = [
            {"role": "user" if msg.sender == 'user' else "assistant", "content": msg.content}
            for msg in history_msgs
        ]

        # --- Layer 1: Input ---
        clean_text = InputLayer.process(text)
        if not clean_text:
            return "I'm listening."
            
        # --- Layer 2: Signals ---
        # Extracts: Emotion, Intensity, Distortion, etc.
        signals = self.signal_layer.process(clean_text)
        # Debug log for visibility
        # print(f"[ORCHESTRATOR] Signals: {signals}")
        
        # --- Layer 3: Risk ---
        # Output: LOW, MEDIUM, HIGH, CRITICAL
        risk_level = SafetyLayer.evaluate(signals)
        # print(f"[ORCHESTRATOR] Risk: {risk_level}")
        
        # --- Layer 4: FSM State & MEANING MEMORY ---
        # Decides: CHECK_IN vs VALIDATION vs INTERVENTION
        session = get_session(session_id)
        
        # 0. Track History (Turn Count for Fix 1)
        session.history.append("user_msg")
        
        # 1. Update Context (Meaning Memory)
        session.update_context(text, signals)
        
        # 2. Update State
        current_state = session.update_state(signals, risk_level, mode=mode)
        # print(f"[ORCHESTRATOR] State: {current_state.value}")
        
        # --- SAFETY TRIGGER (NEW) ---
        if risk_level in ["CRITICAL", "HIGH"]:
             # Retrieve user from DB session if possible
             try:
                 from chatbot.models import ChatSession as DBChatSession
                 from chatbot.utils import send_crisis_email
                 
                 db_session = DBChatSession.objects.filter(session_id=session_id).first()
                 if db_session and db_session.user:
                     send_crisis_email(db_session.user, text)
             except Exception as e:
                 print(f"❌ Error triggering crisis email: {e}")

        # --- Layer 5: Policy ---
        # Decides: CBT vs SUPPORTIVE vs GROUNDING
        # Pass SESSION to allow 'Sticky Policy' logic
        policy = DecisionLayer.select_policy(signals, risk_level, current_state, mode=mode, session=session)
        
        # Save Policy for Sticky Logic next return
        session.current_policy = policy
        
        # print(f"[ORCHESTRATOR] Policy: {policy}")
        
        # --- Layer 6: RAG ---
        # Fetches content if policy needs it
        rag_context = RAGLayer.retrieve(policy, clean_text)
        
        # --- Layer 7: Generation ---
        # Renders the final response (With Context)
        response = self.generation_layer.generate(
            text=clean_text,
            state=current_state.value,
            policy=policy,
            signals=signals,
            rag_context=rag_context,
            mode=mode,
            session=session, # Inject Memory
            history=formatted_history
        )
        
        return response

# Global instance
_orchestrator = Orchestrator()

def process_message(session_id: str, text: str, mode: str = 'friend') -> str:
    return _orchestrator.process_message(session_id, text, mode)
