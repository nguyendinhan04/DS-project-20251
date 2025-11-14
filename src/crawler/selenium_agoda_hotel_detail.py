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
import os
import json
import csv


# get region
def get_region(file_path):
    # get parent directory 'data/processed/processed_hotel_detail_link/Bà Rịa'
    file_path = os.path.normpath(file_path)
    # extract the last part
    region = os.path.basename(os.path.dirname(file_path))
    return region


# create folders to store successed crawled hotel link
def save_region_hotels(region, hotel_details):
    # create file path
    folder_path = os.path.join("data", "crawled", f"{region}")
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"{region}.json")

    # load existing data if file exists
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    # make sure existing_data is a list
    if not isinstance(existing_data, list):
        existing_data = [existing_data]

    # append new hotel_details
    if isinstance(hotel_details, list):
        existing_data.extend(hotel_details)

    # remove duplication
    seen = set()
    unique_hotels = []
    for hotel in existing_data:
        hotel_id = hotel["hotel_id"]
        if hotel_id not in seen:
            seen.add(hotel_id)
            unique_hotels.append(hotel)
    existing_data = unique_hotels

    # save hotel_details dictionary as JSON
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)

    return file_path


# save fail crawled hotel links into seperate folders
def save_failed_hotel_link(region, hotels):
    # create file path
    folder_path = os.path.join("data", "failed", f"{region}")
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"{region}.csv")

    # write list of hotels to CSV
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["hotel_id", "hotel_link"], delimiter=" ")
        writer.writeheader()
        writer.writerows(hotels)

    return file_path


