import json
import os
import random
import requests
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

def fetch_unique_pexels_image(used_photo_ids):
    print("[DEBUG] Pexels sinematik karanlık dikey görseller aranıyor...")
    api_key = os.environ.get("PEXELS_API_KEY")
    
    if not api_key:
        print("[DEBUG UYARI] PEXELS_API_KEY bulunamadı!")
        return None, None

    queries = ["dark aesthetic wallpaper vertical", "moody dark atmosphere 4k", "dark minimalist cinematic", "dark mystery portrait"]
    selected_query = random.choice(queries)
    
    url = f"https://api.pexels.com/v1/search?query={selected_query}&orientation=portrait&per_page=40"
    headers = {"Authorization": api_key}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            photos = response.json().get("photos", [])
            available_photos = [p for p in photos if p["id"] not in used_photo_ids]
            
            if not available_photos:
                available_photos = photos
                
            if available_photos:
                photo = random.choice(available_photos)
                photo_id = photo["id"]
                img_url = photo["src"]["large2x"]
                
                img_response = requests.get(img_url, timeout=10)
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content)).convert("RGBA")
                    return img, photo_id
    except Exception as e:
        print(f"[DEBUG HATA] Pexels hatası: {e}")
        
    return None, None

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

    used_photo_ids = set()
    selected_quotes = random.sample(quotes, min(3, len(quotes)))

    for i in range(3):
        print(f"\n--- Post {i + 1} Üretiliyor ---")
        
        img, photo_id = fetch_unique_pexels_image(used_photo_ids)
        if photo_id:
            used_photo_ids.add(photo_id)
            
        if img is None:
            img = Image.new("RGBA", (1080, 1920), (15, 15, 15, 255))
        
        width, height = img.size

        # Görselin üzerine hafif bir genel karartma (Vignette / Sinematik Karartma) uygulayalım
        # Bu sayede beyaz/parlak resimler otomatik olarak koyulaşır ve yazı her yerde patlar.
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 90)) # %35 siyah tül perde
        img = Image.alpha_composite(img, overlay)

        draw = ImageDraw.Draw(img)

        # İdeal Font Boyutu (48px - Oldukça dengeli ve estetik)
        font = None
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "arial.ttf"
        ]
        
        for f_path in font_paths:
            try:
                font = ImageFont.truetype(f_path, size=48)
                break
            except IOError:
                continue
                
        if font is None:
            font = ImageFont.load_default()

        text = selected_quotes[i % len(selected_quotes)]
        
        # Metni satırlara bölme
        margin = 130
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

        # Metin blok ölçüleri ve ortalama
        line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 22
        total_text_height = len(lines) * line_height
        y = (height - total_text_height) / 2

        for line in lines:
            bbox = font.getbbox(line)
            w = bbox[2] - bbox[0]
            x = (width - w) / 2
            
            # Harf arkasına kalın gölge (Outline / Drop Shadow efekti)
            # Keskin kutu yerine harflerin arkasındaki bu gölge, yazıyı her türlü arka planda okunur kılar.
            shadow_offset = 3
            for ox in range(-shadow_offset, shadow_offset + 1):
                for oy in range(-shadow_offset, shadow_offset + 1):
                    if ox != 0 or oy != 0:
                        draw.text((x + ox, y + oy), line, font=font, fill=(0, 0, 0, 255))
            
            # Ana saf beyaz yazı
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
            y += line_height

        output_path = f"output/post_{i + 1}.jpg"
        img.convert("RGB").save(output_path, "JPEG", quality=95)
        print(f"Post kaydedildi: {output_path}")

if __name__ == "__main__":
    generate_posts()
