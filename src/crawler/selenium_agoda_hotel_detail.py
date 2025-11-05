from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import random
from datetime import datetime, timedelta
from selenium_utils import *


def crawl_hotel_detail(file_path):
    driver = get_driver()
    with open(file_path, "r", encoding="utf-8") as f:
        while True:
            line = f.readline()
            if not line:
                break

            hotel_id = line.strip().split(" ")[0].strip()
            hotel_link = line.strip().split(" ")[1].strip()
            #---------------- Sửa thông tin ngày trong link ----------------#
            parsed_url = urlparse(hotel_link)

            query_params = parse_qs(parsed_url.query)
            query_params["checkIn"] = datetime.strftime(datetime.now()+ timedelta(days=2),r"%Y-%m-%d")
            query_params["checkOut"] = datetime.strftime(datetime.now() + timedelta(days=3),r"%Y-%m-%d")
            modified_query = urlencode(query_params, doseq=True)
            hotel_link = urlunparse(parsed_url._replace(query=modified_query))


            #-------------------- Lấy chi tiết khách sạn --------------------#
            print(format_string(f"Crawling hotel ID: {hotel_id}", 50))
            driver.get(hotel_link)

            if driver is None:
                print("Không thể khởi tạo WebDriver.")
                return

            try:

                hotel_name = None
                hotel_address = None
                room_types = []

                try:
                    # kiểm tra nếu tồn tại div[class="RoomGrid-searchTimeOutText"] thì bỏ qua
                    timeout_element = safe_find_element(driver, 'div[class="RoomGrid-searchTimeOutText"]')
                    if timeout_element:
                        print(f"Timeout while searching for rooms in hotel ID {hotel_id}. Skipping...")
                        continue



                    hotel_name_element = safe_find_element(driver, 'h1[data-selenium*= "hotel-header-name"]')
                    if hotel_name_element:
                        hotel_name = hotel_name_element.get_attribute("innerText").strip()

                    hotel_address_element = safe_find_element(driver,'span[data-selenium*="hotel-address-map"]')
                    if hotel_address_element:
                        hotel_address = hotel_address_element.get_attribute("innerText").strip()

                    rooms_types_elements = safe_find_elements_many(driver,'div[class="MasterRoom"]')
                    print('Found room types elements: ', len(rooms_types_elements))
                    for room_type_element in rooms_types_elements:
                        #Loai phong
                        # room_type_name_element = safe_find_element(room_type_element,'div[class="MasterRoom-header"] > div[class*="MasterRoom-headerLeft"] > h4 > button[data-selenium="MasterRoom-headerTitle"] > p > div[class = "MasterRoom-headerTitle--text"] > div:nth-child(1) > span[data-selenium="masterroom-title-name"]')
                        room_type_name_element = safe_find_element(room_type_element,'span[data-selenium="masterroom-title-name"]')
                        if room_type_name_element:
                            room_type_name = room_type_name_element.get_attribute("innerText").strip()

                        #Tien ich di kem
                        amenities = None
                        amenities = safe_find_elements_many(room_type_element,'ul[class = "MasterRoom-amenities"] > li[class="MasterRoom-amenitiesItem"]')
                        if amenities:
                            amenities_list = []
                            for amenity_item in amenities:
                                amenities_type = None
                                amenities_type_element = safe_find_element(amenity_item,'div[data-testid = "amenity-item"] > i')
                                if amenities_type_element:
                                    amenities_type = amenities_type_element.get_attribute("class").replace("ficon ficon-","").replace(" MasterRoom-amenitiesIcon","").strip()
                                amenities_list.append({"amenity" : amenity_item.get_attribute("innerText").strip() , "type": amenities_type})

                        #Gia theo tung option
                        price_option_list = []
                        # price_option_list_elements = safe_find_elements_many(room_type_element,'div[class*="MasterRoom-roomsList"] > div > div[class*="ChildRoomsList-room"]')
                        price_option_list_elements = safe_find_elements_many(room_type_element,'div[class*="MasterRoom"] div[class*="ChildRoomsList-room"][data-element-name = "child-room-item"]')

                        if len(price_option_list_elements) == 0:
                            while True:
                                print("Scrolling to load more price options...")
                                driver.execute_script("window.scrollBy(0, 600);")
                                time.sleep(1)
                                price_option_list_elements = safe_find_elements_many(room_type_element,'div[class*="MasterRoom"] div[class*="ChildRoomsList-room"][data-element-name = "child-room-item"]')
                                if len(price_option_list_elements) > 0 or is_end_of_page(driver):
                                    break

                        print("Found price option elements: ", len(price_option_list_elements))
                        for price_option_element in price_option_list_elements:
                            #Lay gia theo tung option
                            price_option_price = None
                            # price_option_price_element = safe_find_element(price_option_element,'div[class="ChildRoomsList-room-contents"] > div[class="ChildRoomsList-roomCell ChildRoomsList-roomCell-price relativeCell"] > div[class="ChildRoom__PriceContainer"] > div[class="PriceContainer-Top"] > div > div[class="PriceContainer"] > div > div > span[data-selenium="PriceDisplay"] > span:nth-child(2) > strong')
                            # price_option_price_element = safe_find_element(price_option_element,'div[class*="ChildRoomsList-room-contents"] > div[class*="ChildRoomsList-roomCell ChildRoomsList-roomCell-price relativeCell"] > div[class*="ChildRoom__PriceContainer"] > div[class*="PriceContainer-Top"] > div > div[class*="PriceContainer"] > div > div > span[data-selenium="PriceDisplay"]')
                            price_option_price_element = safe_find_element(price_option_element,'span[data-selenium="PriceDisplay"]')
                            



                            if price_option_price_element:
                                print("Found price option price element")
                                price_option_price = price_option_price_element.get_attribute("innerText").strip()
                            
                            #Lay tung option
                            price_option_name = None
                            # price_option_name_element = safe_find_element(price_option_element,'div[class="ChildRoomsList-room-contents"] > div[class="ChildRoomsList-roomCell ChildRoomsList-roomCell-capacity"] > div > div > button')
                            price_option_name_element = safe_find_element(price_option_element,'button[data-selenium="ChildRoomsList-capacity-container"]')
                            if price_option_name_element:
                                print("Found price option name element")
                                price_option_name = price_option_name_element.get_attribute("aria-label").strip()
                            price_option_list.append({"option_name": price_option_name, "option_price": price_option_price})
                        room_types.append({"room_type_name": room_type_name, "amenities": amenities_list,"price_options": price_option_list})
                    print(f"Hotel Name: {hotel_name}")
                    print(f"Hotel Address: {hotel_address}")
                    print(f"Room Types: {room_types}")
                    input("Press Enter to continue...")

                except Exception as e:
                    print(f"Error crawling hotel ID {hotel_id}: {e}")
            except Exception as e:
                print(f"Error accessing hotel link {hotel_link}: {e}")
            finally:
                driver.quit()
                print("DUng lại driver")



    pass


if __name__ == "__main__":
    file_path = r"data/test.csv"  # Thay đổi đường dẫn tới file của bạn

    crawl_hotel_detail(file_path)



    # https://www.agoda.com/vi-vn/sky-hotel-h79351871/hotel/all/ninh-binh-vn.html?countryId=38&finalPriceView=1&isShowMobileAppPrice=false&cid=1844104&numberOfBedrooms=&familyMode=false&adults=2&children=0&rooms=1&maxRooms=0&checkIn=2025-10-26&isCalendarCallout=false&childAges=&numberOfGuest=0&missingChildAges=false&travellerType=1&showReviewSubmissionEntry=false&currencyCode=VND&isFreeOccSearch=false&los=3&searchrequestid=0f33f416-3067-47d0-8fa6-12fe79e987f1
