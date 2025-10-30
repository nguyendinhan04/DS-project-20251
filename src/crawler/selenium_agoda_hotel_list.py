from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import random
from datetime import datetime,timedelta
from selenium_utils import *
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


import os


def execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()  # Record the start time
        result = func(*args, **kwargs)  # Execute the function
        end_time = time.time()  # Record the end time
        print(f"Execution time for '{func.__name__}': {end_time - start_time:.2f} seconds")
        return result
    return wrapper

@execution_time
def crawl_hotel_list(url,region=None):
    driver = get_driver()
    if driver is None:
        print("Không thể khởi tạo WebDriver.")
        return

    driver.get(url)
    time.sleep(20)
    crawl_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    with open(f"data/raw/hotel_list/{region}_{crawl_time}.csv", "w", encoding="utf-8") as f:
        f.write(f"# Region: {region}\n")

    try:
        contentContainer = safe_find_element(driver, 'div[id = "contentContainer"]')
        pagination_line = safe_find_element(driver,'span[id="paginationPageCount"]').get_attribute("innerText")
        print(f"pagination_line: {pagination_line}")
        total_pages = int(pagination_line.split(' ')[3])
        current_page = int(pagination_line.split(' ')[1])

        #duyet qua tat ca cac trang
        while current_page <= total_pages:
            contentContainer = safe_find_element(driver, 'div[id = "contentContainer"]')
            pagination_line = safe_find_element(driver,'span[id="paginationPageCount"]').get_attribute("innerText")
            total_pages = int(pagination_line.split(' ')[3])
            current_page = int(pagination_line.split(' ')[1])


            print(format_string(f"Tổng số trang: {total_pages}, Trang hiện tại: {current_page}", 50))
            hotels_id_list = []


            #-------------------- Phần 1: Lấy danh sách khách sạn ở phần 1--------------------#
            print(format_string("Start part 1", 50))
            hotels_lists = safe_find_elements_many(contentContainer, 'div:nth-child(3) > ol[class="hotel-list-container"]')
            print(f"Số lượng list khách sạn tìm thấy: {len(hotels_lists)}")

            for hotel_list in hotels_lists:
                hotels = safe_find_elements_many(hotel_list, 'li[data-selenium="hotel-item"]')
                print(f"Số lượng khách sạn trong list: {len(hotels)}")
                for hotel in hotels:
                    hotel_id = hotel.get_attribute("data-hotelid")
                    hotel_link_element = safe_find_element(hotel, 'div > a')
                    if hotel_link_element:
                        hotel_link = hotel_link_element.get_attribute("href")
                    hotels_id_list.append(( hotel_id, hotel_link ))

            print(f"Số lượng khách sạn tìm thấy: {len(hotels_id_list)}")


            #-------------------- Phần 2: Lấy danh sách khách sạn ở phần 2 --------------------#
            print(format_string("Start part 2", 50))
            current_hotel_list = safe_find_elements_many(contentContainer, 'div:nth-child(4) > ol > li')
            current_parse = 0
            current_hotel_id = set([])


            while len(hotels_id_list) < 90:
                for hotel in current_hotel_list:
                    try:
                        hotel_id = hotel.get_attribute("data-hotelid")
                    except:
                        print("Lỗi khi lấy hotel_id")
                        error_hotel_list_element = safe_find_element(driver, 'div:nth-child(4) > ol')
                        with open(f"error_log.txt","a",encoding="utf-8") as f:
                            f.write(f"Lỗi khi lấy hotel_id: {region} page {current_page}")
                        continue
                    if hotel_id not in current_hotel_id:
                        hotel_link = safe_find_element(hotel, 'div > a').get_attribute("href")
                        hotels_id_list.append(( hotel_id, hotel_link ))
                        current_hotel_id.add(hotel_id)
                        current_parse += 1

                driver.execute_script("window.scrollBy(0, 1200);")
                time.sleep(2)
                current_hotel_list = safe_find_elements_many(contentContainer, 'div:nth-child(4) > ol > li')

                print(f"Số lượng khách sạn hiện tại: {len(hotels_id_list)}; Số lượng đã parse: {current_parse}")

                if is_end_of_page(driver):
                    print("Reached the end of the page.")
                    break
            
            print(f"Tổng số lượng khách sạn tìm thấy: {len(hotels_id_list)}")


            # Ghi danh sách hotel_id ra file sau mỗi trang
            try:
                with open(f"data/raw/hotel_list/{region}_{crawl_time}.csv", "a", encoding="utf-8") as f:
                    for hotel_id, hotel_link in hotels_id_list:     
                        f.write(f"{hotel_id}, {hotel_link}\n")
            except Exception as e:
                print(f"Lỗi khi ghi file: {e}")


            # Kiểm tra nếu đã đến trang cuối cùng
            if current_page == total_pages:
                print(format_string("Đã đến trang cuối cùng, dừng lại", 50))
                break

            # Nếu chưa phải trang cuối cùng, chuyển sang trang tiếp theo
            next_button = safe_find_element(driver, 'button[id="paginationNext"]')
            if next_button:
                next_button.click()
                time.sleep(5)
            else:
                print(format_string("Không tìm thấy nút 'Next'", 50))
                break
            
            # # Ghi danh sách hotel_id ra file sau mỗi trang
            # try:
            #     with open(f"data/raw/hotel_list/{region}_{crawl_time}.csv", "a", encoding="utf-8") as f:
            #         for hotel_id, hotel_link in hotels_id_list:     
            #             f.write(f"{hotel_id}, {hotel_link}\n")
            # except Exception as e:
            #     print(f"Lỗi khi ghi file: {e}")

            time.sleep(random.uniform(5, 15))  # Chờ ngẫu nhiên từ 5 đến 15 giây trước khi chuyển trang tiếp theo
            if current_page % 5 ==0:
                print(format_string("Nghỉ dài hơn sau mỗi 5 trang", 50))
                time.sleep(random.uniform(15,20))  # Nghỉ dài hơn sau mỗi 10 trang
                

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
    finally:
        driver.quit()
        input("Nhấn Enter để tiếp tục")



if __name__ == "__main__":
    # Ví dụ crawl một vùng cụ thể


    with open("data/processed/region_list_link.tsv","r",encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines[1:]:
            line_element = line.strip().split("\t")  
            region_name = line_element[0]
            if len(line_element) < 2:
                continue
            region_url = line_element[1]

            print(format_string(f"Crawling region: {region_name}", 50))
            print("Region URL:", region_url)


            parsed_url = urlparse(region_url)

            query_params = parse_qs(parsed_url.query)
            query_params["checkIn"] = datetime.strftime(datetime.now(),r"%Y-%m-%d")
            query_params["checkOut"] = datetime.strftime(datetime.now() + timedelta(days=1),r"%Y-%m-%d")

            modified_query = urlencode(query_params, doseq=True) # doseq=True handles list values

            modified_url = urlunparse(parsed_url._replace(query=modified_query))

            crawl_hotel_list(modified_url,region_name)
            time.sleep(random.uniform(40, 60))  # Chờ ngẫu nhiên từ 40 đến 60 giây trước khi chuyển vùng tiếp theo
            
    



