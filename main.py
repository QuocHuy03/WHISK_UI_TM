import requests
import json
import pandas as pd
import uuid
import base64
import os
from datetime import datetime
from colorama import init, Fore, Style
from tqdm import tqdm
import threading
import time
import sys
import random
import string
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import tkinter as tk
from tkinter import filedialog
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

from auth.auth_guard import check_key_online
API_URL = "http://62.171.131.164:5000"

# Khởi tạo colorama
init(autoreset=True)

# ===== LOGGING CONFIGURATION =====
class LogConfig:
    """Cấu hình logging - có thể bật/tắt các loại log"""
    DEBUG = False  # Bật/tắt log debug chi tiết
    INFO = True    # Bật/tắt log thông tin
    SUCCESS = True # Bật/tắt log thành công
    ERROR = True   # Bật/tắt log lỗi (luôn hiển thị)
    WARNING = True # Bật/tắt log cảnh báo

# Khởi tạo cấu hình log
log_config = LogConfig()

# Thread-safe variables
log_lock = threading.Lock()
progress_lock = threading.Lock()
seed_lock = threading.Lock()
current_seed = 0  # Global seed counter for multi-threading

# ===== BROWSER SIMULATION SETTINGS =====
class BrowserSimulator:
    """Lớp giả lập trình duyệt thật"""
    
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36"
        ]
        self.session = requests.Session()
        self.proxy_config = None
        self._setup_session()
    
    def _setup_session(self):
        """Thiết lập session với retry strategy"""
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def set_proxy(self, proxy_config):
        """Thiết lập proxy cho session"""
        self.proxy_config = proxy_config
        if proxy_config:
            self.session.proxies.update(proxy_config)
            log_success("Đã thiết lập proxy thành công")
        else:
            self.session.proxies.clear()
            log_info("Đã xóa cấu hình proxy")
    
    def get_random_user_agent(self):
        """Lấy User-Agent ngẫu nhiên"""
        return random.choice(self.user_agents)
    
    def get_browser_headers(self):
        """Tạo headers giả lập trình duyệt thật"""
        user_agent = self.get_random_user_agent()
        
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        }
        return headers
    
    def get_api_headers(self, access_token=None, cookie=None):
        """Tạo headers cho API requests"""
        headers = self.get_browser_headers()
        headers.update({
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://labs.google",
            "Referer": "https://labs.google/"
        })
        
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        if cookie:
            headers["Cookie"] = cookie
            
        return headers
    
    def generate_fingerprint(self):
        """Tạo fingerprint giả lập"""
        fingerprint = {
            "screen_resolution": random.choice(["1920x1080", "1366x768", "1440x900", "1536x864"]),
            "timezone": random.choice(["Asia/Ho_Chi_Minh", "Asia/Bangkok", "Asia/Jakarta"]),
            "language": "en-US",
            "platform": "Win32",
            "hardware_concurrency": random.choice([4, 8, 12, 16]),
            "device_memory": random.choice([4, 8, 16, 32])
        }
        return fingerprint
    
    def random_delay(self, min_delay=1, max_delay=3):
        """Delay ngẫu nhiên giữa các request"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        return delay
    
    def make_request(self, method, url, **kwargs):
        """Thực hiện request với giả lập trình duyệt"""
        # Thêm headers giả lập
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        
        # Merge với headers giả lập
        browser_headers = self.get_browser_headers()
        kwargs['headers'].update(browser_headers)
        
        # Thêm proxy nếu có
        if self.proxy_config:
            kwargs['proxies'] = self.proxy_config
        
        # Random delay trước request
        delay = self.random_delay()
        
        try:
            log_debug(f"🔍 make_request:")
            log_debug(f"  - Method: {method}")
            log_debug(f"  - URL: {url}")
            log_debug(f"  - Headers: {kwargs.get('headers', {})}")
            log_debug(f"  - Proxies: {kwargs.get('proxies', 'None')}")
            log_debug(f"  - Timeout: {kwargs.get('timeout', 'None')}")
            
            response = self.session.request(method, url, **kwargs)
            
            log_debug(f"🔍 make_request response:")
            log_debug(f"  - Status: {response.status_code if response else 'None'}")
            log_debug(f"  - Response object: {type(response)}")
            
            # Kiểm tra response có hợp lệ không
            if response is None:
                log_error("Response là None - không có phản hồi từ server")
                return None
            
            # Log thêm thông tin response
            log_debug(f"  - Response headers: {dict(response.headers)}")
            log_debug(f"  - Response text length: {len(response.text) if response.text else 0}")
            
            return response
            
        except requests.exceptions.ProxyError as e:
            log_error(f"Lỗi proxy: {e}")
            log_error("Kiểm tra lại cấu hình proxy trong proxy.txt")
            return None
        except requests.exceptions.Timeout as e:
            log_error(f"Request timeout: {e}")
            log_error("Thử tăng timeout hoặc kiểm tra kết nối mạng")
            return None
        except requests.exceptions.ConnectionError as e:
            log_error(f"Lỗi kết nối: {e}")
            log_error("Kiểm tra kết nối internet và proxy")
            return None
        except requests.exceptions.RequestException as e:
            log_error(f"Lỗi request: {e}")
            return None
        except Exception as e:
            log_error(f"Lỗi không xác định: {e}")
            import traceback
            log_error(f"Chi tiết lỗi: {traceback.format_exc()}")
            return None

# Khởi tạo browser simulator
browser_sim = BrowserSimulator()

def activate_browser_simulation():
    """Kích hoạt các thông số giả lập trình duyệt thật"""
    print("✓ Đã kích hoạt các thông số giả lập trình duyệt thật:")
    print("  - User-Agent ngẫu nhiên")
    print("  - Headers giả lập trình duyệt")
    print("  - Fingerprint giả lập")
    print("  - Retry strategy cho request")
    print("  - Connection pooling")

def log_debug(message):
    """Log debug chi tiết - chỉ hiển thị khi DEBUG = True"""
    if log_config.DEBUG:
        with log_lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{Fore.CYAN}[{timestamp}] {Fore.BLUE}[DEBUG]{Style.RESET_ALL} {message}")

def log_info(message):
    """Log thông tin với thời gian và màu xanh"""
    if log_config.INFO:
        with log_lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{Fore.CYAN}[{timestamp}] {Fore.GREEN}[INFO]{Style.RESET_ALL} {message}")

def log_success(message):
    """Log thành công với thời gian và màu xanh lá"""
    if log_config.SUCCESS:
        with log_lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{Fore.CYAN}[{timestamp}] {Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {message}")

def log_error(message):
    """Log lỗi với thời gian và màu đỏ - luôn hiển thị"""
    with log_lock:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{Fore.CYAN}[{timestamp}] {Fore.RED}[ERROR]{Style.RESET_ALL} {message}")

def log_warning(message):
    """Log cảnh báo với thời gian và màu vàng"""
    if log_config.WARNING:
        with log_lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{Fore.CYAN}[{timestamp}] {Fore.YELLOW}[WARNING]{Style.RESET_ALL} {message}")

def log_user_info(name, email):
    """Log thông tin user với màu đặc biệt"""
    with log_lock:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{Fore.CYAN}[{timestamp}] {Fore.MAGENTA}[USER]{Style.RESET_ALL} {Fore.BLUE}{name}{Style.RESET_ALL} <{Fore.CYAN}{email}{Style.RESET_ALL}>")

class LoadingSpinner:
    """Loading spinner với animation"""
    def __init__(self, message="Loading...", color=Fore.YELLOW):
        self.message = message
        self.color = color
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.running = False
        self.thread = None
    
    def start(self):
        """Bắt đầu spinner"""
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Dừng spinner"""
        self.running = False
        if self.thread:
            self.thread.join()
        # Xóa dòng hiện tại
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
        sys.stdout.flush()
    
    def _spin(self):
        """Animation loop"""
        i = 0
        while self.running:
            sys.stdout.write(f'\r{self.color}{self.spinner_chars[i % len(self.spinner_chars)]}{Style.RESET_ALL} {self.message}')
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

