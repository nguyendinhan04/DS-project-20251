from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import random
from datetime import datetime
from selenium_utils import *


def crawl_hotel_list(url,region=None):
    driver = get_driver()
    if driver is None:
        print("Không thể khởi tạo WebDriver.")
        return

    driver.get(url)
    time.sleep(20)
    crawl_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    with open(f"output/{crawl_time}.txt", "w", encoding="utf-8") as f:
        f.write(f"# Region: {region}\n")

    try:
        contentContainer = safe_find_element(driver, 'div[id = "contentContainer"]')
        pagination_line = safe_find_element(driver,'span[id="paginationPageCount"]').get_attribute("innerText")
        print(f"pagination_line: {pagination_line}")
        total_pages = int(pagination_line.split(' ')[3])
        current_page = int(pagination_line.split(' ')[1])

        #duyet qua tat ca cac trang
        while current_page < total_pages:
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
                        with open(f"error_log.txt","w",encoding="utf-8") as f:
                            f.write(error_hotel_list_element.get_attribute("innerHTML"))
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
            
            # Ghi danh sách hotel_id ra file sau mỗi trang
            try:
                with open(f"output/{crawl_time}.txt", "a", encoding="utf-8") as f:
                    for hotel_id, hotel_link in hotels_id_list:     
                        f.write(f"{hotel_id}, {hotel_link}\n")
            except Exception as e:
                print(f"Lỗi khi ghi file: {e}")

            time.sleep(random.uniform(5, 15))  # Chờ ngẫu nhiên từ 5 đến 15 giây trước khi chuyển trang tiếp theo
            if current_page % 10 ==0:
                print(format_string("Nghỉ dài hơn sau mỗi 10 trang", 50))
                time.sleep(random.uniform(6, 12))  # Nghỉ dài hơn sau mỗi 10 trang
                

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
    finally:
        driver.quit()
    return hotels_id_list


if __name__ == "__main__":
    url = r"https://www.agoda.com/search?guid=b946eb98-39be-4c6f-bdbc-ce5a5f5af3db&asq=NQVGXW6jsE3tbdY9S%2BqUCpufa9Vwpz6XltTHq4n%2B9gPt6Sc9VYM%2BOtJvOdzFsuZ%2FR3540Dw%2FPKliKXr42QsJdLFCp4UBSEfk9sgyztRQL3Ho1ifkkJKRFygk%2Bspk5G9DK%2Fz%2B8iDeoBw4V4Q3nxNwkQqQMycviD3CIWSJVwpQ8soDVIDBxx2rZh%2BVcp5yQ1YQhEVtH7S5N5TRuYy%2Bg2LTsEHb%2BKC2e3zym6tmyvlzCzM%3D&city=17245&tick=638968609925&locale=en-us&ckuid=9ad60962-bba9-4bba-b472-3bd113b95394&prid=0&gclid=CjwKCAjwmNLHBhA4EiwA3ts3mem8w8e3oa3DkreXLIFWzQsvhzGkRtPaEZq3Sa-osnLh8Su4BTDwQhoCSbYQAvD_BwE&currency=VND&correlationId=23364059-5ec7-43f8-aa8f-a5d443288384&analyticsSessionId=-5756775562513916165&pageTypeId=103&realLanguageId=1&languageId=1&origin=VN&stateCode=HN&cid=1844104&userId=9ad60962-bba9-4bba-b472-3bd113b95394&whitelabelid=1&loginLvl=0&storefrontId=3&currencyId=78&currencyCode=VND&htmlLanguage=en-us&cultureInfoName=en-us&machineName=hk-pc-2f-acm-web-user-6dcf557767-dfx2c&trafficGroupId=1&trafficSubGroupId=84&aid=130589&useFullPageLogin=true&cttp=4&isRealUser=true&mode=production&browserFamily=Chrome&cdnDomain=agoda.net&checkIn=2025-10-26&checkOut=2025-10-29&rooms=1&adults=2&children=0&priceCur=VND&los=3&textToSearch=Ninh+B%C3%ACnh&productType=-1&travellerType=1&familyMode=off&ds=eBjFLNkoDVRqVzyY"

    crawl_hotel_list(url,"Ninh Binh")
    

    