import requests
import logging
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS 

# =========================================================================
# 1. TEMEL YAPILANDIRMA VE SABİTLER
# =========================================================================

app = Flask(__name__)
CORS(app) # Tüm endpoint'ler için CORS'u etkinleştir

# REST Countries API temel URL'si
COUNTRY_API_URL = "https://restcountries.com/v3.1/name/"

# Basit bir önbellekleme mekanizması (Hafızada)
country_cache = {}


# =========================================================================
# 2. YARDIMCI FONKSİYON: VERİ TEMİZLEME
# =========================================================================

def clean_country_data(data):
    """REST Countries API verisini temizler ve gelişmiş frontend için hazırlar."""
    if not data or not isinstance(data, list):
        return None

    country = data[0]

    # --- Veri Çıkarımı ---
    currencies = country.get('currencies', {})
    currency_code = next(iter(currencies.keys()), 'N/A')
    currency_info = currencies.get(currency_code, {})
    currency_name = currency_info.get('name', 'N/A')
    currency_symbol = currency_info.get('symbol', '')
    
    languages = country.get('languages', {})
    language_list = list(languages.values())
    
    capital_list = country.get('capital', ['N/A'])
    capital = capital_list[0] if capital_list and capital_list[0] else 'N/A'
    
    latlng = country.get('latlng', [0, 0])
    
    continent = country.get('continents', ['N/A'])[0]
    
    # --- Dinamik Tema Rengi ---
    theme_color = {
        "Africa": "yellow",
        "Europe": "blue",
        "Asia": "red",
        "Americas": "green",
        "Oceania": "turquoise"
    }.get(continent, "gray")


    # --- İstenen formatta son veri yapısını oluştur ---
    cleaned_data = {
        "ülke adı": country.get('name', {}).get('common', 'N/A'),
        "başkent": capital,
        "nüfus": country.get('population', 0), # CANVAS için sayısal tutuldu
        "bölge": country.get('region', 'N/A'),
        "bayrak görseli": country.get('flags', {}).get('svg', ''),
        "harita bağlantısı": country.get('maps', {}).get('googleMaps', '#'),
        
        # Gelişmiş Alanlar
        "para birimi": f"{currency_name} ({currency_code})",
        "para birimi kısa": currency_code,
        "para birimi sembol": currency_symbol,
        "diller": ', '.join(language_list) if language_list else 'N/A',
        "ana dil": language_list[0] if language_list else 'N/A',
        "kıta": continent,
        "latlng": latlng, 
        "tema rengi": theme_color,
        # Hava durumu alanı kaldırıldı.
    }
    
    return cleaned_data

# =========================================================================
# 3. ROUTE İŞLEMLERİ
# =========================================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/country/<country_name>', methods=['GET'])
def get_country_info(country_name):
    country_name = country_name.strip()
    
    if country_name in country_cache:
        return jsonify(country_cache[country_name]), 200

    try:
        response = requests.get(f"{COUNTRY_API_URL}{country_name}", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if response.status_code == 404 or ('status' in data and data['status'] == 404):
            return jsonify({"error": "Ülke Bulunamadı. Lütfen tam ve doğru bir ülke adı girin."}), 404

        country_data = clean_country_data(data)

        if not country_data:
             return jsonify({"error": "Ülke Bulunamadı veya veri formatı beklenenden farklı."}), 404
        
        country_cache[country_name] = country_data
        
        return jsonify(country_data), 200

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Ülke Bulunamadı. Lütfen ülke adını kontrol edin."}), 404
        return jsonify({"error": f"API'ye bağlanırken bir HTTP hatası oluştu: {e}"}), e.response.status_code
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Bir bağlantı hatası oluştu: {e}"}), 503
        
    except Exception as e:
        return jsonify({"error": f"Beklenmedik bir hata oluştu: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
