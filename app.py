import requests
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# REST Countries API temel URL'si
API_URL = "https://restcountries.com/v3.1/name/"

# Bilgilerin Türkçe anahtarları
COUNTRY_INFO_KEYS = {
    "name": "Ülke Adı",
    "capital": "Başkent",
    "population": "Nüfus",
    "region": "Bölge",
    "flag_img": "Bayrak Görseli",
    "map_link": "Harita Bağlantısı",
    "currencies": "Para Birimi",
    "languages": "Diller",
    "continent": "Kıta"
}

def clean_country_data(data):
    """
    REST Countries API'den gelen ham veriyi temizler ve istenen formatta düzenler.
    """
    if not data or not isinstance(data, list):
        return None

    # API'den gelen ilk ülke objesini alıyoruz
    country = data[0]

    # Para birimi verisini temizleme
    currencies = country.get('currencies', {})
    currency_list = []
    for code, info in currencies.items():
        currency_list.append(f"{info.get('name', 'N/A')} ({code})")
    
    # Dil verisini temizleme
    languages = country.get('languages', {})
    language_list = list(languages.values())
    
    # Başkent (bazen liste olarak geliyor)
    capital = country.get('capital', ['N/A'])
    if isinstance(capital, list):
        capital = ', '.join(capital)

    # Kıta (bazen liste olarak geliyor)
    continents = country.get('continents', ['N/A'])
    if isinstance(continents, list):
        continent = ', '.join(continents)
    else:
        continent = continents

    # İstenen formatta son veri yapısını oluştur
    cleaned_data = {
        "ülke adı": country.get('name', {}).get('common', 'N/A'),
        "başkent": capital,
        "nüfus": f"{country.get('population', 0):,}".replace(",", "."), # Nüfusu okunabilir formatta göster
        "bölge": country.get('region', 'N/A'),
        "bayrak görseli": country.get('flags', {}).get('svg', ''),
        "harita bağlantısı": country.get('maps', {}).get('googleMaps', '#'),
        "para birimi": ', '.join(currency_list) if currency_list else 'N/A',
        "diller": ', '.join(language_list) if language_list else 'N/A',
        "kıta": continent
    }
    
    return cleaned_data

# Ana sayfa (Frontend'i sunar)
@app.route('/')
def index():
    return render_template('index.html')

# API Endpoint'i: /api/country/<country_name>
@app.route('/api/country/<country_name>', methods=['GET'])
def get_country_info(country_name):
    if not country_name:
        return jsonify({"error": "Lütfen bir ülke adı girin."}), 400

    try:
        # REST Countries API'ye istek gönderme
        response = requests.get(f"{API_URL}{country_name}", timeout=10)
        response.raise_for_status() # Hata durumları (4xx veya 5xx) için istisna fırlatır
        
        data = response.json()
        
        # Eğer API'den hata veya boş sonuç gelirse (örn: "Not Found")
        if response.status_code == 404 or 'status' in data and data['status'] == 404:
            return jsonify({"error": "Ülke Bulunamadı. Lütfen tam ve doğru bir ülke adı girin."}), 404

        # Gelen veriyi temizleyip düzenleme
        country_data = clean_country_data(data)

        if not country_data:
             return jsonify({"error": "Ülke Bulunamadı veya veri formatı beklenenden farklı."}), 404
        
        return jsonify(country_data), 200

    except requests.exceptions.HTTPError as e:
        # 4xx veya 5xx hatalarını yakala
        if e.response.status_code == 404:
            return jsonify({"error": "Ülke Bulunamadı. Lütfen ülke adını kontrol edin."}), 404
        return jsonify({"error": f"API'ye bağlanırken bir hata oluştu: {e}"}), e.response.status_code
        
    except requests.exceptions.RequestException as e:
        # Ağ bağlantısı, timeout vb. hataları yakala
        return jsonify({"error": f"Bir bağlantı hatası oluştu: {e}"}), 503
        
    except Exception as e:
        # Beklenmedik diğer hataları yakala
        return jsonify({"error": f"Beklenmedik bir hata oluştu: {e}"}), 500

if __name__ == '__main__':
    # Geliştirme ortamında çalıştırmak için debug=True ayarı
    app.run(debug=True, host='0.0.0.0', port=5000)