def show_loading(message, duration=2):
    """Hiển thị loading với thời gian cố định"""
    spinner = LoadingSpinner(message, Fore.CYAN)
    spinner.start()
    time.sleep(duration)
    spinner.stop()

def get_thread_count():
    """Lấy số luồng từ user input"""
    print(f"\n{Fore.YELLOW}🧵 Cấu hình số luồng:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Lưu ý:{Style.RESET_ALL} Số luồng cao hơn sẽ tạo ảnh nhanh hơn nhưng có thể gây quá tải server")
    print(f"{Fore.CYAN}Khuyến nghị:{Style.RESET_ALL} 2-5 luồng cho hiệu suất tối ưu")
    
    while True:
        try:
            thread_input = input(f"\n{Fore.GREEN}Nhập số luồng (1-10, mặc định 3): {Style.RESET_ALL}").strip()
            
            if not thread_input:
                return 3  # Mặc định 3 luồng
            
            thread_count = int(thread_input)
            
            if 1 <= thread_count <= 10:
                log_success(f"Đã chọn {thread_count} luồng")
                return thread_count
            else:
                print(f"{Fore.RED}Số luồng phải từ 1 đến 10!{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Vui lòng nhập số nguyên hợp lệ!{Style.RESET_ALL}")

def get_output_folder():
    """Lấy folder output từ user input"""
    print(f"\n{Fore.YELLOW}📁 Chọn folder để lưu ảnh:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}1.{Style.RESET_ALL} Sử dụng folder hiện tại (./)")
    print(f"{Fore.CYAN}2.{Style.RESET_ALL} Tạo folder mới")
    print(f"{Fore.CYAN}3.{Style.RESET_ALL} Nhập đường dẫn folder")
    
    while True:
        choice = input(f"\n{Fore.GREEN}Chọn (1/2/3): {Style.RESET_ALL}").strip()
        
        if choice == "1":
            return "./"
        elif choice == "2":
            folder_name = input(f"{Fore.GREEN}Nhập tên folder mới: {Style.RESET_ALL}").strip()
            if not folder_name:
                folder_name = f"images_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            return folder_name
        elif choice == "3":
            folder_path = input(f"{Fore.GREEN}Nhập đường dẫn folder: {Style.RESET_ALL}").strip()
            return folder_path
        else:
            print(f"{Fore.RED}Lựa chọn không hợp lệ! Vui lòng chọn 1, 2 hoặc 3.{Style.RESET_ALL}")

def create_folder_if_not_exists(folder_path):
    """Tạo folder nếu chưa tồn tại"""
    if not os.path.exists(folder_path):
        try:
            os.makedirs(folder_path, exist_ok=True)
            log_success(f"Đã tạo folder: {folder_path}")
            return True
        except Exception as e:
            log_error(f"Không thể tạo folder {folder_path}: {e}")
            return False
    else:
        log_info(f"Folder đã tồn tại: {folder_path}")
        return True

def read_cookie():
    """Đọc cookie từ file cookie.txt"""
    with open('cookie.txt', 'r', encoding='utf-8') as f:
        return f.read().strip()

def read_proxy():
    """Đọc proxy từ file proxy.txt"""
    try:
        with open('proxy.txt', 'r', encoding='utf-8') as f:
            proxy_line = f.read().strip()
            if not proxy_line:
                return None
            
            # Format: ip:port:username:password
            parts = proxy_line.split(':')
            if len(parts) == 4:
                ip, port, username, password = parts
                proxy_url = f"http://{username}:{password}@{ip}:{port}"
                return {
                    'http': proxy_url,
                    'https': proxy_url
                }
            else:
                log_error("Format proxy không đúng. Cần: ip:port:username:password")
                return None
    except FileNotFoundError:
        log_warning("Không tìm thấy file proxy.txt")
        return None
    except Exception as e:
        log_error(f"Lỗi khi đọc proxy: {e}")
        return None

