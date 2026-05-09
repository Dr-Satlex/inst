import fitz  # PyMuPDF
from groq import Groq
import json
import re
import base64

class AkinatorEngine:
    def __init__(self):
        self.client = None
        self.concepts_queue = []
        self.current_concept = None
        self.total_concepts = 0

        self.vision_model = "meta-llama/llama-4-scout-17b-16e-instruct" 
        self.speed_model = "llama-3.1-8b-instant"         

    def set_api_key(self, api_key):
        try:
            self.client = Groq(api_key=api_key)
            return True
        except Exception:
            return False

    def get_pdf_page_count(self, pdf_path):
        try:
            doc = fitz.open(pdf_path)
            count = doc.page_count
            doc.close()
            return count
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return 0

    def extract_images_from_pdf(self, pdf_path, start_page, end_page):
        base64_images = []
        try:
            doc = fitz.open(pdf_path)
            start_idx = max(0, start_page - 1)
            end_idx = min(doc.page_count, end_page)
            
            for i in range(start_idx, end_idx):
                page = doc.load_page(i)
                matrix = fitz.Matrix(2.0, 2.0) 
                pix = page.get_pixmap(matrix=matrix)
                
                img_bytes = pix.tobytes("jpeg")
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                base64_images.append(img_base64)
                
            doc.close()
            return base64_images
        except Exception as e:
            print(f"Image Extraction Error: {e}")
            return []

    def generate_concepts(self, base64_images):
        if not base64_images:
            return False

        # THE FIX: Massively upgraded negative constraints to stop non-medical words.
        prompt_text = """
        Analyze these images of medical/biology textbook pages. Extract a list of the most important testable scientific concepts.
        
        CRITICAL RULES FOR EXTRACTION:
        1. VALID CONCEPTS ONLY: You must only extract strict nouns representing biological, chemical, physical, or medical entities (e.g., 'Mitochondria', 'Myocardial Infarction', 'Action Potential', 'Dopamine').
        2. EXCLUDE JUNK: You MUST NOT extract common English words, verbs, adjectives, publisher names, copyright text, page numbers, or colloquial phrases (e.g., do NOT extract words like 'Hardwired', 'Mechanism', 'Introduction', 'Function', 'Therefore').
        3. DO NOT invent concepts not physically visible in the text or diagrams. 
        4. Return ONLY a raw JSON list of strings. No markdown formatting, no explanations. 
        
        Example Output: ["Subcutaneous Tissue", "Sinoatrial Node", "Photosynthesis"]
        """

        content_payload = [{"type": "text", "text": prompt_text}]
        for img_b64 in base64_images:
            content_payload.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
            })

        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": content_payload}],
                model=self.vision_model,
                temperature=0.0 
            )
            
            raw_output = response.choices[0].message.content.strip()
            match = re.search(r'\[.*\]', raw_output, re.DOTALL)
            if match:
                json_str = match.group(0)
                self.concepts_queue = json.loads(json_str)
                self.total_concepts = len(self.concepts_queue)
                
                if self.total_concepts == 0:
                    return False
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error parsing concepts from Vision model: {e}")
            return False

    def load_next_concept(self, difficulty="Medium"):
        if not self.concepts_queue:
            return None, "All concepts mastered! You beat the selected pages."
            
        self.current_concept = self.concepts_queue.pop(0)
        
        if difficulty == "Easy":
            instruction = "Give a straightforward, textbook-style definition of this concept, but leave out the actual name so the user has to guess it."
        elif difficulty == "Hard":
            instruction = "Create a challenging, highly realistic clinical vignette or investigative case study where this concept is the root cause, diagnosis, or primary mechanism. Do not name the concept. Make the user deduce it from the symptoms/evidence. Ensure the medical logic is flawless."
        else: 
            instruction = "Describe the function, mechanism, or real-world application of this concept creatively. Give a solid clue without making it obvious."

        prompt = f"""
        You are a medical school professor testing a NEET aspirant.
        The secret concept the student needs to guess is: "{self.current_concept}".
        
        INSTRUCTION: {instruction}
        
        Output ONLY the text of the hint/case study. Do not include conversational filler.
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.speed_model,
                temperature=0.7 
            )
            return self.current_concept, response.choices[0].message.content
        except Exception as e:
            return self.current_concept, f"Hint generation failed: {e}"

    def check_guess(self, user_question):
        system_prompt = f"""
        You are a strict game judge for an investigative medical game. 
        The secret concept the user is trying to guess is: "{self.current_concept}".
        
        CRITICAL RULES - YOU MUST ONLY OUTPUT ONE OF THE FOLLOWING EXACT PHRASES:
        1. If the user correctly guesses the concept (or a close synonym), output exactly: WIN
        2. If the user asks a yes/no diagnostic question, output exactly: YES, NO, or IRRELEVANT
        3. If the user asks for a hint, output a new, distinct clinical clue starting exactly with: HINT: 
        4. If the user says "skip", "next", "abort", or "give up", output exactly: SKIP
        5. If the user asks an open-ended question that isn't a guess or yes/no, output exactly: IRRELEVANT

        DO NOT output any conversational text. DO NOT explain what the concept is unless giving a hint.
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ],
                model=self.speed_model,
                temperature=0.0 
            )
            return response.choices[0].message.content.strip().upper()
        except Exception as e:
            return "ERROR"