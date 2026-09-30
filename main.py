import json
import os
import random
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# @motivekaos tarzına uygun örnek vurucu sözler havuzu
DEFAULT_QUOTES = [
    "İnsan zihni, en kusursuz hapishanedir.",
    "Herkesin bildiği doğrular, en büyük illüzyondur.",
    "Yalnızlık, kalabalıkların yarattığı en sessiz çığlıktır.",
    "Gözler, sadece beynin inanmak istediğini görür.",
    "En tehlikeli düşman, kendi zihninde sessizce büyüttüğündür.",
    "Sessizlik, söylenmemiş en ağır intikamdır."
]

def fetch_random_pexels_image():
    # API anahtarını doğrudan sistem ortam değişkeninden alıyoruz
    api_key = os.environ.get("PEXELS_API_KEY")
    
    if not api_key:
        print("Uyarı: PEXELS_API_KEY ortam değişkeni bulunamadı!")
        return None

    queries = ["dark aesthetic", "moody nature", "shadows", "mysterious portrait", "dark minimal"]
    selected_query = random.choice(queries)
    
    url = f"https://api.pexels.com/v1/search?query={selected_query}&orientation=portrait&per_page=15"
    headers = {"Authorization": api_key}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Pexels API Yanıt Kodu: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            photos = data.get("photos", [])
            if photos:
                photo = random.choice(photos)
                img_url = photo["src"]["large2x"]
                
                img_response = requests.get(img_url, timeout=10)
                if img_response.status_code == 200:
                    return Image.open(BytesIO(img_response.content)).convert("RGBA")
        else:
            print(f"Pexels Hatası Detayı: {response.text}")
            
    except Exception as e:
        print(f"Pexels bağlantı hatası oluştu: {e}")
        
    return None

def generate_posts():
    if not os.path.exists('output'):
        os.makedirs('output')

    quotes = DEFAULT_QUOTES
    if os.path.exists('input/metinler.json'):
        with open('input/metinler.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data:
                quotes = [item["text"] for item in data]

    for i in range(3):
        img = fetch_random_pexels_image()
        if img is None:
            # Yedek olarak şık bir karanlık arka plan oluşturuyoruz
            img = Image.new("RGBA", (1080, 1920), (20, 20, 20, 255))
        
        width, height = img.size
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", size=55)
        except IOError:
            font = ImageFont.load_default()

        text = random.choice(quotes)
        
        margin = 120
        max_width = width - (2 * margin)
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            bbox = font.getbbox(test_line)
            if (bbox[2] - bbox[0]) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 20
        total_text_height = len(lines) * line_height
        y = (height - total_text_height) / 2

        for line in lines:
            bbox = font.getbbox(line)
            w = bbox[2] - bbox[0]
            x = (width - w) / 2
            
            draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0, 255))
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
            y += line_height

        output_path = f"output/post_{i + 1}.jpg"
        img.convert("RGB").save(output_path, "JPEG", quality=95)
        print(f"Post hazır: {output_path}")

if __name__ == "__main__":
    generate_posts()
