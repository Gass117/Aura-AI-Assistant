from PIL import Image

# Path all'immagine generata
image_path = r"C:\Users\engin\.gemini\antigravity\brain\f66a9565-7935-4c8a-865a-b88947a1c8b7\aura_icon_1776683142540.png"
output_path = r"C:\Users\engin\Desktop\Aura AI Assistant\icon.ico"

try:
    img = Image.open(image_path)
    # Crea l'icona con diverse dimensioni per Windows
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(output_path, format="ICO", sizes=icon_sizes)
    print("Icona creata con successo!")
except Exception as e:
    print(f"Errore: {e}")
