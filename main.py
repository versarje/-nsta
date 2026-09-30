import json
import os
import random
import requests
import traceback
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# @motivekaos tarzına özel analiz edilmiş varsayılan söz havuzu
DEFAULT_QUOTES = [
    "İnsan, kendi zihninde kurduğu hapishanenin hem mahkûmu hem de gardiyanıdır.",
    "Herkesin bildiği doğrular, başkaları tarafından yazılmış en büyük senaryolardır.",
    "Sessizlik, zayıflık değil; karşındakinin anlamayacağını bildiğin için verilen en ağır cezadır.",
    "En tehlikeli manipülasyon, sana kendi fikrinmiş gibi hissettirilen yalanlardır.",
    "Yalnızlaşmak bir tercih değil; insanları çözmenin getirdiği kaçınılmaz bir sondur.",
    "Gözler, sadece beynin inanmaya programlandığı gerçeği görür."
]

def fetch_random_pexels_image():
    print("[DEBUG] 1. Adım: Pexels API'den görsel çekme fonksiyonu başladı.")
    api_key = os.environ.get("PEXELS_API_KEY")
    
    if not api_key:
        print("[DEBUG UYARI] PEXELS_API_KEY ortam değişkeni bulunamadı!")
        return None

    # @motivekaos tarzı karanlık, estetik ve gizemli arama etiketleri
    queries = ["dark aesthetic", "moody shadows", "dark psychology", "mysterious portrait", "dark minimalist"]
    selected_query = random.choice(queries)
    print(f"[DEBUG] Seçilen Pexels arama terimi: {selected_query}")
    
    url = f"https://api.pexels.com/v1/search?query={selected_query}&orientation=portrait&per_page=15"
    headers = {"Authorization": api_key}
    
    try:
        print("[DEBUG] Pexels API'ye istek atılıyor...")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"[DEBUG] Pexels API Yanıt Kodu: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            photos = data.get("photos", [])
            print(f"[DEBUG] Bulunan fotoğraf sayısı: {len(photos)}")
            if photos:
                photo = random.choice(photos)
                img_url = photo["src"]["large2x"]
                print(f"[DEBUG] Görsel indiriliyor URL: {img_url}")
                
                img_response = requests.get(img_url, timeout=10)
                if img_response.status_code == 200:
                    print("[DEBUG] Görsel başarıyla indirildi ve Pillow formatına çevriliyor.")
                    return Image.open(BytesIO(img_response.content)).convert("RGBA")
        else:
            print(f"[DEBUG HATA] Pexels Hata Detayı: {response.text}")
            
    except Exception as e:
        print(f"[DEBUG HATA] Pexels bağlantı/istek hatası: {e}")
        traceback.print_exc()
        
    return None

def generate_posts():
    print("[DEBUG] Bot ana fonksiyonu (generate_posts) çalıştı.")
    
    if not os.path.exists('output'):
        os.makedirs('output')
        print("[DEBUG] 'output' klasörü oluşturuldu.")

    # Sözlerin yüklenmesi
    quotes = DEFAULT_QUOTES
    if os.path.exists('input/metinler.json'):
        try:
            print("[DEBUG] 'input/metinler.json' dosyası okunuyor...")
            with open('input/metinler.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data:
                    quotes = [item["text"] for item in data]
                    print(f"[DEBUG] JSON dosyasından {len(quotes)} adet söz yüklendi.")
        except Exception as e:
            print(f"[DEBUG HATA] JSON okunurken hata oluştu: {e}")
            traceback.print_exc()
    else:
        print("[DEBUG] 'input/metinler.json' bulunamadı, varsayılan söz havuzu kullanılacak.")

    # Üretim döngüsü (3 adet post üretir)
    for i in range(3):
        print(f"\n--- [DEBUG] Döngü Başlangıcı: Post {i + 1} ---")
        
        # A) Görsel alımı
        img = fetch_random_pexels_image()
        if img is None:
            print("[DEBUG] Pexels görseli alınamadığı için yedek koyu arka plan oluşturuluyor.")
            img = Image.new("RGBA", (1080, 1920), (15, 15, 15, 255))
        
        width, height = img.size
        draw = ImageDraw.Draw(img)

        # B) Font ve Boyut Ayarı (Instagram dikey formatı için ideal boyut: 55)
        try:
            font = ImageFont.truetype("arial.ttf", size=55)
            print("[DEBUG] Özel font (arial.ttf) yüklendi.")
        except IOError:
            print("[DEBUG UYARI] arial.ttf bulunamadı, varsayılan sistem fontu kullanılıyor.")
            font = ImageFont.load_default()

        # C) Söz seçimi
        text = random.choice(quotes)
        print(f"[DEBUG] Seçilen Söz: {text}")
        
        # D) Metin işleme, satırlara bölme ve ortalama
        try:
            margin = 120  # Sağdan ve soldan bırakılacak boşluk payı
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

            line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 25
            total_text_height = len(lines) * line_height
            y = (height - total_text_height) / 2  # Dikey ortalama

            for line in lines:
                bbox = font.getbbox(line)
                w = bbox[2] - bbox[0]
                x = (width - w) / 2  # Yatay ortalama
                
                # Gölge Efekti (Arka planda okunabilirliği artırmak için siyah gölge + beyaz ana yazı)
                draw.text((x + 4, y + 4), line, font=font, fill=(0, 0, 0, 220))  # Gölge
                draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))      # Ana Yazı
                y += line_height
                
            print("[DEBUG] Metin gölgelendirilerek görsel üzerine başarıyla işlendi.")
            
        except Exception as e:
            print(f"[DEBUG HATA] Metin işleme veya çizim sırasında hata oluştu: {e}")
            traceback.print_exc()

        # E) Kayıt aşaması
        try:
            output_path = f"output/post_{i + 1}.jpg"
            img.convert("RGB").save(output_path, "JPEG", quality=95)
            print(f"[DEBUG] Başarılı! Post kaydedildi: {output_path}")
        except Exception as e:
            print(f"[DEBUG HATA] Görsel kaydedilirken hata oluştu: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    generate_posts()
