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

def fetch_unique_pexels_image(used_photo_ids):
    print("[DEBUG] Pexels 4K dikey duvar kağıtları aranıyor...")
    api_key = os.environ.get("PEXELS_API_KEY")
    
    if not api_key:
        print("[DEBUG UYARI] PEXELS_API_KEY bulunamadı!")
        return None, None

    # İstediğiniz 4K dikey wallpaper konseptine uygun arama kelimeleri
    queries = ["4k wallpaper vertical", "dark 4k wallpaper", "moody dark aesthetic", "dark mobile wallpaper"]
    selected_query = random.choice(queries)
    
    # Sayfayı aşağı kaydırıyormuş gibi daha geniş bir havuz için per_page değerini yüksek tutuyoruz (örn: 40)
    url = f"https://api.pexels.com/v1/search?query={selected_query}&orientation=portrait&per_page=40"
    headers = {"Authorization": api_key}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            photos = response.json().get("photos", [])
            
            # Daha önce KULLANILMAMIŞ fotoğrafları filtrele (Aynı resmi tekrar kullanmamak için)
            available_photos = [p for p in photos if p["id"] not in used_photo_ids]
            
            if not available_photos:
                available_photos = photos # Liste biterse havuza tekrar izin ver
                
            if available_photos:
                photo = random.choice(available_photos)
                photo_id = photo["id"]
                
                # En yüksek kalitedeki görsel kaynağını alıyoruz
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
        
        # Kesinlikle benzersiz görsel çek
        img, photo_id = fetch_unique_pexels_image(used_photo_ids)
        if photo_id:
            used_photo_ids.add(photo_id) # ID'yi hafızaya at ki bir daha seçilmesin
            
        if img is None:
            img = Image.new("RGBA", (1080, 1920), (15, 15, 15, 255))
        
        width, height = img.size
        draw = ImageDraw.Draw(img)

        # İdeal Font Boyutu (60px - Üst ile orta arasında dengeli ve okunaklı)
        font = None
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "arial.ttf"
        ]
        
        for f_path in font_paths:
            try:
                font = ImageFont.truetype(f_path, size=60)
                break
            except IOError:
                continue
                
        if font is None:
            font = ImageFont.load_default()

        text = selected_quotes[i % len(selected_quotes)]
        
        # Metni satırlara bölme
        margin = 110
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
        line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 25
        total_text_height = len(lines) * line_height
        y = (height - total_text_height) / 2

        for line in lines:
            bbox = font.getbbox(line)
            w = bbox[2] - bbox[0]
            x = (width - w) / 2
            
            # Gölge ve ana yazı
            draw.text((x + 4, y + 4), line, font=font, fill=(0, 0, 0, 230))
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
            y += line_height

        output_path = f"output/post_{i + 1}.jpg"
        img.convert("RGB").save(output_path, "JPEG", quality=95)
        print(f"Post kaydedildi: {output_path}")

if __name__ == "__main__":
    generate_posts()