def test_proxy_connection(proxy_config):
    """Test kết nối proxy"""
    if not proxy_config:
        log_info("Không có proxy để test")
        return True
    
    log_info("🔍 Đang test kết nối proxy...")
    test_urls = [
        "http://httpbin.org/ip",
        "https://httpbin.org/ip",
        "https://www.google.com"
    ]
    
    for url in test_urls:
        try:
            log_info(f"  - Test URL: {url}")
            response = requests.get(url, proxies=proxy_config, timeout=10)
            if response.status_code == 200:
                log_success(f"  ✓ Proxy hoạt động với {url}")
                if "httpbin.org" in url:
                    log_info(f"    IP hiện tại: {response.json().get('origin', 'Unknown')}")
                return True
            else:
                log_warning(f"  ⚠ Proxy trả về status {response.status_code} với {url}")
        except requests.exceptions.ProxyError as e:
            log_error(f"  ✗ Lỗi proxy với {url}: {e}")
        except requests.exceptions.Timeout as e:
            log_error(f"  ✗ Timeout với {url}: {e}")
        except Exception as e:
            log_error(f"  ✗ Lỗi khác với {url}: {e}")
    
    log_error("Proxy không hoạt động với bất kỳ URL nào")
    return False

def get_access_token(cookie):
    """Lấy access_token từ Google Labs API"""
    url = "https://labs.google/fx/api/auth/session"
    headers = browser_sim.get_api_headers(cookie=cookie)
    
    # Hiển thị loading spinner
    spinner = LoadingSpinner("Đang xác thực với Google Labs...", Fore.CYAN)
    spinner.start()
    
    try:
        response = browser_sim.make_request("GET", url, headers=headers, timeout=30)
        spinner.stop()
        
        if response and response.status_code == 200:
            return response.json()
        else:
            if response:
                log_error(f"Lỗi khi lấy access_token: {response.status_code}")
                log_error(response.text)
            return None
    except requests.exceptions.Timeout:
        spinner.stop()
        log_error("Timeout khi kết nối đến Google Labs")
        return None
    except Exception as e:
        spinner.stop()
        log_error(f"Lỗi kết nối: {e}")
        return None

def read_excel_data(excel_file_path='prompt_image.xlsx'):
    """Đọc dữ liệu từ file Excel (STT, PROMPT)"""
    try:
        df = pd.read_excel(excel_file_path)
        stt_list = df.iloc[:, 0].tolist()  # Cột A
        prompt_list = df.iloc[:, 1].tolist()  # Cột B
        return list(zip(stt_list, prompt_list))
    except Exception as e:
        log_error(f"Lỗi khi đọc file Excel: {e}")
        return []

def read_excel_img2img_data(excel_file_path='prompt_image.xlsx'):
    """Đọc dữ liệu từ file Excel cho Image-to-Image (STT, PROMPT, IMAGE_PATH)"""
    try:
        df = pd.read_excel(excel_file_path)
        stt_list = df.iloc[:, 0].tolist()  # Cột A
        prompt_list = df.iloc[:, 1].tolist()  # Cột B
        image_path_list = df.iloc[:, 2].tolist()  # Cột C
        return list(zip(stt_list, prompt_list, image_path_list))
    except Exception as e:
        log_error(f"Lỗi khi đọc file Excel: {e}")
        return []

def generate_image(access_token, prompt, seed, max_retries=3):
    """Gọi API để tạo ảnh với cơ chế retry"""
    url = "https://aisandbox-pa.googleapis.com/v1/whisk:generateImage"
    
    headers = browser_sim.get_api_headers(access_token=access_token)
    
    # Các thông số cố định
    image_model = "IMAGEN_3_5"
    
    for attempt in range(max_retries):
        # Tạo UUID ngẫu nhiên cho workflowId mỗi lần retry
        workflow_id = str(uuid.uuid4())
        
        payload = {
            "clientContext": {
                "workflowId": workflow_id,
                "tool": "BACKBONE",
                "sessionId": f";{uuid.uuid4().int}"
            },
            "imageModelSettings": {
                "imageModel": image_model,
                "aspectRatio": "IMAGE_ASPECT_RATIO_LANDSCAPE"
            },
            "seed": seed,
            "prompt": prompt,
            "mediaCategory": "MEDIA_CATEGORY_BOARD"
        }
        
        # Hiển thị loading spinner
        if attempt == 0:
            spinner = LoadingSpinner("Đang tạo ảnh với AI...", Fore.MAGENTA)
        else:
            spinner = LoadingSpinner(f"Đang tạo ảnh với AI... (Thử lại lần {attempt + 1})", Fore.MAGENTA)
        spinner.start()
        
        try:
            if attempt > 0:
                log_info(f"🔄 Thử lại lần {attempt + 1}/{max_retries}")
                # Delay trước khi retry
                time.sleep(2 * attempt)
            
            log_debug(f"🔍 Đang gọi API generate_image:")
            log_debug(f"  - URL: {url}")
            log_debug(f"  - Payload: {json.dumps(payload, indent=2)}")
            
            response = browser_sim.make_request("POST", url, headers=headers, json=payload, timeout=60)
            spinner.stop()
            
            if response is None:
                log_error("API trả về None - không có kết quả")
                if attempt < max_retries - 1:
                    log_warning(f"Sẽ thử lại sau {2 * (attempt + 1)} giây...")
                    continue
                else:
                    log_error("Có thể do:")
                    log_error("  - Proxy không hoạt động")
                    log_error("  - Kết nối mạng bị lỗi")
                    log_error("  - Server Google Labs không phản hồi")
                    log_error("  - Access token hết hạn")
                    return None
            
            log_debug(f"🔍 API response:")
            log_debug(f"  - Status code: {response.status_code}")
            log_debug(f"  - Headers: {dict(response.headers)}")
            log_debug(f"  - Response text: {response.text[:500]}...")  # Chỉ in 500 ký tự đầu
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    log_debug(f"🔍 JSON response:")
                    log_debug(f"  - Response keys: {list(result.keys()) if result else 'None'}")
                    if 'imagePanels' in result:
                        log_debug(f"  - imagePanels count: {len(result['imagePanels'])}")
                        for i, panel in enumerate(result['imagePanels']):
                            log_debug(f"    Panel {i} keys: {list(panel.keys())}")
                            if 'generatedImages' in panel:
                                log_debug(f"    Panel {i} generatedImages count: {len(panel['generatedImages'])}")
                                for j, img in enumerate(panel['generatedImages']):
                                    log_debug(f"      Image {j} keys: {list(img.keys())}")
                    return result
                except Exception as json_error:
                    log_error(f"Lỗi parse JSON: {json_error}")
                    log_error(f"Response text gốc: {response.text}")
                    if attempt < max_retries - 1:
                        log_warning(f"Sẽ thử lại sau {2 * (attempt + 1)} giây...")
                        continue
                    return None
            elif response.status_code == 401:
                log_error("Lỗi xác thực (401) - Access token có thể đã hết hạn")
                log_error("Vui lòng cập nhật cookie.txt")
                return None
            elif response.status_code == 403:
                log_error("Lỗi quyền truy cập (403) - Có thể bị chặn bởi Google")
                if attempt < max_retries - 1:
                    log_warning("Thử đổi proxy hoặc User-Agent và thử lại...")
                    continue
                else:
                    log_error("Thử đổi proxy hoặc User-Agent")
                    return None
            elif response.status_code == 429:
                log_error("Quá nhiều request (429) - Bị rate limit")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    log_warning(f"Chờ {wait_time} giây rồi thử lại...")
                    time.sleep(wait_time)
                    continue
                else:
                    log_error("Chờ một lúc rồi thử lại")
                    return None
            elif response.status_code >= 500:
                log_error(f"Lỗi server (5xx): {response.status_code}")
                if attempt < max_retries - 1:
                    log_warning("Server Google Labs có thể đang gặp sự cố, thử lại...")
                    continue
                else:
                    log_error("Server Google Labs có thể đang gặp sự cố")
                    return None
            else:
                log_error(f"Lỗi HTTP không xác định: {response.status_code}")
                log_error(f"Response text: {response.text}")
                if attempt < max_retries - 1:
                    log_warning(f"Sẽ thử lại sau {2 * (attempt + 1)} giây...")
                    continue
                return None
        except requests.exceptions.Timeout:
            spinner.stop()
            log_error("Timeout khi tạo ảnh - có thể prompt quá phức tạp")
            if attempt < max_retries - 1:
                log_warning(f"Sẽ thử lại sau {2 * (attempt + 1)} giây...")
                continue
            return None
        except Exception as e:
            spinner.stop()
            log_error(f"Lỗi khi tạo ảnh: {e}")
            if attempt < max_retries - 1:
                log_warning(f"Sẽ thử lại sau {2 * (attempt + 1)} giây...")
                continue
            return None
    
    log_error(f"Đã thử {max_retries} lần nhưng vẫn thất bại")
    return None

