import pandas as pd
from geocoding_utils import clean_address_for_geopy, get_lat_lng_with_fallback

# Test cases provided by user (failures)
test_data = [
    "73 Đoàn Thị Điểm, Bà Rịa, Việt Nam",
    "Khu dân cư Baria City Gate, Long Huong, Ba Ria - Vung Tau 3, Việt Nam",  # Was NaN
    "QL51, Bà Rịa, Việt Nam",
    "328C, Đại lộ Bình Dương, Hưng Định, Thuận An, Bình Dương, Việt Nam",    # Was NaN
    "153, Hoang Van Thu Đường, Thủ Dầu Một, Bình Dương, Việt Nam",           # Was NaN
    "80, Đường D8, Thủ Dầu Một, Bình Dương, Việt Nam",                       # Was NaN
    "An Dương Vương, Bình Dương, Việt Nam",
    "Housing Area 19-8 Hoa Cuc Phuong - 72C, Dĩ An, Bình Dương, Việt Nam",   # Was NaN
    "10B đại lộ Hữu Nghị, Bình Hòa, cổng VSIP1), Hồ Ch Minh, Việt Nam",      # Was NaN
    "Số 68 Đường L Duẩn, Hồ Ch Minh, Bình Dương, Việt Nam"                   # Was NaN
]

# Raw addresses corresponding to the cleaned ones above (approximation based on context)
# Actually, let's use the RAW addresses from the user's "bad examples" table if possible, 
# but the user provided a mix. Let's use the strings the user provided in the "hotel_address_cleaned" column 
# as the starting point for *our* new cleaning function, OR even better, 
# let's try to simulate the raw input if we can, but testing the cleaning function on the already semi-cleaned strings 
# is also a valid test of the cleaning robustness.

# Better yet, let's copy the RAW addresses from the notebook output I read earlier to be sure.
raw_test_data = [
    "73 Đoàn Thị Điểm, Bà Rịa, Bà Rịa, Việt Nam",
    "KDC Baria City Gate, Long Huong Ward, Ba Ria City, Ba Ria - Vung Tau Province 3, 3, Bà Rịa, Bà Rịa, Việt Nam, 90000",
    "QL51, Bà Rịa, Bà Rịa, Việt Nam",
    "Số 328C, Đại lộ B nh Dương, Khu phố Hưng Lộc, Phường Hưng Định, Th nh phố Thuận An, Tỉnh B nh Dương, Việt Nam, Thuận An, Bình Dương, Việt Nam, 820000",
    "153 Hoang Van Thu Street, Thủ Dầu Một, Bình Dương, Việt Nam, 821779",
    "80 Đ. D8, Chánh Nghĩa, Thủ Dầu Một, Bình Dương, Thủ Dầu Một, Bình Dương, Việt Nam",
    "An Dương Vương, Hòa Phú, L5 L6 An Dương Vương Hòa Phú, Hòa Phú, Bình Dương, Vietnam, Hòa Phú, Bình Dương, Việt Nam",
    "Housing Area 19-8 Hoa Cuc Phuong - 72C, Hoa Cúc Phương - 72C, Dĩ An, Bình Dương, Việt Nam, 75000",
    "10B, đại lộ Hữu Nghị, (khu c ng nghiệp Việt Nam - Singapore, cổng VSIP1), phường B nh H a, th nh phố Hồ Ch Minh, Việt Nam., Thuận An, Bình Dương, Việt Nam, 75000",
    "Số 68 đường L Duẩn, Phường B nh Dương, Th nh phố Hồ Ch Minh, Việt Nam, Hòa Phú, Bình Dương, Việt Nam, 75000"
]

results = []
print(f"{'Raw Address':<50} | {'Cleaned Address':<50} | {'Lat':<10} | {'Lng':<10}")
print("-" * 130)

for raw in raw_test_data:
    cleaned, comps = clean_address_for_geopy(raw)
    lat_lng = get_lat_lng_with_fallback(raw)
    lat = lat_lng[0]
    lng = lat_lng[1]
    
    print(f"{str(raw)[:48]:<50} | {str(cleaned)[:48]:<50} | {str(lat):<10} | {str(lng):<10}")
    results.append({'raw': raw, 'cleaned': cleaned, 'lat': lat, 'lng': lng})

df_results = pd.DataFrame(results)
print("\nSummary:")
print(f"Total: {len(df_results)}")
print(f"Success (found coordinates): {df_results['lat'].notna().sum()}")