# crawling logic for interface 1
def crawl_interface_1(driver, hotel_link, hotel_id):
    hotel_detail = {}
    hotel_detail["hotel_id"] = hotel_id
    try:
        hotel_name = None
        hotel_address = None
        room_types = []

        try:
            # ignore if div[class='RoomGrid-searchTimeOutText'] exists
            timeout_element = safe_find_element(
                driver, 'div[class="RoomGrid-searchTimeOutText"]'
            )
            if timeout_element:
                print(
                    f"Timeout while searching for rooms in hotel ID {hotel_id}. Skipping..."
                )
                return None

            # get hotel_name
            hotel_name_element = safe_find_element(
                driver, 'h1[data-selenium*= "hotel-header-name"]'
            )
            if hotel_name_element:
                hotel_name = hotel_name_element.get_attribute("innerText").strip()
                hotel_detail["hotel_name"] = hotel_name

            # get hotel_address
            hotel_address_element = safe_find_element(
                driver, 'span[data-selenium*="hotel-address-map"]'
            )
            if hotel_address_element:
                hotel_address = hotel_address_element.get_attribute("innerText").strip()
                hotel_detail["hotel_address"] = hotel_address

            # get room_types detail
            time.sleep(2)
            rooms_types_elements = safe_find_elements_many(
                driver, 'div[class="MasterRoom"]'
            )
            if len(rooms_types_elements) == 0:
                return None
            else:
                print("Found room types elements: ", len(rooms_types_elements))
                for room_type_element in rooms_types_elements:
                    # get name of child room type
                    room_type_name_element = safe_find_element(
                        room_type_element,
                        'span[data-selenium="masterroom-title-name"]',
                    )
                    if room_type_name_element:
                        room_type_name = room_type_name_element.get_attribute(
                            "innerText"
                        ).strip()

                    # get amenities
                    amenities = None
                    amenities = safe_find_elements_many(
                        room_type_element,
                        'ul[class = "MasterRoom-amenities"] > li[class="MasterRoom-amenitiesItem"]',
                    )
                    if amenities:
                        amenities_list = []
                        for amenity_item in amenities:
                            amenities_type = None
                            amenities_type_element = safe_find_element(
                                amenity_item,
                                'div[data-testid = "amenity-item"] > i',
                            )
                            if amenities_type_element:
                                amenities_type = (
                                    amenities_type_element.get_attribute("class")
                                    .replace("ficon ficon-", "")
                                    .replace(" MasterRoom-amenitiesIcon", "")
                                    .strip()
                                )
                            amenities_list.append(
                                {
                                    "amenity": amenity_item.get_attribute(
                                        "innerText"
                                    ).strip(),
                                    "type": amenities_type,
                                }
                            )

                    # get options price
                    price_option_list = []
                    price_option_list_elements = safe_find_elements_many(
                        room_type_element,
                        'div[class*="MasterRoom"] div[class*="ChildRoomsList-room"][data-element-name = "child-room-item"]',
                    )

                    if len(price_option_list_elements) == 0:
                        while True:
                            print("Scrolling to load more price options...")
                            driver.execute_script("window.scrollBy(0, 600);")
                            time.sleep(1)
                            price_option_list_elements = safe_find_elements_many(
                                room_type_element,
                                'div[class*="MasterRoom"] div[class*="ChildRoomsList-room"][data-element-name = "child-room-item"]',
                            )
                            if len(price_option_list_elements) > 0 or is_end_of_page(
                                driver
                            ):
                                break

                    print(
                        "Found price option elements: ",
                        len(price_option_list_elements),
                    )
                    for price_option_element in price_option_list_elements:
                        # get each option price
                        price_option_price = None
                        price_option_price_element = safe_find_element(
                            price_option_element,
                            'span[data-selenium="PriceDisplay"]',
                        )

                        if price_option_price_element:
                            print("Found price option price element")
                            price_option_price = (
                                price_option_price_element.get_attribute(
                                    "innerText"
                                ).strip()
                            )

                        # get each option
                        price_option_name = None
                        price_option_name_element = safe_find_element(
                            price_option_element,
                            'button[data-selenium="ChildRoomsList-capacity-container"]',
                        )
                        if price_option_name_element:
                            print("Found price option name element")
                            price_option_name = price_option_name_element.get_attribute(
                                "aria-label"
                            ).strip()
                        price_option_list.append(
                            {
                                "option_name": price_option_name,
                                "option_price": price_option_price,
                            }
                        )
                    room_types.append(
                        {
                            "room_type_name": room_type_name,
                            "amenities": amenities_list,
                            "price_options": price_option_list,
                        }
                    )
            hotel_detail["room_types"] = room_types

            print(f"Hotel Name: {hotel_name}")
            print(f"Hotel Address: {hotel_address}")
            print(f"Room Types: {room_types}")
            # input("Press Enter to continue...")

        except Exception as e:
            print(f"Error crawling hotel ID {hotel_id}: {e}")
    except Exception as e:
        print(f"Error accessing hotel link {hotel_link}: {e}")
    finally:
        # driver.quit()
        print("Stop driver")
        return hotel_detail


