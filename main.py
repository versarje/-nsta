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
    print("[DEBUG] Pexels karanlık ve estetik dikey duvar kağıtları aranıyor...")
    api_key = os.environ.get("PEXELS_API_KEY")
    
    if not api_key:
        print("[DEBUG UYARI] PEXELS_API_KEY bulunamadı!")
        return None, None

    queries = ["dark aesthetic wallpaper vertical", "moody dark wallpaper 4k", "dark minimalist portrait", "dark shadows wallpaper"]
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

        # İdeal ve Dengeli Font Boyutu (48px - Ekranı kaplamaz)
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

        # Metin blok ölçüleri
        line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 20
        total_text_height = len(lines) * line_height
        
        start_y = (height - total_text_height) / 2

        # Arka plana yarı saydam siyah kutu (Overlay) çizmek için geçici katman
        txt_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_txt = ImageDraw.Draw(txt_layer)

        # Yazının arkasına hafif karanlık, modern bir kutu ekleyelim ki beyaz arka planda bile net okunsun
        box_padding = 40
        max_line_width = max(font.getbbox(l)[2] - font.getbbox(l)[0] for l in lines)
        box_x0 = (width - max_line_width) / 2 - box_padding
        box_y0 = start_y - box_padding
        box_x1 = (width + max_line_width) / 2 + box_padding
        box_y1 = start_y + total_text_height + box_padding

        # Yarı saydam siyah kutu (RGBA: 0,0,0, 160 -> %60 opaklık)
        draw_txt.rounded_rectangle(
            [box_x0, box_y0, box_x1, box_y1], 
            radius=20, 
            fill=(0, 0, 0, 160)
        )

        # Satırları kutunun üzerine yazdır
        y = start_y
        for line in lines:
            bbox = font.getbbox(line)
            w = bbox[2] - bbox[0]
            x = (width - w) / 2
            
            # Yazı rengi saf beyaz
            draw_txt.text((x, y), line, font=font, fill=(255, 255, 255, 255))
            y += line_height

        # Katmanları birleştir
        img = Image.alpha_composite(img, txt_layer)

        output_path = f"output/post_{i + 1}.jpg"
        img.convert("RGB").save(output_path, "JPEG", quality=95)
        print(f"Post kaydedildi: {output_path}")

if __name__ == "__main__":
    generate_posts()
