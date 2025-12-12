import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS 
import logging

app = Flask(__name__)
CORS(app) # Geliştirme ortamı için CORS etkinleştirildi

# REST Countries API temel URL'si
COUNTRY_API_URL = "https://restcountries.com/v3.1/name/"

country_cache = {}

def clean_country_data(data):
    """Sadece istenen temel verileri temizler ve döndürür."""
    if not data or not isinstance(data, list):
        return None

    country = data[0]

    currencies = country.get('currencies', {})
    currency_list = [f"{info.get('name', 'N/A')} ({code})" for code, info in currencies.items()]
    
    languages = country.get('languages', {})
    language_list = list(languages.values())
    
    capital_list = country.get('capital', ['N/A'])
    capital = capital_list[0] if capital_list and capital_list[0] else 'N/A'
    
    continents = country.get('continents', ['N/A'])
    continent = continents[0] if continents else 'N/A'


    cleaned_data = {
        "ülke adı": country.get('name', {}).get('common', 'N/A'),
        "başkent": capital,
        "nüfus": f"{country.get('population', 0):,}".replace(",", "."), # Okunabilir formatta
        "bölge": country.get('region', 'N/A'),
        "bayrak görseli": country.get('flags', {}).get('svg', ''),
        "harita bağlantısı": country.get('maps', {}).get('googleMaps', '#'),
        "para birimi": ', '.join(currency_list) if currency_list else 'N/A',
        "diller": ', '.join(language_list) if language_list else 'N/A',
        "kıta": continent
    }
    
    return cleaned_data

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
            return jsonify({"error": "Ülke Bulunamadı."}), 404

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
