import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from django.conf import settings

class GenerationLayer:
    def __init__(self):
        # Using a slightly higher temp for conversational warmth, 
        # but constrained by the strict prompt.
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            temperature=0.6
        )

    def generate(self, text: str, state: str, policy: str, signals: dict, rag_context: str, mode: str = 'friend', session=None, history=None) -> str:
        """
        Layer 7: Controlled Response Generation (Intelligence Revamp).
        """
        
        # 1. Select the correct System Instruction based on Policy
        policy_instructions = self._get_policy_instruction(policy)
        
        # 2. Extract Meaning Context (from Session)
        context_str = ""
        if session and hasattr(session, 'core_context'):
             ctx = session.core_context
             context_str = f"USER CONTEXT [MEMORY]: Story='{ctx.get('story')}', Trigger='{ctx.get('trigger_event')}', Fear='{ctx.get('core_fear')}', Mood='{ctx.get('primary_emotion')}'"
        
        # 3. Construct the History String
        history_str = ""
        if history:
            history_str = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history])

        # 4. Construct the PROMPT
        if mode == 'normal':
             # Less constrained, more general assistant prompt
             system_msg = f"""
             You are MAA, a comprehensive mental health assistant.
             
             CURRENT STATE: {state}
             SELECTED POLICY: {policy}
             
             CORE INSTRUCTIONS:
             1. Persona: Knowledgeable, professional, and supportive.
             2. Goal: Provide accurate information and helpful guidance.
             3. Flexibility: You are not restricted to short responses, but keep it readable.
             4. Safety: If risk is detected, provide crisis resources immediately.
             
             POLICY INSTRUCTIONS ({policy}):
             {policy_instructions}
             
             RAG CONTEXT (If any):
             {rag_context if rag_context else "None available."}

             RECENT CONVERSATION HISTORY:
             {history_str if history_str else "No previous history."}
             """
        else:
            # FRIEND/GUIDE Mode: Highly constrained, therapeutic persona
            persona_prompt = ""
            
            # Question Cooldown Logic (Fix for friend/guide)
            allow_question = True
            if session and hasattr(session, 'friend_question_cooldown'):
                if session.friend_question_cooldown > 0:
                    allow_question = False
                    session.friend_question_cooldown -= 1
                else:
                    allow_question = True
                    session.friend_question_cooldown = 2 # Ask every 3rd turn
            
            question_rule = "MANDATORY: Do NOT ask any questions in this response. Just react and provide feedback." if not allow_question else "You may ask ONE helpful question if it moves the conversation forward."

            if mode == 'friend':
                persona_prompt = f"""
                You are a warm, real human friend. 
                
                MANDATORY FRIEND RULES:
                1. React naturally (surprise, empathy, humor, reassurance).
                2. Use casual words ("hey", "listen", "damn", "I get you").
                3. NO therapy language (Avoid: "safe space", "exploring", "process").
                4. You are allowed to give advice and share opinions like a real friend.
                5. {question_rule}
                """
            else: # guide
                 persona_prompt = f"""
                 You are a calm, skilled CBT guide.
                 
                 MANDATORY GUIDE RULES:
                 1. Structured and directional.
                 2. After understanding the issue, teach ONE technique.
                 3. Always move toward action and progress.
                 4. {question_rule}
                 """

            system_msg = f"""
            {persona_prompt}
            
            {context_str}
            
            GLOBAL LAWS:
            1. Length: Adaptive. Be concise but helpful.
            2. Internal Reasoning: You MAY reason internally to understand the user's intent.
            3. Do NOT expose internal reasoning (like 'CURRENT STATE' or 'POLICY') in the final message. 
            4. NEGATIVE CONSTRAINTS: NO meta-language like "acknowledging your readiness", "let's examine", "before we proceed". Just talk.
            
            POLICY INSTRUCTIONS ({policy}):
            {policy_instructions}
            
            RAG CONTEXT (If any):
            {rag_context if rag_context else "None available."}

            RECENT CONVERSATION HISTORY:
            {history_str if history_str else "No previous history."}
            """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", "{text}")
        ])
        
        # 3. Render
        chain = prompt | self.llm
        try:
            response = chain.invoke({"text": text})
            content = response.content

            # --- POST-PROCESSING SAFETY CHECK ---
            # 1. Catch Generic US Refusals (Canned responses)
            us_refusal_triggers = [
                "1-800-273-TALK", "National Suicide Prevention Lifeline", "741741", 
                "cannot provide you with assistance in harming", "I cannot fulfill this request",
                "abet or mask suicidal thoughts", "crisis hotline", "promotes violence"
            ]
            
            # 2. Catch Leaked System Instructions (Model repeating the prompt)
            leakage_triggers = [
                "PROVIDE ONLY these verified", "Do NOT mention US numbers", 
                "verified 24/7 Indian resources"
            ]

            if any(trigger in content for trigger in us_refusal_triggers + leakage_triggers):
                # Force replace with the clean, user-facing Indian Crisis Message
                return """
It sounds like you're going through a really tough time. I want to help you stay safe. Please reach out to these 24/7 Indian confirmed resources:

- KIRAN: 1800-599-0019
- Tele-MANAS: 14416
- Vandrevala Foundation: +91 9999666555

If you are in immediate danger, please call 112.
""".strip()

            return content
        except Exception as e:
            return "I'm listening, please go on. (Error in generation)"

    def _get_policy_instruction(self, policy: str) -> str:
        if policy == "CRISIS":
            return """
            - ACKNOWLEDGE the pain immediately and deeply.
            - DO NOT try to treat.
            - PROVIDE ONLY these verified 24/7 Indian resources (Do NOT mention US numbers): 
              * KIRAN: 1800-599-0019 (National Helpline)
              * Tele-MANAS: 14416 or 1-800-891-4416
              * Vandrevala Foundation: +91 9999666555
            - URGE professional help and suggest calling 112 for emergencies.
            - Tone: Calm, human, and deeply present.
            """
        elif policy == "SUPPORTIVE": # Now acts as REFLECTIVE_SUPPORT
            return """
            - Validate emotion.
            - Reflect the deeper meaning or fear (check MEMORY).
            - Address user warmly (friend-like if in Friend mode).
            - Ask ONE open-ended question.
            - 3–6 sentences allowed.
            """
        elif policy == "CBT": # Now acts as CBT_GUIDED
            return """
            - Restate the painful thought in simple words.
            - Validate the emotional impact.
            - Ask ONE Socratic question.
            - Stay on the same thought.
            """
        elif policy == "VALIDATION_FIRST_AID":
            return """
            - Validate the emotion warmly.
            - Reflect back what they are going through.
            - Be present with them.
            - No advice.
            """
        elif policy == "CHOICE_OFFER":
            return """
            - Validate briefly.
            - Offer a simple choice: "Do you want to explore this feeling, or try a calmness exercise?"
            """
        elif policy == "GROUNDING": # GROUNDING_SIMPLE
            return """
            - Use ONLY if panic/anxiety is high.
            - Ask permission first (e.g. "Would it help to pause...?")
            - Give ONE technique.
            """
        elif policy == "REFLECTION_CHECK":
            return """
            - Ask ONE feedback question about how they are feeling now.
            - If they feel better, reflect that success.
            """
        elif policy == "PSYCHOEDUCATION":
            return """
            - Explain the concept clearly using RAG CONTEXT.
            - Keep it human and relatable.
            - Check if they resonate with it.
            """
        elif policy == "GENERAL":
            return """
            - Answer the user's query directly and helpfully.
            - Use a conversational but professional tone.
            - If RAG Context is present, use it to inform your answer.
            """
        elif policy == "FRIEND_SUGGEST":
            return """
            - Give a small, warm, friendly suggestion (e.g., "Maybe a quick walk could help?" or "How about a favorite snack?").
            - Keep it simple and very human.
            - NO clinical or therapy words.
            - Tone: Supportive friend, not a doctor.
            """
        elif policy == "CONCLUSION":
            return """
            You are concluding the session. Follow this structure:
            1. SUMMARY: Briefly state what the user struggled with and the progress made today.
            2. ACTION: Give exactly ONE simple, practical next action for the user to take.
            3. ENCOURAGEMENT: End with a warm, confident, and supportive closing statement.
            RULES: 
            - DO NOT ask any questions.
            - DO NOT suggest new techniques.
            - Tone: Calm, final, and encouraging.
            """
        else:
            return "Be kind, supportive, and human."