# crawling logic for interface 2
def crawl_interface_2(driver, hotel_link, hotel_id):
    hotel_detail = {}
    hotel_detail["hotel_id"] = hotel_id
    try:
        hotel_name = None
        hotel_address = None
        room_types = []

        try:
            # ignore if div[class='RoomGrid-searchTimeOutText'] exists
            timeout_element = safe_find_element(
                driver, 'div[class="RoomGrid-searchTimeOutText"]'
            )
            if timeout_element:
                print(
                    f"Timeout while searching for rooms in hotel ID {hotel_id}. Skipping..."
                )
                return None

            # get hotel_name
            hotel_name_element = safe_find_element(
                driver, 'h1[data-selenium*="hotel-header-name"]'
            )
            if hotel_name_element:
                hotel_name = hotel_name_element.get_attribute("innerText").strip()
                hotel_detail["hotel_name"] = hotel_name

            # get hotel_address
            hotel_address_element = safe_find_element(
                driver, 'span[data-selenium*="hotel-address-map"]'
            )
            if hotel_address_element:
                hotel_address = hotel_address_element.get_attribute("innerText").strip()
                hotel_detail["hotel_address"] = hotel_address

            # get room_types detail
            time.sleep(2)
            rooms_types_elements = safe_find_elements_many(
                driver, 'div[data-testid="room-item"]'
            )
            if len(rooms_types_elements) == 0:
                return None
            else:
                print("Found room types elements: ", len(rooms_types_elements))
                for room_type_element in rooms_types_elements:
                    # get name of child room type
                    room_type_name_element = safe_find_element(
                        room_type_element,
                        'span[class="sc-dlfnbm Typographystyled__TypographyStyled-sc-1uoovui-0 czBDpX hsiwJn"]',
                    )
                    if room_type_name_element:
                        room_type_name = room_type_name_element.get_attribute(
                            "innerText"
                        ).strip()

                    # get amenities
                    amenities = None
                    amenities = safe_find_elements_many(
                        room_type_element,
                        'span[class="sc-dlfnbm Typographystyled__TypographyStyled-sc-1uoovui-0 eBEczI kLOGfH"]',
                    )

                    # get options
                    option_list = []
                    option_elements = safe_find_elements_many(
                        room_type_element, 'div[data-element-name="mob-room-offer"]'
                    )

                    if len(option_elements) == 0:
                        while True:
                            print("Scrolling to load more price options...")
                            driver.execute_script("window.scrollBy(0, 600);")
                            time.sleep(1)
                            if len(option_elements) > 0 or is_end_of_page(driver):
                                break

                    print("Found option elements: ", len(option_elements))
                    for option_element in option_elements:
                        # get each option price
                        option_price = None
                        option_price_element = safe_find_element(
                            option_element,
                            'span[class="sc-dlfnbm Typographystyled__TypographyStyled-sc-1uoovui-0 eBEczI iwOmxK"]',
                        )

                        if option_price_element:
                            print("Found price option price element")
                            option_price = option_price_element.get_attribute(
                                "innerText"
                            ).strip()

                        # get each option name
                        option_name = None
                        option_name_element = safe_find_element(
                            option_element,
                            'span[class="sc-dlfnbm Typographystyled__TypographyStyled-sc-1uoovui-0 eBEczI gyiEcV"]',
                        )

                        if option_name_element:
                            print("Found option name element")
                            option_name = option_name_element.get_attribute(
                                "innerText"
                            ).strip()
                        option_list.append(
                            {"option_name": option_name, "option_price": option_price}
                        )
                    room_types.append(
                        {
                            "room_type_name": room_type_name,
                            "amenities": amenities,
                            "price_options": option_list,
                        }
                    )
            hotel_detail["room_types"] = room_types

            print(f"Hotel Name: {hotel_name}")
            print(f"Hotel Address: {hotel_address}")
            print(f"Room Types: {room_types}")
            # input("Press Enter to continue...")

        except Exception as e:
            print(f"Error crawling hotel ID {hotel_id}: {e}")

    except Exception as e:
        print(f"Error accessing hotel link {hotel_link}: {e}")
    finally:
        print("Stop driver")
        return hotel_detail


