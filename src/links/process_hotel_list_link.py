import pandas as pd

def process_hotel_detail_link(input_file):
    region = None
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readline()
        region = lines.strip().replace("# Region: ","")
     # Set pandas options to display all content in columns
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_colwidth', None)  # Ensure full content in columns is shown
    #skip 1st row
    hotel_link_df = pd.read_csv(skiprows= 1, filepath_or_buffer=input_file, names=["hotel_id","hotel_link"])
    hotel_link_df = hotel_link_df.dropna()
    #loại bỏ trường searchrequestid trong link
    hotel_link_df['hotel_link'] = hotel_link_df['hotel_link'].apply(lambda x: x.split('&searchrequestid=')[0] if '&searchrequestid=' in x else x)
    

    hotel_link_df.to_csv(f"data/processed/bronze/{region.lower().replace(' ','_')}_hotel_detail_link.csv", index=False)

def process_region_list_link(input_file):
     # Set pandas options to display all content in columns
    region_list_df = pd.read_csv(skiprows=1,filepath_or_buffer=input_file, names=["region_name","region_link"],delimiter="`")
    print("Initial region list dataframe:")
    print(region_list_df)
    region_list_df = region_list_df.dropna()
    region_list_df["region_link"] = region_list_df["region_link"].apply(lambda x : x.split(' '))
    region_list_df = region_list_df.explode("region_link").reset_index(drop=True)
    region_list_df["parameter_list"] = region_list_df["region_link"].apply(lambda x: x.split('?')[1] if '?' in x else '')
    region_list_df = region_list_df.drop('region_link', axis=1)
    region_list_df["parameter_list"] = region_list_df["parameter_list"].apply(lambda x : x.split('&'))
    region_list_df = region_list_df.explode("parameter_list")
    
    region_list_df = region_list_df[region_list_df['parameter_list'].str.contains('ckuid') == False]
    region_list_df = region_list_df[region_list_df['parameter_list'].str.contains('prid') == False]
    region_list_df = region_list_df[region_list_df['parameter_list'].str.contains('guid') == False]
    region_list_df = region_list_df[region_list_df['parameter_list'].str.contains('gclid') == False]
    region_list_df = region_list_df[region_list_df['parameter_list'].str.contains('analyticsSessionId') == False]
    region_list_df = region_list_df[region_list_df['parameter_list'].str.contains('userId') == False]
    

    grouped_region_list_df = region_list_df.groupby(region_list_df.index).agg({
        "region_name": "first",  # Keep the first region name for each group
        "parameter_list": list   # Combine parameter_list into a list
    })
    grouped_region_list_df["parameter_list"] = grouped_region_list_df["parameter_list"].apply(lambda x : '&'.join(x))
    grouped_region_list_df["processed_region_link"] = grouped_region_list_df["parameter_list"].apply(lambda x : f"https://www.agoda.com/vi-vn/search?{x}")
    
    processed_region_list_df = grouped_region_list_df.drop('parameter_list', axis=1)
    print("Processed grouped region list dataframe:")
    print(processed_region_list_df)
    processed_region_list_df.to_csv(path_or_buf=f"data/processed/processed_hotel_list/region_list_link.tsv", index=False,sep='\t')


if __name__ == "__main__":
    process_region_list_link(r"data/raw/region.tsv")