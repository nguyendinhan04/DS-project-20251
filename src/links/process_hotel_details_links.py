from collections import defaultdict
import pandas as pd
import os
import numpy as np
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse



def split_dataframe(df, chunk_size=50):
    """
    Chia DataFrame thành một danh sách các DataFrame nhỏ hơn.

    Tham số:
    - df (pd.DataFrame): DataFrame ban đầu cần chia.
    - chunk_size (int): Số lượng hàng tối đa trong mỗi DataFrame con. Mặc định là 50.

    Trả về:
    - list: Danh sách chứa các DataFrame con.
    """
    # Tính toán các chỉ mục bắt đầu cho mỗi "chunk" (lát cắt)
    # Ví dụ: nếu có 103 hàng, và chunk_size=50, thì các chỉ mục sẽ là: 0, 50, 100
    indices = np.arange(0, len(df), chunk_size)

    # Chia DataFrame dựa trên các chỉ mục đã tính toán
    list_of_dfs = [df.iloc[i:i + chunk_size] for i in indices]

    return list_of_dfs


def process_hotel_details_link(input_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        line = file.readline()
        region_name = line.strip().split(":")[1].strip()
    print(region_name)
    try:
        hotel_link = pd.read_csv(input_file, skiprows = 1, header = None, sep = ' ')
    except pd.errors.EmptyDataError:
        print(f"File {input_file} is empty after skipping the first line.")
        return pd.DataFrame(columns=['hotel_id', 'hotel_link'])
    hotel_link.columns = ['hotel_id', 'hotel_link']
    hotel_link['hotel_id'] = hotel_link['hotel_id'].str.strip().str.replace(',', '').astype(int)
    # print("sau khi bo dau phay")
    # print(hotel_link.head())
    return hotel_link



def parse_link(link):
    if pd.isna(link):
        print("Link is NaN")
        return link
    if isinstance(link, bytes):
        try:
            print("Link is bytes, trying utf-8 decode")
            link = link.decode()
        except Exception:
            link = link.decode('utf-8', 'ignore')
    if not isinstance(link, str):
        link = str(link)


    parsed_url = urlparse(link)
    query_params = parse_qs(parsed_url.query)
    # Loại bỏ các tham số không mong muốn
    unwanted_params = ['searchrequestid']
    for param in unwanted_params:
        query_params.pop(param, None)
    modified_url = urlencode(query_params, doseq=True)
    cleaned_link = urlunparse(parsed_url._replace(query=modified_url))
    return cleaned_link

            
    

        

def main():
    folder_link = r"data/raw/hotel_list"
    # loop through all files in folder_link
    groups = defaultdict(list)
    for filename in os.listdir(folder_link):
        input_file = os.path.join(folder_link, filename)

        region = filename.split("_")[0]
        groups[region].append(input_file)
    for region, files in groups.items():
        df = pd.DataFrame(columns=['hotel_id', 'hotel_link'])
        for input_file in files:
            hotel_link = process_hotel_details_link(input_file)
            df = pd.concat([df, hotel_link], ignore_index=True)
        df = df.drop_duplicates(subset=['hotel_id'])
        df['hotel_link'] = df['hotel_link'].apply(parse_link)
            
        dfs = split_dataframe(df)
        os.makedirs(f"data/processed/processed_hotel_detail_link/{region}", exist_ok=True)
        for i, chunk in enumerate(dfs):
            chunk.to_csv(f"data/processed/processed_hotel_detail_link/{region}/hotel_list_{region}_part_{i}.csv", index=False, sep=' ')
        # break  # chỉ chạy cho region đầu tiên để test
if __name__ == "__main__":
    main()