# retry crawling detail from a hotel link several times
def crawl_one_link_with_retry(driver, hotel_link, hotel_id, max_retries=3):
    # delays time for 3 retries consecutive
    delays = [0, 3, 5]

    # delay for 1st attempt
    time.sleep(1)

    # retries loop
    for attempt in range(max_retries):
        # initiate driver
        print(format_string(f"{attempt+1} attempt: Crawling hotel ID: {hotel_id}", 50))
        driver.get(hotel_link)

        if driver is None:
            print(f"Cannot initiate WebDriver in {attempt} attempt")
            continue

        # delay for each attempt
        time.sleep(delays[attempt])

        # extract hotel detail in to dictionary
        # hotel_detail = {}
        # hotel_detail["hotel_id"] = hotel_id
        # try:
        #     hotel_name = None
        #     hotel_address = None
        #     room_types = []

        #     try:
        #         # ignore if div[class='RoomGrid-searchTimeOutText'] exists
        #         timeout_element = safe_find_element(
        #             driver, 'div[class="RoomGrid-searchTimeOutText"]'
        #         )
        #         if timeout_element:
        #             print(
        #                 f"Timeout while searching for rooms in hotel ID {hotel_id}. Skipping..."
        #             )
        #             continue

        #         # get hotel_name
        #         hotel_name_element = safe_find_element(
        #             driver, 'h1[data-selenium*= "hotel-header-name"]'
        #         )
        #         if hotel_name_element:
        #             hotel_name = hotel_name_element.get_attribute("innerText").strip()
        #             hotel_detail["hotel_name"] = hotel_name

        #         # get hotel_address
        #         hotel_address_element = safe_find_element(
        #             driver, 'span[data-selenium*="hotel-address-map"]'
        #         )
        #         if hotel_address_element:
        #             hotel_address = hotel_address_element.get_attribute(
        #                 "innerText"
        #             ).strip()
        #             hotel_detail["hotel_address"] = hotel_address

        #         # get room_types detail
        #         time.sleep(2)
        #         rooms_types_elements = safe_find_elements_many(
        #             driver, 'div[class="MasterRoom"]'
        #         )
        #         if len(rooms_types_elements) == 0:
        #             return
        #         else:
        #             print("Found room types elements: ", len(rooms_types_elements))
        #             for room_type_element in rooms_types_elements:
        #                 # get name of child room type
        #                 room_type_name_element = safe_find_element(
        #                     room_type_element,
        #                     'span[data-selenium="masterroom-title-name"]',
        #                 )
        #                 if room_type_name_element:
        #                     room_type_name = room_type_name_element.get_attribute(
        #                         "innerText"
        #                     ).strip()

        #                 # get amenities
        #                 amenities = None
        #                 amenities = safe_find_elements_many(
        #                     room_type_element,
        #                     'ul[class = "MasterRoom-amenities"] > li[class="MasterRoom-amenitiesItem"]',
        #                 )
        #                 if amenities:
        #                     amenities_list = []
        #                     for amenity_item in amenities:
        #                         amenities_type = None
        #                         amenities_type_element = safe_find_element(
        #                             amenity_item,
        #                             'div[data-testid = "amenity-item"] > i',
        #                         )
        #                         if amenities_type_element:
        #                             amenities_type = (
        #                                 amenities_type_element.get_attribute("class")
        #                                 .replace("ficon ficon-", "")
        #                                 .replace(" MasterRoom-amenitiesIcon", "")
        #                                 .strip()
        #                             )
        #                         amenities_list.append(
        #                             {
        #                                 "amenity": amenity_item.get_attribute(
        #                                     "innerText"
        #                                 ).strip(),
        #                                 "type": amenities_type,
        #                             }
        #                         )

        #                 # get options price
        #                 price_option_list = []
        #                 price_option_list_elements = safe_find_elements_many(
        #                     room_type_element,
        #                     'div[class*="MasterRoom"] div[class*="ChildRoomsList-room"][data-element-name = "child-room-item"]',
        #                 )

        #                 if len(price_option_list_elements) == 0:
        #                     while True:
        #                         print("Scrolling to load more price options...")
        #                         driver.execute_script("window.scrollBy(0, 600);")
        #                         time.sleep(1)
        #                         price_option_list_elements = safe_find_elements_many(
        #                             room_type_element,
        #                             'div[class*="MasterRoom"] div[class*="ChildRoomsList-room"][data-element-name = "child-room-item"]',
        #                         )
        #                         if len(
        #                             price_option_list_elements
        #                         ) > 0 or is_end_of_page(driver):
        #                             break

        #                 print(
        #                     "Found price option elements: ",
        #                     len(price_option_list_elements),
        #                 )
        #                 for price_option_element in price_option_list_elements:
        #                     # get each option price
        #                     price_option_price = None
        #                     price_option_price_element = safe_find_element(
        #                         price_option_element,
        #                         'span[data-selenium="PriceDisplay"]',
        #                     )

        #                     if price_option_price_element:
        #                         print("Found price option price element")
        #                         price_option_price = (
        #                             price_option_price_element.get_attribute(
        #                                 "innerText"
        #                             ).strip()
        #                         )

        #                     # get each option
        #                     price_option_name = None
        #                     price_option_name_element = safe_find_element(
        #                         price_option_element,
        #                         'button[data-selenium="ChildRoomsList-capacity-container"]',
        #                     )
        #                     if price_option_name_element:
        #                         print("Found price option name element")
        #                         price_option_name = (
        #                             price_option_name_element.get_attribute(
        #                                 "aria-label"
        #                             ).strip()
        #                         )
        #                     price_option_list.append(
        #                         {
        #                             "option_name": price_option_name,
        #                             "option_price": price_option_price,
        #                         }
        #                     )
        #                 room_types.append(
        #                     {
        #                         "room_type_name": room_type_name,
        #                         "amenities": amenities_list,
        #                         "price_options": price_option_list,
        #                     }
        #                 )
        #         hotel_detail["room_types"] = room_types

        #         print(f"Hotel Name: {hotel_name}")
        #         print(f"Hotel Address: {hotel_address}")
        #         print(f"Room Types: {room_types}")
        #         # input("Press Enter to continue...")

        #     except Exception as e:
        #         print(f"Error crawling hotel ID {hotel_id}: {e}")
        # except Exception as e:
        #     print(f"Error accessing hotel link {hotel_link}: {e}")
        # finally:
        #     # driver.quit()
        #     print("Stop driver")

        # if crawling with interface 1 is failed, crawl with interface 2
        hotel_detail = crawl_interface_1(driver, hotel_link, hotel_id)
        if hotel_detail == None:
            hotel_detail = crawl_interface_2(driver, hotel_link, hotel_id)

        # retry control
        if not hotel_detail or not hotel_detail.get("room_types"):
            if attempt < max_retries - 1:
                print(f"Retrying in {delays[attempt+1]} seconds.")
                continue
            else:
                print(f"Failed after {max_retries} attempts.")
                return None
        else:
            return hotel_detail


