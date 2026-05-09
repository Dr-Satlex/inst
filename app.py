import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import json
from engine import AkinatorEngine

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class LearningApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Project Chimera - Investigative Recall Engine")
        # Expanded Window Size
        self.geometry("800x850") 
        
        self.engine = AkinatorEngine()
        self.user_name = ""
        self.config_file = "config.json"
        
        # Default difficulty
        self.difficulty = ctk.StringVar(value="Medium")
        
        self.check_saved_config()

    def check_saved_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    self.user_name = data.get("name", "Investigator")
                    saved_key = data.get("api_key", "")
                    
                    if saved_key and self.engine.set_api_key(saved_key):
                        self.show_upload_screen()
                        return
            except Exception as e:
                print(f"Failed to load config: {e}")
                
        self.show_api_screen()

    def save_config(self, name, api_key):
        try:
            with open(self.config_file, "w") as f:
                json.dump({"name": name, "api_key": api_key}, f)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def show_api_screen(self):
        self.clear_window()
        
        lbl = ctk.CTkLabel(self, text="System Authentication", font=("Arial", 24, "bold"))
        lbl.pack(pady=(200, 20))
        
        self.name_entry = ctk.CTkEntry(self, width=350, height=40, placeholder_text="Enter your Name/Alias")
        self.name_entry.pack(pady=10)
        
        self.api_entry = ctk.CTkEntry(self, width=350, height=40, show="*", placeholder_text="Enter Groq API Key")
        self.api_entry.pack(pady=10)
        
        btn = ctk.CTkButton(self, text="Authenticate & Save", height=40, command=self.authenticate)
        btn.pack(pady=20)

    def authenticate(self):
        name = self.name_entry.get().strip()
        api_key = self.api_entry.get().strip()
        
        if self.engine.set_api_key(api_key):
            self.user_name = name if name else "Investigator"
            self.save_config(self.user_name, api_key)
            self.show_upload_screen()
        else:
            messagebox.showerror("Error", "Invalid API Key or Connection Failed.")

    def show_upload_screen(self):
        self.clear_window()
        
        lbl = ctk.CTkLabel(self, text=f"Welcome, {self.user_name}.", font=("Arial", 24, "bold"))
        lbl.pack(pady=(150, 20))
        
        # Difficulty Selector added to upload screen
        lbl_diff = ctk.CTkLabel(self, text="Select Interrogation Difficulty:")
        lbl_diff.pack(pady=(20, 5))
        
        seg_button = ctk.CTkSegmentedButton(self, values=["Easy", "Medium", "Hard"], variable=self.difficulty)
        seg_button.pack(pady=10)
        
        btn_upload = ctk.CTkButton(self, text="Browse PDF & Extract", width=200, height=40, command=self.process_pdf)
        btn_upload.pack(pady=30)
        
        btn_history = ctk.CTkButton(self, text="View Past Files (Offline)", width=200, height=40, fg_color="gray")
        btn_history.pack(pady=10)
        
        btn_logout = ctk.CTkButton(self, text="Clear Credentials", width=200, fg_color="#c93434", hover_color="#9e2a2a", command=self.logout)
        btn_logout.pack(pady=50)

    def logout(self):
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        self.engine.client = None
        self.show_api_screen()

    def process_pdf(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not filepath:
            return

        total_pages = self.engine.get_pdf_page_count(filepath)
        if total_pages == 0:
            messagebox.showerror("Error", "Could not read the PDF.")
            return

        dialog = ctk.CTkInputDialog(
            text=f"PDF loaded! ({total_pages} pages total)\n\nEnter the page range to study (e.g., 10-15):", 
            title="Select Pages"
        )
        range_input = dialog.get_input()

        if not range_input:
            return 

        try:
            start_str, end_str = range_input.split('-')
            start_page = int(start_str.strip())
            end_page = int(end_str.strip())
        except ValueError:
            messagebox.showerror("Error", "Invalid format. Please use 'Start-End' (e.g., 12-15).")
            return

        lbl_loading = ctk.CTkLabel(self, text=f"Taking high-res scans of pages {start_page} to {end_page}...")
        lbl_loading.pack(pady=10)
        self.update() 
        
        images = self.engine.extract_images_from_pdf(filepath, start_page, end_page)
        
        if self.engine.generate_concepts(images):
            self.show_game_screen()
        else:
            lbl_loading.destroy()
            messagebox.showwarning("No Concepts Found", "The Vision AI could not find any explicit scientific concepts in those images.")

    def show_game_screen(self):
        self.clear_window()
        
        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        self.btn_back = ctk.CTkButton(self.nav_frame, text="← Abort Case", width=80, fg_color="#c93434", hover_color="#9e2a2a", command=self.go_back)
        self.btn_back.pack(side="left")

        # Display current difficulty
        self.lbl_diff_display = ctk.CTkLabel(self.nav_frame, text=f"Difficulty: {self.difficulty.get()}", font=("Arial", 12, "bold"), text_color="#aaaaaa")
        self.lbl_diff_display.pack(side="right")

        self.progress = ctk.CTkProgressBar(self, width=700)
        self.progress.pack(pady=20)
        self.progress.set(0)
        
        self.lbl_progress_text = ctk.CTkLabel(self, text="Files Closed: 0 / " + str(self.engine.total_concepts))
        self.lbl_progress_text.pack()

        # MASSIVELY increased chatbox size and font
        self.chat_box = ctk.CTkTextbox(self, width=700, height=500, state="disabled", font=("Courier", 14), wrap="word")
        self.chat_box.pack(pady=20)

        self.entry_frame = ctk.CTkFrame(self)
        self.entry_frame.pack(pady=10)
        
        self.user_input = ctk.CTkEntry(self.entry_frame, width=550, height=40, placeholder_text="Submit diagnostic guess, ask Yes/No, 'hint', or 'skip'...")
        self.user_input.pack(side="left", padx=10)
        
        self.btn_send = ctk.CTkButton(self.entry_frame, text="Execute", width=100, height=40, command=self.handle_question)
        self.btn_send.pack(side="left")
        
        self.bind('<Return>', lambda event: self.handle_question())

        self.start_new_concept()

    def go_back(self):
        self.engine.concepts_queue = []
        self.engine.total_concepts = 0
        self.show_upload_screen()

    def start_new_concept(self):
        # Pass the difficulty setting to the engine
        concept, hint = self.engine.load_next_concept(difficulty=self.difficulty.get())
        if concept:
            self.log_to_chat(f"SYSTEM: New case file opened.\n\nCASE DETAILS:\n{hint}\n", text_color="#00ffcc")
        else:
            self.log_to_chat(f"SYSTEM: {hint}\n", text_color="#00ffcc")
            self.user_input.configure(state="disabled")

    def handle_question(self):
        question = self.user_input.get()
        if not question: return
        
        self.user_input.delete(0, 'end')
        self.log_to_chat(f"\nINVESTIGATOR: {question}", text_color="#ffffff")
        
        answer = self.engine.check_guess(question)
        
        if answer == "WIN":
            self.log_to_chat("MAINFRAME: DIAGNOSIS CONFIRMED (WIN)\n", text_color="#00ff00")
            self.log_to_chat("-" * 50, text_color="#555555")
            self.update_progress()
            self.start_new_concept()
        elif answer == "SKIP":
            self.log_to_chat(f"MAINFRAME: CASE ABORTED. The correct diagnosis was: {self.engine.current_concept}\n", text_color="#ff5555")
            self.log_to_chat("-" * 50, text_color="#555555")
            self.update_progress()
            self.start_new_concept()
        elif answer.startswith("HINT:"):
            self.log_to_chat(f"MAINFRAME: {answer}\n", text_color="#ffff00")
        else:
            self.log_to_chat(f"MAINFRAME: {answer}\n", text_color="#aaaaaa")

    def update_progress(self):
        completed = self.engine.total_concepts - len(self.engine.concepts_queue)
        progress_val = completed / self.engine.total_concepts if self.engine.total_concepts > 0 else 0
        self.progress.set(progress_val)
        self.lbl_progress_text.configure(text=f"Files Closed: {completed} / {self.engine.total_concepts}")

    def log_to_chat(self, text, text_color="#ffffff"):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", text + "\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = LearningApp()
    app.mainloop()