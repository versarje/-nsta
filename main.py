import json
import os
import random
import requests
import traceback
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

DEFAULT_QUOTES = [
    "İnsan, kendi zihninde kurduğu hapishanenin hem mahkûmu hem de gardiyanıdır.",
    "Herkesin bildiği doğrular, başkaları tarafından yazılmış en büyük senaryolardır.",
    "Sessizlik, zayıflık değil; karşındakinin anlamayacağını bildiğin için verilen en ağır cezadır.",
    "En tehlikeli manipülasyon, sana kendi fikrinmiş gibi hissettirilen yalanlardır.",
    "Yalnızlaşmak bir tercih değil; insanları çözmenin getirdiği kaçınılmaz bir sondur.",
    "Gözler, sadece beynin inanmaya programlandığı gerçeği görür."
]

def fetch_random_pexels_image():
    print("[DEBUG] Pexels API'den görsel çekiliyor...")
    api_key = os.environ.get("PEXELS_API_KEY")
    
    if not api_key:
        print("[DEBUG UYARI] PEXELS_API_KEY bulunamadı!")
        return None

    queries = ["dark aesthetic", "moody shadows", "dark psychology", "mysterious portrait", "dark minimalist"]
    selected_query = random.choice(queries)
    
    url = f"https://api.pexels.com/v1/search?query={selected_query}&orientation=portrait&per_page=15"
    headers = {"Authorization": api_key}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            photos = response.json().get("photos", [])
            if photos:
                photo = random.choice(photos)
                img_url = photo["src"]["large2x"]
                img_response = requests.get(img_url, timeout=10)
                if img_response.status_code == 200:
                    return Image.open(BytesIO(img_response.content)).convert("RGBA")
    except Exception as e:
        print(f"[DEBUG HATA] Pexels hatası: {e}")
        
    return None

def generate_posts():
    if not os.path.exists('output'):
        os.makedirs('output')

    quotes = DEFAULT_QUOTES
    if os.path.exists('input/metinler.json'):
        try:
            with open('input/metinler.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data:
                    quotes = [item["text"] for item in data]
        except Exception as e:
            print(f"[DEBUG HATA] JSON okunamadı: {e}")

    for i in range(3):
        print(f"\n--- Post {i + 1} Üretiliyor ---")
        img = fetch_random_pexels_image()
        if img is None:
            img = Image.new("RGBA", (1080, 1920), (15, 15, 15, 255))
        
        width, height = img.size
        draw = ImageDraw.Draw(img)

        # Linux (Ubuntu) ve yerel ortam için güvenli font yükleme (Büyük boyut: 85)
        font = None
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "arial.ttf"
        ]
        
        for f_path in font_paths:
            try:
                font = ImageFont.truetype(f_path, size=85)
                print(f"[DEBUG] Başarıyla yüklenen font: {f_path}")
                break
            except IOError:
                continue
                
        if font is None:
            print("[DEBUG UYARI] Hiçbir özel font bulunamadı, varsayılan kullanılıyor.")
            font = ImageFont.load_default()

        text = random.choice(quotes)
        
        # Metni satırlara bölme (Genişlik ve okunabilirlik ayarı)
        margin = 100
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

        # Satır aralığı ve dikey/yatay ortalama
        line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 30
        total_text_height = len(lines) * line_height
        y = (height - total_text_height) / 2

        for line in lines:
            bbox = font.getbbox(line)
            w = bbox.get('right', bbox[2] - bbox[0]) if isinstance(bbox, dict) else (bbox[2] - bbox[0])
            x = (width - w) / 2
            
            # Güçlü gölge efekti (Arka planda yazının patlaması için)
            draw.text((x + 5, y + 5), line, font=font, fill=(0, 0, 0, 240))
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
            y += line_height

        output_path = f"output/post_{i + 1}.jpg"
        img.convert("RGB").save(output_path, "JPEG", quality=95)
        print(f"Post kaydedildi: {output_path}")

if __name__ == "__main__":
    generate_posts()