def crawl_hotel_detail(file_path):
    driver = get_driver()
    hotel_details = []
    failed_crawled_hotels = []
    with open(file_path, "r", encoding="utf-8") as f:
        # ignore first row
        line = f.readline()
        while True:
            line = f.readline()
            if not line:
                break

            hotel_id = line.strip().split(" ")[0].strip()
            hotel_link = line.strip().split(" ")[1].strip()
            # ---------------- Sửa thông tin ngày trong link ----------------#
            parsed_url = urlparse(hotel_link)

            query_params = parse_qs(parsed_url.query)
            query_params["checkIn"] = datetime.strftime(
                datetime.now() + timedelta(days=2), r"%Y-%m-%d"
            )
            query_params["checkOut"] = datetime.strftime(
                datetime.now() + timedelta(days=3), r"%Y-%m-%d"
            )
            modified_query = urlencode(query_params, doseq=True)
            hotel_link = urlunparse(parsed_url._replace(query=modified_query))

            # -------------------- Lấy chi tiết khách sạn --------------------#
            hotel_detail = crawl_one_link_with_retry(driver, hotel_link, hotel_id)
            # if hotel_detail has data -> append to hotel_details list, else store hotel_link for crawling later
            if hotel_detail and all(hotel_detail.values()):
                hotel_details.append(hotel_detail)
            else:
                failed_crawled_hotels.append(
                    {"hotel_id": hotel_id, "hotel_link": hotel_link}
                )

    # save successfully exrtacted information + save failed crawled links for later
    region = get_region(file_path)
    save_region_hotels(region, hotel_details)
    save_failed_hotel_link(region, failed_crawled_hotels)
    # driver.quit()

    return hotel_details


if __name__ == "__main__":
    file_path = r"data\processed\processed_hotel_detail_link\Bắc Kạn\hotel_list_Bắc Kạn_part_0.csv"  # Thay đổi đường dẫn tới file của bạn

    crawl_hotel_detail(file_path)

# https://www.agoda.com/vi-vn/sky-hotel-h79351871/hotel/all/ninh-binh-vn.html?countryId=38&finalPriceView=1&isShowMobileAppPrice=false&cid=1844104&numberOfBedrooms=&familyMode=false&adults=2&children=0&rooms=1&maxRooms=0&checkIn=2025-10-26&isCalendarCallout=false&childAges=&numberOfGuest=0&missingChildAges=false&travellerType=1&showReviewSubmissionEntry=false&currencyCode=VND&isFreeOccSearch=false&los=3&searchrequestid=0f33f416-3067-47d0-8fa6-12fe79e987f1
