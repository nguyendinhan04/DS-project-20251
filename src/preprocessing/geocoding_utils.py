import re
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

def clean_address_for_geopy(address):
    """
    Làm sạch và sắp xếp lại địa chỉ theo thứ tự chuẩn:
    [Số nhà] → [Đường] → [Phường/Xã] → [Quận/Huyện] → [Tỉnh/TP] → Vietnam
    
    Args:
        address: Chuỗi địa chỉ thô
        
    Returns:
        tuple: (cleaned_address_string, components_dict)
    """
    if pd.isna(address) or not address:
        return None, {}
    
    # Chuyển sang string và loại bỏ khoảng trắng thừa
    address = str(address).strip()
    
    # Sửa lỗi encoding phổ biến ngay từ đầu
    encoding_fixes = {
        'B nh Dương': 'Bình Dương', 'B nh H a': 'Bình Hòa',
        'Th nh phố': 'Thành phố', 'Th nh Phố': 'Thành phố', 'th nh phố': 'Thành phố',
        'T nh': 'Tỉnh', 'Ph Lợi': 'Phú Lợi', 'Hiệp Th nh': 'Hiệp Thành',
        'Ch nh Nghĩa': 'Chánh Nghĩa', 'Khu d n cư': 'Khu dân cư',
        'Khu dân chư': 'Khu dân cư', 'khu d n cư': 'Khu dân cư', 'khu dan cu': 'Khu dân cư',
        'Hồ Ch Minh': 'Hồ Chí Minh', 'L Duẩn': 'Lê Duẩn', 'c ng nghiệp': 'công nghiệp'
    }
    for wrong, correct in encoding_fixes.items():
        address = address.replace(wrong, correct)

    # Loại bỏ các ký tự đặc biệt không cần thiết (giữ lại dấu phẩy, chấm, số, dấu gạch)
    address = re.sub(r'[^\w\s,. \-()/]', ' ', address)
    
    # Loại bỏ số điện thoại
    address = re.sub(r'\+?\d{8,15}', '', address)
    address = re.sub(r'\b0\d{9,10}\b', '', address)
    
    # Loại bỏ mã bưu điện (5-6 chữ số)
    address = re.sub(r',\s*\d{5,6}(?=\s*,|\s*$)', '', address)
    address = re.sub(r'\s+\d{5,6}\s*,', ',', address)
    
    # Loại bỏ thông tin trong ngoặc đơn (tên khách sạn, tòa nhà)
    address = re.sub(r'\([^)]*(?:Hotel|Motel|Apartment|Building|Residence|Tòa nhà|Khách sạn|Căn hộ|Floor|Tầng|VSIP)[^)]*\)', '', address, flags=re.IGNORECASE)
    
    # Loại bỏ các từ khóa nhiễu ở đầu địa chỉ (tên khu dân cư, housing area, etc.)
    noise_patterns = [
        r'Housing Area [^,]+,', 
        r'Khu dân cư [^,]+,', 
        r'KDC [^,]+,',
        r'Khu phố [^,]+,',
        r'KP [^,]+,',
        r'Hotel [^,]+,'
    ]
    # Chỉ loại bỏ nếu địa chỉ đủ dài (tránh xóa hết thông tin)
    for pat in noise_patterns:
        if len(address.split(',')) > 3:
            address = re.sub(pat, '', address, flags=re.IGNORECASE)

    # Loại bỏ các từ khóa không cần thiết khác
    address = re.sub(r'\b(?:Số|No\.)\s+(\d+[A-Z]?)\s*,', r'\1,', address, flags=re.IGNORECASE)  # Giữ số nhà, bỏ "Số"
    address = re.sub(r'\bLot\s+[A-Z0-9]+\s*,?\s*', '', address, flags=re.IGNORECASE)
    address = re.sub(r'\b(?:Floor|Tầng)\s+\d+\s*,?\s*', '', address, flags=re.IGNORECASE)
    address = re.sub(r'\b\d+\s+tầng\s*,?\s*', '', address, flags=re.IGNORECASE)
    
    # Chuẩn hóa các từ khóa địa chỉ
    address = re.sub(r'\bĐ\.\s*', 'Đường ', address)
    address = re.sub(r'\b(?:P\.|p\.)\s*', 'Phường ', address)
    address = re.sub(r'\b(?:TP\.|Tp\.)\s*', 'Thành phố ', address)
    address = re.sub(r'\bT\.\s*', 'Tỉnh ', address)
    address = re.sub(r'\b(?:Ward|Phường|phường)\b', 'Phường', address, flags=re.IGNORECASE)
    address = re.sub(r'\b(?:Street|Road|Duong|đường)\b', 'Đường', address, flags=re.IGNORECASE)
    address = re.sub(r'\bAvenue\b', 'Đại lộ', address, flags=re.IGNORECASE)
    address = re.sub(r'\b(?:Province|Tỉnh|tỉnh)\b', 'Tỉnh', address, flags=re.IGNORECASE)
    address = re.sub(r'\b(?:Thành phố|thành phố)\b', 'Thành phố', address, flags=re.IGNORECASE)
    address = re.sub(r'\b(?:Vietnam|Viet Nam)\b', 'Việt Nam', address, flags=re.IGNORECASE)
    
    # Tách địa chỉ thành các phần
    parts = [p.strip() for p in address.split(',')]
    parts = [p for p in parts if len(p.strip()) >= 2]
    
    components = {
        'street_number': None,
        'street_name': None,
        'ward': None,
        'district': None,
        'province': None,
        'country': 'Việt Nam'
    }
    
    ward_keywords = ['Phường', 'Xã']
    district_keywords = ['Quận', 'Huyện', 'Thị xã', 'Thành phố']
    province_keywords = ['Tỉnh']
    major_cities = ['Hồ Chí Minh', 'Hà Nội', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ', 'Bà Rịa - Vũng Tàu', 'Bình Dương', 'Đồng Nai', 'Tiền Giang', 'Long An', 'Yên Bái']
    
    seen_parts = set()
    
    for part in parts:
        part_clean = part.strip()
        part_lower = part_clean.lower()
        
        if len(part_clean) < 2 or part_clean in seen_parts:
            continue
        seen_parts.add(part_clean)
        
        if 'việt nam' in part_lower or 'vietnam' in part_lower:
            continue
            
        # Tỉnh/TP trực thuộc TU
        is_province = False
        if any(kw in part for kw in province_keywords) or any(city.lower() in part_lower for city in major_cities):
             if 'bình dương' in part_lower:
                 components['province'] = 'Bình Dương'
                 is_province = True
             elif 'hồ chí minh' in part_lower:
                 components['province'] = 'Hồ Chí Minh'
                 is_province = True
             elif 'bà rịa' in part_lower and ('vũng tàu' in part_lower or 'tỉnh' in part_lower):
                 components['province'] = 'Bà Rịa - Vũng Tàu'
                 is_province = True
             elif not components['province'] and not components['district']: 
                 for city in major_cities:
                     if city.lower() in part_lower:
                         components['province'] = city
                         is_province = True
                         break
        
        if is_province: continue

        # Quận/Huyện
        if any(kw in part for kw in district_keywords) or (components['province'] == 'Bình Dương' and any(d in part for d in ['Thủ Dầu Một', 'Dĩ An', 'Thuận An', 'Bến Cát', 'Tân Uyên'])):
             if not components['district']:
                 components['district'] = part_clean
             continue
             
        # Phường/Xã
        if any(kw in part for kw in ward_keywords):
            if not components['ward']:
                components['ward'] = part_clean
            continue
            
        # Đường
        if 'Đường' in part or 'Đại lộ' in part or 'Street' in part or 'Quốc lộ' in part or 'QL' in part:
             if not components['street_name']:
                 components['street_name'] = part_clean
             continue
             
        # Số nhà/Khác
        if re.match(r'^\d+', part_clean):
             if not components['street_number']:
                 components['street_number'] = part_clean
        elif not components['street_name']:
             components['street_name'] = part_clean

    # Post-processing fixups
    if components['province'] == 'Bà Rịa - Vũng Tàu' and components['district'] == 'Bà Rịa':
         pass
    elif not components['province'] and components['district'] == 'Bà Rịa':
         components['province'] = 'Bà Rịa - Vũng Tàu'
         
    if components['street_number'] and components['street_name'] and not re.match(r'^\d', components['street_name']):
        full_street = f"{components['street_number']} {components['street_name']}"
        components['street_name'] = full_street

    # Reconstruct
    address_parts_ordered = []
    if components['street_name']: address_parts_ordered.append(components['street_name'])
    elif components['street_number']: address_parts_ordered.append(components['street_number'])
    
    if components['ward']: address_parts_ordered.append(components['ward'])
    if components['district']: address_parts_ordered.append(components['district'])
    if components['province']: address_parts_ordered.append(components['province'])
    address_parts_ordered.append(components['country'])
    
    cleaned_address = ', '.join(address_parts_ordered)
    return cleaned_address, components

def get_lat_lng_with_fallback(address_raw, user_agent="hotel_geocoding_app_improved"):
    """
    Geocode with fallback strategy:
    1. Full cleaned address
    2. Street + District + Province
    3. District + Province
    4. Province
    """
    
    geolocator = Nominatim(user_agent=user_agent)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, max_retries=2, error_wait_seconds=5)
    
    cleaned_addr, comps = clean_address_for_geopy(address_raw)
    
    if not cleaned_addr:
        return pd.Series([None, None])

    candidates = []
    candidates.append(cleaned_addr) # 1. Full
    
    # 2. Relaxed: Street + District + Province (No Ward)
    if comps['street_name'] and comps['district'] and comps['province']:
        candidates.append(f"{comps['street_name']}, {comps['district']}, {comps['province']}, Việt Nam")
        
    # 3. District Level
    if comps['district'] and comps['province']:
        candidates.append(f"{comps['district']}, {comps['province']}, Việt Nam")
        
    # 4. Province Level (Last resort)
    if comps['province']:
        candidates.append(f"{comps['province']}, Việt Nam")
        
    # Remove duplicates preserving order
    unique_candidates = []
    for c in candidates:
        if c not in unique_candidates:
            unique_candidates.append(c)
            
    for candidate in unique_candidates:
        try:
            # print(f"Trying: {candidate}") # Debug
            location = geocode(candidate)
            if location:
                return pd.Series([location.latitude, location.longitude])
        except Exception as e:
            print(f"Error geocoding {candidate}: {e}")
            time.sleep(2) # Extra backoff on error
            continue
            
    return pd.Series([None, None])
