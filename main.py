from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button


class InstpdfApp(App):
    def build(self):
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        self.label = Label(text="Welcome to Instpdf", font_size="28sp")
        button = Button(text="Tap me", size_hint_y=0.3)
        button.bind(on_press=lambda *_: setattr(self.label, "text", "Instpdf runs on Android!"))
        layout.add_widget(self.label)
        layout.add_widget(button)
        return layout


InstpdfApp().run()
