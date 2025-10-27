import pandas as pd

def main(input_file):
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



if __name__ == "__main__":
    main("src/crawler/output/test.txt")