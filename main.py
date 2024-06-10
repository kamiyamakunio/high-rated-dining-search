import requests
import streamlit as st
import folium
from streamlit_folium import folium_static
from dotenv import load_dotenv
import os
import pandas as pd

class Restaurant:
    def __init__(self, name, rating, address, lat, lng):
        self.name = name
        self.rating = rating
        self.address = address
        self.lat = lat
        self.lng = lng

def get_coordinates(address, api_key):
    """
    指定された住所の緯度と経度を取得する関数。

    Parameters:
    address (str): 緯度と経度を取得したい住所
    api_key (str): Google Maps APIキー

    Returns:
    tuple: (緯度, 経度)のタプル

    Raises:
    Exception: 住所が取得できなかった場合に例外を発生させる
    """
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    response = requests.get(geocode_url)
    result = response.json()
    if result["status"] == "OK":
        location = result["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    else:
        raise Exception("住所を取得できませんでした")

def search_nearby_places(lat, lng, api_key, radius=1000, min_rating=4.0, keyword=None, place_type=None):
    """
    指定された緯度と経度を中心に、指定された半径内の評価が高い場所を検索する関数。

    Parameters:
    lat (float): 検索の中心となる場所の緯度
    lng (float): 検索の中心となる場所の経度
    api_key (str): Google Maps APIキー
    radius (int): 検索範囲の半径（メートル）
    min_rating (float): 最低評価値
    keyword (str): 検索クエリのキーワード
    place_type (str): 検索する場所のタイプ

    Returns:
    list: 高評価の場所（Restaurantオブジェクト）のリスト
    """
    places_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&key={api_key}"
    if keyword:
        places_url += f"&keyword={keyword}"
    if place_type:
        places_url += f"&type={place_type}"
    
    response = requests.get(places_url)
    results = response.json().get("results", [])
    
    high_rated_restaurants = [
        Restaurant(
            place.get("name"),
            place.get("rating"),
            place.get("vicinity"),
            place["geometry"]["location"]["lat"],
            place["geometry"]["location"]["lng"]
        )
        for place in results if place.get("rating", 0) >= min_rating
    ]
    return high_rated_restaurants

def main():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        st.error("Google APIキーが設定されていません。.envファイルにGOOGLE_API_KEYを設定してください。")
        return

    st.title("飲食店検索アプリ")
    
    address = st.text_input("検索したい住所を入力してください")
    keyword = st.text_input("キーワードを入力してください（例：焼肉、焼き鳥）")
    place_type = st.selectbox("ジャンルを選択してください（任意）", ["None", "restaurant", "cafe", "bar", "bakery", "meal_takeaway", "shopping_mall", "clothing_store", "book_store", "electronics_store", "furniture_store", "movie_theater", "museum", "night_club", "park", "spa", "hospital", "pharmacy", "school", "library", "police", "airport", "bus_station", "subway_station", "taxi_stand", "train_station"])
    
    if place_type == "None":
        place_type = None
    
    if st.button("検索"):
        if not address:
            st.error("住所を入力してください")
            return
        
        try:
            lat, lng = get_coordinates(address, api_key)
            restaurants = search_nearby_places(lat, lng, api_key, keyword=keyword, place_type=place_type)
            
            if not restaurants:
                st.write("指定された条件に該当する評価4以上の飲食店が見つかりませんでした。")
                return
            
            # 地図の作成
            map_ = folium.Map(location=[lat, lng], zoom_start=15)
            for restaurant in restaurants:
                folium.Marker(
                    [restaurant.lat, restaurant.lng],
                    popup=f"{restaurant.name}\nRating: {restaurant.rating}\nAddress: {restaurant.address}",
                    tooltip=restaurant.name
                ).add_to(map_)
            
            folium_static(map_)

            # テーブルの作成
            restaurant_data = {
                "Name": [restaurant.name for restaurant in restaurants],
                "Rating": [restaurant.rating for restaurant in restaurants]
            }
            df = pd.DataFrame(restaurant_data)
            st.write("検索結果:")
            st.dataframe(df)
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