def download_image(image_url, filename):
    """Tải xuống ảnh"""
    try:
        # Sử dụng proxy nếu có
        proxies = browser_sim.proxy_config if browser_sim.proxy_config else None
        response = requests.get(image_url, proxies=proxies)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(response.content)
            log_success(f"Đã tải xuống: {filename}")
            return True
    except Exception as e:
        log_error(f"Lỗi khi tải xuống ảnh {filename}: {e}")
    return False

def save_base64_image(base64_data, filename, output_folder="./"):
    """Lưu ảnh từ base64 vào folder được chỉ định"""
    full_path = os.path.join(output_folder, filename)
    
    try:
        # Loại bỏ prefix data:image/jpeg;base64, nếu có
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        image_data = base64.b64decode(base64_data)
        
        with open(full_path, 'wb') as f:
            f.write(image_data)
        
        return True
    except Exception as e:
        log_error(f"Lỗi khi lưu ảnh {full_path}: {e}")
        return False

def upload_image_to_google_labs(cookie, image_path, caption="A hyperrealistic digital illustration depicts a shiny, chrome-like mouse character, standing confidently in a martial arts gi against a subtly rendered, dark background of what appears to be an arena. The character, positioned centrally in the frame, faces forward with a slight tilt of its head to the right. Its body is composed of a highly reflective, polished silver material, giving it a metallic, almost liquid sheen.\n\nThe mouse has large, round ears that match its reflective silver body. Its face is characterized by large, expressive eyes with black pupils surrounded by a thin white iris, and a faint, thin black eyebrow line above each eye. A small, dark triangular nose sits above a tiny, closed mouth. Whiskers, depicted as thin black lines, extend from its cheeks. The overall expression of the mouse is one of determination or seriousness.\n\nIt wears a dark, possibly black or very dark gray, martial arts gi. The gi consists of a wrap-around top with a V-neck opening and wide sleeves, secured at the waist by a tied belt with a knot at the front. The fabric of the gi has visible texture, with distinct lines and shading suggesting folds and creases, giving it a somewhat sketch-like or illustrated appearance in contrast to the smooth, reflective quality of the mouse's skin. The gi extends down to just above its feet. The mouse's feet are clad in simple, low-top white sneakers with dark soles, contrasting with the dark gi.\n\nThe background is dark and desaturated, creating a stark contrast with the shiny character. It suggests the interior of an arena or training dojo, with a circular, slightly elevated platform visible in the foreground where the mouse stands. The background features blurred architectural elements, possibly seating or walls, rendered in shades of dark gray and black. A faint \"SU\" logo, stylized in white, is visible in the upper right corner of the image. The lighting appears to come from the front and slightly above, accentuating the metallic sheen of the mouse and casting subtle shadows."):
    """Upload ảnh lên Google Labs API"""
    url = "https://labs.google/fx/api/trpc/backbone.uploadImage"
    
    headers = browser_sim.get_api_headers(cookie=cookie)
    
    # Đọc ảnh và chuyển thành base64
    try:
        with open(image_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            # Thêm prefix data:image/jpeg;base64,
            base64_string = f"data:image/jpeg;base64,{image_data}"
    except Exception as e:
        log_error(f"Lỗi khi đọc file ảnh {image_path}: {e}")
        return None
    
    # Tạo UUID cho workflowId và sessionId
    workflow_id = str(uuid.uuid4())
    session_id = f";{uuid.uuid4().int}"
    
    payload = {
        "json": {
            "clientContext": {
                "workflowId": workflow_id,
                "sessionId": session_id
            },
            "uploadMediaInput": {
                "mediaCategory": "MEDIA_CATEGORY_SUBJECT",
                "rawBytes": base64_string,
                "caption": caption
            }
        }
    }
    
    # Hiển thị loading spinner
    spinner = LoadingSpinner("Đang upload ảnh lên Google Labs...", Fore.CYAN)
    spinner.start()
    
    try:
        response = browser_sim.make_request("POST", url, headers=headers, json=payload, timeout=60)
        spinner.stop()
        
        if response and response.status_code == 200:
            result = response.json()
            if 'result' in result and 'data' in result['result']:
                upload_data = result['result']['data']['json']['result']
                log_success("Upload ảnh thành công!")
                return {
                    'caption': caption,
                    'uploadMediaGenerationId': upload_data['uploadMediaGenerationId'],
                    'workflowId': workflow_id,
                    'sessionId': session_id
                }
        else:
            if response:
                log_error(f"Lỗi khi upload ảnh: {response.status_code}")
                log_error(response.text)
            return None
    except requests.exceptions.Timeout:
        spinner.stop()
        log_error("Timeout khi upload ảnh")
        return None
    except Exception as e:
        spinner.stop()
        log_error(f"Lỗi khi upload ảnh: {e}")
        return None

def generate_image_from_image(access_token, upload_data, user_instruction, seed):
    """Tạo ảnh từ ảnh đã upload"""
    url = "https://aisandbox-pa.googleapis.com/v1/whisk:runImageRecipe"
    
    headers = browser_sim.get_api_headers(access_token=access_token)
    
    payload = {
        "clientContext": {
            "workflowId": upload_data['workflowId'],
            "tool": "BACKBONE",
            "sessionId": upload_data['sessionId']
        },
        "seed": seed,
        "imageModelSettings": {
            "imageModel": image_model,
            "aspectRatio": "IMAGE_ASPECT_RATIO_LANDSCAPE"
        },
        "userInstruction": user_instruction,
        "recipeMediaInputs": [
            {
                "caption": upload_data.get('caption', ''),
                "mediaInput": {
                    "mediaCategory": "MEDIA_CATEGORY_SUBJECT",
                    "mediaGenerationId": upload_data['uploadMediaGenerationId']
                }
            }
        ]
    }
    
    
    # Hiển thị loading spinner
    spinner = LoadingSpinner("Đang tạo ảnh từ ảnh với AI...", Fore.MAGENTA)
    spinner.start()
    
    try:
        response = browser_sim.make_request("POST", url, headers=headers, json=payload, timeout=60)
        spinner.stop()
        
        if response and response.status_code == 200:
            return response.json()
        else:
            if response:
                log_error(f"Lỗi khi tạo ảnh từ ảnh: {response.status_code}")
                log_error(response.text)
            return None
    except requests.exceptions.Timeout:
        spinner.stop()
        log_error("Timeout khi tạo ảnh từ ảnh")
        return None
    except Exception as e:
        spinner.stop()
        log_error(f"Lỗi khi tạo ảnh từ ảnh: {e}")
        return None

def sanitize_filename(stt_value, prompt_text, max_prompt_length=80):
    """Tạo tên file an toàn cho Windows: STT_PROMPT.jpg"""
    invalid_chars = '\\/:*?"<>|'
    safe = ''.join(
        (ch if (ch.isalnum() or ch in (' ', '-', '_')) and ch not in invalid_chars else '_')
        for ch in str(prompt_text)
    )
    safe = ' '.join(safe.split())  # chuẩn hóa khoảng trắng
    safe = safe.strip(' .')  # bỏ dấu chấm hoặc space ở cuối
    if len(safe) > max_prompt_length:
        safe = safe[:max_prompt_length].rstrip()
    if not safe:
        safe = 'image'
    return f"{stt_value}_{safe}.jpg"

def get_next_seed():
    """Thread-safe function để lấy seed tiếp theo"""
    global current_seed
    with seed_lock:
        seed = current_seed
        current_seed += 1
        return seed

def process_single_image_task(task_data):
    """Xử lý một task tạo ảnh trong thread"""
    stt, prompt, access_token, output_folder = task_data
    
    try:
        # Lấy seed thread-safe
        seed = get_next_seed()
        
        # Gọi API tạo ảnh
        result = generate_image(access_token, prompt, seed)
        
        if result and 'imagePanels' in result:
            for panel_idx, panel in enumerate(result['imagePanels']):
                if 'generatedImages' in panel:
                    for img_idx, img in enumerate(panel['generatedImages']):
                        if 'encodedImage' in img:
                            filename = sanitize_filename(stt, prompt)
                            success = save_base64_image(img['encodedImage'], filename, output_folder)
                            if success:
                                log_success(f"✅ [Thread] Đã lưu thành công: {filename}")
                                return True
                            else:
                                log_error(f"❌ [Thread] Lỗi khi lưu: {filename}")
                                return False
                        else:
                            log_error(f"[Thread] Ảnh {img_idx} không có encodedImage")
                else:
                    log_error(f"[Thread] Panel {panel_idx} không có generatedImages")
        else:
            log_error(f"[Thread] Response không có imagePanels cho STT {stt}")
            return False
            
    except Exception as e:
        log_error(f"[Thread] Lỗi khi xử lý STT {stt}: {e}")
        return False

def process_single_img2img_task(task_data):
    """Xử lý một task tạo ảnh từ ảnh trong thread"""
    stt, prompt, image_path, access_token, cookie, output_folder = task_data
    
    try:
        # Kiểm tra file ảnh có tồn tại không
        if not os.path.exists(image_path):
            log_error(f"[Thread] Không tìm thấy file ảnh: {image_path}")
            return False
        
        # Lấy seed thread-safe
        seed = get_next_seed()
        
        # Upload ảnh lên Google Labs
        log_info(f"[Thread] Đang upload ảnh: {os.path.basename(image_path)}")
        upload_data = upload_image_to_google_labs(cookie, image_path, caption="A hyperrealistic digital illustration depicts a shiny, chrome-like mouse character, standing confidently in a martial arts gi against a subtly rendered, dark background of what appears to be an arena. The character, positioned centrally in the frame, faces forward with a slight tilt of its head to the right. Its body is composed of a highly reflective, polished silver material, giving it a metallic, almost liquid sheen.\n\nThe mouse has large, round ears that match its reflective silver body. Its face is characterized by large, expressive eyes with black pupils surrounded by a thin white iris, and a faint, thin black eyebrow line above each eye. A small, dark triangular nose sits above a tiny, closed mouth. Whiskers, depicted as thin black lines, extend from its cheeks. The overall expression of the mouse is one of determination or seriousness.\n\nIt wears a dark, possibly black or very dark gray, martial arts gi. The gi consists of a wrap-around top with a V-neck opening and wide sleeves, secured at the waist by a tied belt with a knot at the front. The fabric of the gi has visible texture, with distinct lines and shading suggesting folds and creases, giving it a somewhat sketch-like or illustrated appearance in contrast to the smooth, reflective quality of the mouse's skin. The gi extends down to just above its feet. The mouse's feet are clad in simple, low-top white sneakers with dark soles, contrasting with the dark gi.\n\nThe background is dark and desaturated, creating a stark contrast with the shiny character. It suggests the interior of an arena or training dojo, with a circular, slightly elevated platform visible in the foreground where the mouse stands. The background features blurred architectural elements, possibly seating or walls, rendered in shades of dark gray and black. A faint \"SU\" logo, stylized in white, is visible in the upper right corner of the image. The lighting appears to come from the front and slightly above, accentuating the metallic sheen of the mouse and casting subtle shadows.")
        
        if not upload_data:
            log_error(f"[Thread] Không thể upload ảnh: {image_path}")
            return False
        
        # Tạo ảnh từ ảnh
        result = generate_image_from_image(access_token, upload_data, prompt, seed)
        
        if result and 'imagePanels' in result:
            for panel in result['imagePanels']:
                if 'generatedImages' in panel:
                    for img in panel['generatedImages']:
                        if 'encodedImage' in img:
                            filename = sanitize_filename(stt, prompt)
                            success = save_base64_image(img['encodedImage'], filename, output_folder)
                            if success:
                                log_success(f"✅ [Thread] Đã lưu thành công: {filename}")
                                return True
                            else:
                                log_error(f"❌ [Thread] Lỗi khi lưu: {filename}")
                                return False
        else:
            log_error(f"[Thread] Response không có imagePanels cho STT {stt}")
            return False
            
    except Exception as e:
        log_error(f"[Thread] Lỗi khi xử lý STT {stt}: {e}")
        return False


def toggle_debug_mode():
    """Bật/tắt chế độ debug"""
    current_status = "BẬT" if log_config.DEBUG else "TẮT"
    print(f"\n{Fore.YELLOW}🔧 Cấu hình Debug Mode:{Style.RESET_ALL}")
    print(f"Trạng thái hiện tại: {Fore.CYAN}{current_status}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}1.{Style.RESET_ALL} Bật debug (hiển thị log chi tiết)")
    print(f"{Fore.CYAN}2.{Style.RESET_ALL} Tắt debug (chỉ hiển thị lỗi)")
    print(f"{Fore.CYAN}3.{Style.RESET_ALL} Quay lại menu chính")
    
    while True:
        choice = input(f"\n{Fore.GREEN}Chọn (1/2/3): {Style.RESET_ALL}").strip()
        if choice == '1':
            log_config.DEBUG = True
            log_success("Đã bật chế độ debug - sẽ hiển thị log chi tiết")
            return True
        elif choice == '2':
            log_config.DEBUG = False
            log_success("Đã tắt chế độ debug - chỉ hiển thị lỗi và thông tin quan trọng")
            return True
        elif choice == '3':
            return False
        else:
            print(f"{Fore.RED}Lựa chọn không hợp lệ! Vui lòng chọn 1, 2 hoặc 3.{Style.RESET_ALL}")

def show_main_menu(current_excel_file='prompt_image.xlsx'):
    """Hiển thị menu chính"""
    print(f"\n{Fore.YELLOW}🎨 Chọn chế độ tạo ảnh:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}1.{Style.RESET_ALL} Tạo ảnh từ prompt (Excel) - Multi-threading")
    print(f"{Fore.CYAN}2.{Style.RESET_ALL} Tạo ảnh từ Prompt + Image (Image-to-Image) - Multi-threading")
    print(f"{Fore.CYAN}3.{Style.RESET_ALL} Chọn file Excel khác")
    print(f"{Fore.CYAN}4.{Style.RESET_ALL} Cấu hình Debug Mode")
    print(f"{Fore.CYAN}5.{Style.RESET_ALL} Thoát")
    print(f"\n{Fore.MAGENTA}📁 File Excel hiện tại: {Fore.YELLOW}{os.path.basename(current_excel_file)}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}🧵 Hỗ trợ multi-threading để tăng tốc độ tạo ảnh{Style.RESET_ALL}")
    
    while True:
        choice = input(f"\n{Fore.GREEN}Chọn chế độ (1/2/3/4/5): {Style.RESET_ALL}").strip()
        if choice in ['1', '2', '3', '4', '5']:
            return choice
        else:
            print(f"{Fore.RED}Lựa chọn không hợp lệ! Vui lòng chọn 1, 2, 3, 4 hoặc 5.{Style.RESET_ALL}")

def main():
    # Hiển thị ASCII art
    text = r"""
  __        ___     _     _       ____            _    _           
 \ \      / / |__ (_)___| | __  / ___|___   ___ | | _(_) ___  ___ 
  \ \ /\ / /| '_ \| / __| |/ / | |   / _ \ / _ \| |/ / |/ _ \/ __|
   \ V  V / | | | | \__ \   <  | |__| (_) | (_) |   <| |  __/\__ \
    \_/\_/  |_| |_|_|___/_|\_\  \____\___/ \___/|_|\_\_|\___||___/
"""
    print(f"{Fore.YELLOW}{text}{Style.RESET_ALL}")
    
    # Kích hoạt browser simulation
    activate_browser_simulation()
    
    # Hiển thị trạng thái debug mode
    debug_status = "BẬT" if log_config.DEBUG else "TẮT"
    print(f"\n{Fore.CYAN}🔧 Debug Mode: {Fore.YELLOW}{debug_status}{Style.RESET_ALL}")
    if not log_config.DEBUG:
        print(f"{Fore.GREEN}✓ Chế độ tối ưu: Chỉ hiển thị lỗi và thông tin quan trọng{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  (Có thể bật debug trong menu để xem log chi tiết){Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠ Chế độ debug: Sẽ hiển thị tất cả log chi tiết{Style.RESET_ALL}")
    
    # Hiển thị thông tin multi-threading
    print(f"\n{Fore.GREEN}🧵 Multi-threading: {Fore.YELLOW}ĐÃ KÍCH HOẠT{Style.RESET_ALL}")
    print(f"{Fore.CYAN}✓ Hỗ trợ chạy nhiều luồng để tăng tốc độ tạo ảnh{Style.RESET_ALL}")
    print(f"{Fore.CYAN}✓ Thread-safe logging và progress tracking{Style.RESET_ALL}")
    print(f"{Fore.CYAN}✓ Khuyến nghị sử dụng 2-5 luồng cho hiệu suất tối ưu{Style.RESET_ALL}")
    
    # Đọc và thiết lập proxy
    log_info("Đang đọc cấu hình proxy...")
    proxy_config = read_proxy()
    if proxy_config:
        browser_sim.set_proxy(proxy_config)
        # Test kết nối proxy
        if not test_proxy_connection(proxy_config):
            log_warning("Proxy không hoạt động tốt, có thể gây lỗi khi tạo ảnh")
            choice = input("Bạn có muốn tiếp tục không? (y/n): ").strip().lower()
            if choice not in ['y', 'yes']:
                log_info("Thoát chương trình")
                return
    else:
        log_info("Không sử dụng proxy")
    
    # Đọc config
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    seed = config.get('seed', 0)
    global image_model
    image_model = config.get('imageModel', 'IMAGEN_3_5')
    
    # Lấy access_token
    log_info("Đang lấy access_token...")
    cookie = read_cookie()
    access_data = get_access_token(cookie)
    
    if not access_data or not access_data.get('access_token'):
        log_error("Không thể lấy access_token. Dừng chương trình.")
        return
    
    user_info = access_data.get('user', {})
    log_success("Đã lấy access_token thành công!")
    log_user_info(user_info.get('name', 'Unknown'), user_info.get('email', 'Unknown'))

    access_token = access_data.get('access_token')
    
    # Biến lưu trữ file Excel được chọn
    selected_excel_file = 'prompt_image.xlsx'  # File mặc định
    
    # Hiển thị menu chính
    while True:
        choice = show_main_menu(selected_excel_file)
        
        if choice == '1':
            # Chế độ tạo ảnh từ prompt (Excel)
            excel_mode(access_token, seed, selected_excel_file)
        elif choice == '2':
            # Chế độ tạo ảnh từ Excel + Ảnh
            excel_img2img_mode(access_token, cookie, seed, selected_excel_file)
        elif choice == '3':
            # Chọn file Excel khác
            new_file = select_excel_file()
            if new_file:
                selected_excel_file = new_file
                print(f"{Fore.GREEN}✓ Đã chọn file Excel: {os.path.basename(selected_excel_file)}{Style.RESET_ALL}")
        elif choice == '4':
            # Cấu hình Debug Mode
            toggle_debug_mode()
        elif choice == '5':
            # Thoát
            log_info("Cảm ơn bạn đã sử dụng chương trình!")
            break

def excel_mode(access_token, seed, excel_file_path='prompt_image.xlsx'):
    """Chế độ tạo ảnh từ Excel (chỉ prompt) với multi-threading"""
    global current_seed
    current_seed = seed  # Khởi tạo seed global
    
    # Lấy số luồng từ user
    thread_count = get_thread_count()
    
    output_folder = get_output_folder()
    if not create_folder_if_not_exists(output_folder):
        log_error("Không thể tạo folder. Dừng chương trình.")
        return
    
    excel_data = read_excel_data(excel_file_path)
    if not excel_data:
        log_error("Không có dữ liệu trong file Excel. Dừng chương trình.")
        return
    
    log_success(f"Đã đọc {len(excel_data)} dòng dữ liệu từ Excel")
    log_info(f"Bắt đầu tạo {len(excel_data)} ảnh với {thread_count} luồng...")
    
    # Tạo danh sách tasks
    tasks = []
    for stt, prompt in excel_data:
        task_data = (stt, prompt, access_token, output_folder)
        tasks.append(task_data)
    
    # Tạo progress bar
    with tqdm(total=len(tasks), desc="Tạo ảnh", 
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
              colour='green') as pbar:
        
        # Sử dụng ThreadPoolExecutor để xử lý multi-threading
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            # Submit tất cả tasks
            future_to_task = {executor.submit(process_single_image_task, task): task for task in tasks}
            
            # Xử lý kết quả khi hoàn thành
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                stt = task[0]
                
                try:
                    result = future.result()
                    if result:
                        pbar.set_description(f"✅ Hoàn thành STT {stt}")
                    else:
                        pbar.set_description(f"❌ Lỗi STT {stt}")
                except Exception as e:
                    log_error(f"Lỗi thread cho STT {stt}: {e}")
                    pbar.set_description(f"❌ Exception STT {stt}")
                
                pbar.update(1)
    
    log_success("Hoàn thành tạo ảnh từ Excel với multi-threading!")

def excel_img2img_mode(access_token, cookie, seed, excel_file_path='prompt_image.xlsx'):
    """Chế độ tạo ảnh từ Excel với Image-to-Image và multi-threading"""
    global current_seed
    current_seed = seed  # Khởi tạo seed global
    
    # Lấy số luồng từ user
    thread_count = get_thread_count()
    
    output_folder = get_output_folder()
    if not create_folder_if_not_exists(output_folder):
        log_error("Không thể tạo folder. Dừng chương trình.")
        return
    
    excel_data = read_excel_img2img_data(excel_file_path)
    if not excel_data:
        log_error("Không có dữ liệu trong file Excel. Dừng chương trình.")
        return
    
    log_success(f"Đã đọc {len(excel_data)} dòng dữ liệu từ Excel")
    log_info(f"Bắt đầu tạo {len(excel_data)} ảnh từ ảnh với {thread_count} luồng...")
    
    # Tạo danh sách tasks
    tasks = []
    for stt, prompt, image_path in excel_data:
        task_data = (stt, prompt, image_path, access_token, cookie, output_folder)
        tasks.append(task_data)
    
    # Tạo progress bar
    with tqdm(total=len(tasks), desc="Tạo ảnh từ ảnh", 
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
              colour='magenta') as pbar:
        
        # Sử dụng ThreadPoolExecutor để xử lý multi-threading
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            # Submit tất cả tasks
            future_to_task = {executor.submit(process_single_img2img_task, task): task for task in tasks}
            
            # Xử lý kết quả khi hoàn thành
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                stt = task[0]
                
                try:
                    result = future.result()
                    if result:
                        pbar.set_description(f"✅ Hoàn thành STT {stt}")
                    else:
                        pbar.set_description(f"❌ Lỗi STT {stt}")
                except Exception as e:
                    log_error(f"Lỗi thread cho STT {stt}: {e}")
                    pbar.set_description(f"❌ Exception STT {stt}")
                
                pbar.update(1)
    
    log_success("Hoàn thành tạo ảnh từ Excel Image-to-Image với multi-threading!")




# === UTILITY FUNCTIONS ===
def select_excel_file():
    """Chọn file Excel - hỗ trợ kéo thả vào CMD hoặc nhập đường dẫn"""
    print(f"\n{Fore.YELLOW}📁 Chọn file Excel:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}1.{Style.RESET_ALL} Kéo thả file Excel vào cửa sổ này")
    print(f"{Fore.CYAN}2.{Style.RESET_ALL} Nhập đường dẫn file Excel")
    print(f"{Fore.CYAN}3.{Style.RESET_ALL} Sử dụng file dialog")
    print(f"{Fore.CYAN}4.{Style.RESET_ALL} Hủy bỏ")
    
    while True:
        choice = input(f"\n{Fore.GREEN}Chọn cách chọn file (1/2/3/4): {Style.RESET_ALL}").strip()
        
        if choice == '1':
            # Kéo thả file vào CMD
            print(f"\n{Fore.YELLOW}📂 Kéo thả file Excel vào cửa sổ này, sau đó nhấn Enter...{Style.RESET_ALL}")
            file_path = input(f"{Fore.CYAN}Đường dẫn file: {Style.RESET_ALL}").strip()
            
            if file_path:
                file_path = file_path.strip('"')
                if os.path.exists(file_path) and file_path.lower().endswith(('.xlsx', '.xls')):
                    return file_path
                else:
                    print(f"{Fore.RED}File không tồn tại hoặc không phải file Excel!{Style.RESET_ALL}")
                    continue
            else:
                return None
                
        elif choice == '2':
            # Nhập đường dẫn thủ công
            file_path = input(f"\n{Fore.CYAN}Nhập đường dẫn file Excel: {Style.RESET_ALL}").strip()
            file_path = file_path.strip('"')
            
            if file_path:
                if os.path.exists(file_path) and file_path.lower().endswith(('.xlsx', '.xls')):
                    return file_path
                else:
                    print(f"{Fore.RED}File không tồn tại hoặc không phải file Excel!{Style.RESET_ALL}")
                    continue
            else:
                return None
                
        elif choice == '3':
            # Sử dụng file dialog
            try:
                root = tk.Tk()
                root.withdraw()
                
                file_path = filedialog.askopenfilename(
                    title="Chọn file Excel",
                    filetypes=[
                        ("Excel files", "*.xlsx *.xls"),
                        ("All files", "*.*")
                    ],
                    initialdir=os.getcwd()
                )
                
                root.destroy()
                return file_path if file_path else None
                
            except Exception as e:
                print(f"{Fore.RED}Lỗi khi mở file dialog: {e}{Style.RESET_ALL}")
                continue
                
        elif choice == '4':
            return None
            
        else:
            print(f"{Fore.RED}Lựa chọn không hợp lệ!{Style.RESET_ALL}")

def ensure_dir(path):
    """Ensure directory exists"""
    if not os.path.exists(path):
        os.makedirs(path)

def center_line(text, width=70):
    """Center text within given width"""
    return text.center(width)

def print_box(info):
    """Print authentication info in a formatted box"""
    box_width = 70
    print("╔" + "═" * (box_width - 2) + "╗")
    print("║" + center_line("🔐 XÁC THỰC KEY THÀNH CÔNG", box_width - 2) + "║")
    print("╠" + "═" * (box_width - 2) + "╣")
    print("║" + center_line(f"🔑 KEY       : {info.get('key')}", box_width - 2) + "║")
    print("║" + center_line(f"📅 Hết hạn    : {info.get('expires')}", box_width - 2) + "║")
    print("║" + center_line(f"🔁 Số lượt    : {info.get('remaining')}", box_width - 2) + "║")
    print("╠" + "═" * (box_width - 2) + "╣")
    print("║" + center_line("🧠 Info dev @huyit32", box_width - 2) + "║")
    print("║" + center_line("📧 qhuy.dev@gmail.com", box_width - 2) + "║")
    print("╚" + "═" * (box_width - 2) + "╝")


if __name__ == "__main__":
    API_AUTH = f"{API_URL}/api/make_video_ai/auth"
    MAX_RETRIES = 5

    print("\n📌 XÁC THỰC KEY ĐỂ SỬ DỤNG CÔNG CỤ - WHISK AI\n")

    for attempt in range(1, MAX_RETRIES + 1):
        key = input(f"🔑 Nhập API Key (Lần {attempt}/{MAX_RETRIES}): ").strip()
        success, message, info = check_key_online(key, API_AUTH)

        if success:
            print("\n" + message + "\n")
            print_box(info)
            print()

            run_now = input("▶️  Bạn có muốn chạy chương trình ngay bây giờ không? (Y/n): ").strip().lower()
            if run_now in ("", "y", "yes"):
                print("🚀 Khởi động WHISK AI...")
                main()  # Gọi hàm main() trực tiếp
            else:
                print("✋ Bạn đã chọn không chạy chương trình. Thoát.")
            break
        else:
            print(f"\n {message}")
            if attempt < MAX_RETRIES:
                print("↩️  Vui lòng thử lại...\n")
                time.sleep(1)
            else:
                print("\n🚫 Đã nhập sai quá 5 lần. Thoát chương trình.")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print("🧠 Info dev @huyit32 | 📧 qhuy.dev@gmail.com")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                sys.exit(1)
