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

# Khởi tạo colorama
init(autoreset=True)

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
        
        # Random delay trước request
        delay = self.random_delay()
        
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except Exception as e:
            log_error(f"Request failed: {e}")
            return None

# Khởi tạo browser simulator
browser_sim = BrowserSimulator()

def activate_browser_simulation():
    """Kích hoạt các thông số giả lập trình duyệt thật"""
    print("✓ Đã kích hoạt các thông số giả lập trình duyệt thật:")
    print("  - User-Agent ngẫu nhiên")
    print("  - Headers giả lập trình duyệt")
    print("  - Fingerprint giả lập")
    print("  - Delay ngẫu nhiên giữa các request")
    print("  - Session giả lập")
    print("  - Retry strategy cho request")
    print("  - Connection pooling")

def log_info(message):
    """Log thông tin với thời gian và màu xanh"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.CYAN}[{timestamp}] {Fore.GREEN}[INFO]{Style.RESET_ALL} {message}")

def log_success(message):
    """Log thành công với thời gian và màu xanh lá"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.CYAN}[{timestamp}] {Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {message}")

def log_error(message):
    """Log lỗi với thời gian và màu đỏ"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.CYAN}[{timestamp}] {Fore.RED}[ERROR]{Style.RESET_ALL} {message}")

def log_warning(message):
    """Log cảnh báo với thời gian và màu vàng"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.CYAN}[{timestamp}] {Fore.YELLOW}[WARNING]{Style.RESET_ALL} {message}")

def log_user_info(name, email):
    """Log thông tin user với màu đặc biệt"""
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

def read_excel_data():
    """Đọc dữ liệu từ file Excel (STT, PROMPT)"""
    # Hiển thị loading spinner
    spinner = LoadingSpinner("Đang đọc file Excel...", Fore.GREEN)
    spinner.start()
    
    try:
        df = pd.read_excel('prompt_image.xlsx')
        # Lấy cột A (STT) và cột B (PROMPT)
        stt_list = df.iloc[:, 0].tolist()  # Cột A
        prompt_list = df.iloc[:, 1].tolist()  # Cột B
        
        spinner.stop()
        return list(zip(stt_list, prompt_list))
    except Exception as e:
        spinner.stop()
        log_error(f"Lỗi khi đọc file Excel: {e}")
        return []

def read_excel_img2img_data():
    """Đọc dữ liệu từ file Excel cho Image-to-Image (STT, PROMPT, IMAGE_PATH)"""
    # Hiển thị loading spinner
    spinner = LoadingSpinner("Đang đọc file Excel cho Image-to-Image...", Fore.GREEN)
    spinner.start()
    
    try:
        df = pd.read_excel('prompt_image.xlsx')
        # Lấy cột A (STT), cột B (PROMPT), cột C (IMAGE_PATH)
        stt_list = df.iloc[:, 0].tolist()  # Cột A
        prompt_list = df.iloc[:, 1].tolist()  # Cột B
        image_path_list = df.iloc[:, 2].tolist()  # Cột C
        
        spinner.stop()
        return list(zip(stt_list, prompt_list, image_path_list))
    except Exception as e:
        spinner.stop()
        log_error(f"Lỗi khi đọc file Excel: {e}")
        return []

def generate_image(access_token, prompt, seed):
    """Gọi API để tạo ảnh"""
    url = "https://aisandbox-pa.googleapis.com/v1/whisk:generateImage"
    
    headers = browser_sim.get_api_headers(access_token=access_token)
    
    # Tạo UUID ngẫu nhiên cho workflowId
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
    spinner = LoadingSpinner("Đang tạo ảnh với AI...", Fore.MAGENTA)
    spinner.start()
    
    try:
        response = browser_sim.make_request("POST", url, headers=headers, json=payload, timeout=60)
        spinner.stop()
        
        if response and response.status_code == 200:
            return response.json()
        else:
            if response:
                log_error(f"Lỗi khi tạo ảnh: {response.status_code}")
                log_error(response.text)
            return None
    except requests.exceptions.Timeout:
        spinner.stop()
        log_error("Timeout khi tạo ảnh - có thể prompt quá phức tạp")
        return None
    except Exception as e:
        spinner.stop()
        log_error(f"Lỗi khi tạo ảnh: {e}")
        return None

def download_image(image_url, filename):
    """Tải xuống ảnh"""
    try:
        response = requests.get(image_url)
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
    # Tạo đường dẫn đầy đủ
    full_path = os.path.join(output_folder, filename)
    
    # Hiển thị loading spinner
    spinner = LoadingSpinner(f"Đang lưu ảnh: {filename[:30]}...", Fore.BLUE)
    spinner.start()
    
    try:
        # Loại bỏ prefix data:image/jpeg;base64, nếu có
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        image_data = base64.b64decode(base64_data)
        with open(full_path, 'wb') as f:
            f.write(image_data)
        
        spinner.stop()
        log_success(f"Đã lưu ảnh: {full_path}")
        return True
    except Exception as e:
        spinner.stop()
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


def show_main_menu():
    """Hiển thị menu chính"""
    print(f"\n{Fore.YELLOW}🎨 Chọn chế độ tạo ảnh:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}1.{Style.RESET_ALL} Tạo ảnh từ prompt (Excel)")
    print(f"{Fore.CYAN}2.{Style.RESET_ALL} Tạo ảnh từ Prompt + Image (Image-to-Image)")
    print(f"{Fore.CYAN}3.{Style.RESET_ALL} Thoát")
    
    while True:
        choice = input(f"\n{Fore.GREEN}Chọn chế độ (1/2/3): {Style.RESET_ALL}").strip()
        if choice in ['1', '2', '3']:
            return choice
        else:
            print(f"{Fore.RED}Lựa chọn không hợp lệ! Vui lòng chọn 1, 2 hoặc 3.{Style.RESET_ALL}")

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
    
    # Hiển thị menu chính
    while True:
        choice = show_main_menu()
        
        if choice == '1':
            # Chế độ tạo ảnh từ prompt (Excel)
            excel_mode(access_token, seed)
        elif choice == '2':
            # Chế độ tạo ảnh từ Excel + Ảnh
            excel_img2img_mode(access_token, cookie, seed)
        elif choice == '3':
            # Thoát
            log_info("Cảm ơn bạn đã sử dụng chương trình!")
            break

def excel_mode(access_token, seed):
    """Chế độ tạo ảnh từ Excel (chỉ prompt)"""
    # Bước 1: Chọn folder output
    output_folder = get_output_folder()
    if not create_folder_if_not_exists(output_folder):
        log_error("Không thể tạo folder. Dừng chương trình.")
        return
    
    # Bước 2: Đọc dữ liệu từ Excel
    log_info("Đang đọc dữ liệu từ Excel...")
    excel_data = read_excel_data()
    
    if not excel_data:
        log_error("Không có dữ liệu trong file Excel. Dừng chương trình.")
        return
    
    log_success(f"Đã đọc {len(excel_data)} dòng dữ liệu từ Excel")
    
    # Bước 3: Tạo ảnh cho từng prompt
    log_info(f"Bắt đầu tạo {len(excel_data)} ảnh...")
    log_info(f"Ảnh sẽ được lưu vào: {os.path.abspath(output_folder)}")
    
    # Tạo progress bar
    with tqdm(total=len(excel_data), desc="Tạo ảnh", 
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
              colour='green') as pbar:
        
        for stt, prompt in excel_data:
            pbar.set_description(f"Tạo ảnh STT {stt}")
            
            # Gọi API tạo ảnh
            result = generate_image(access_token, prompt, seed)
            
            if result and 'imagePanels' in result:
                for panel in result['imagePanels']:
                    if 'generatedImages' in panel:
                        for img in panel['generatedImages']:
                            if 'encodedImage' in img:
                                filename = sanitize_filename(stt, prompt)
                                # Lưu ảnh từ base64 vào folder được chọn
                                save_base64_image(img['encodedImage'], filename, output_folder)
            
            # Tăng seed cho lần tiếp theo
            seed += 1
            pbar.update(1)
    
    log_success("Hoàn thành tạo ảnh từ Excel!")

def excel_img2img_mode(access_token, cookie, seed):
    """Chế độ tạo ảnh từ Excel với Image-to-Image"""
    # Bước 1: Chọn folder output
    output_folder = get_output_folder()
    if not create_folder_if_not_exists(output_folder):
        log_error("Không thể tạo folder. Dừng chương trình.")
        return
    
    # Bước 2: Đọc dữ liệu từ Excel
    log_info("Đang đọc dữ liệu từ Excel cho Image-to-Image...")
    excel_data = read_excel_img2img_data()
    
    if not excel_data:
        log_error("Không có dữ liệu trong file Excel. Dừng chương trình.")
        return
    
    log_success(f"Đã đọc {len(excel_data)} dòng dữ liệu từ Excel")
    
    # Bước 3: Tạo ảnh cho từng dòng
    log_info(f"Bắt đầu tạo {len(excel_data)} ảnh từ ảnh...")
    log_info(f"Ảnh sẽ được lưu vào: {os.path.abspath(output_folder)}")
    
    # Tạo progress bar
    with tqdm(total=len(excel_data), desc="Tạo ảnh từ ảnh", 
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
              colour='magenta') as pbar:
        
        for stt, prompt, image_path in excel_data:
            pbar.set_description(f"Xử lý STT {stt}")
            
            # Kiểm tra file ảnh có tồn tại không
            if not os.path.exists(image_path):
                log_error(f"Không tìm thấy file ảnh: {image_path}")
                pbar.update(1)
                continue
            
            # Upload ảnh lên Google Labs
            log_info(f"Đang upload ảnh: {os.path.basename(image_path)}")
            upload_data = upload_image_to_google_labs(cookie, image_path, caption="A hyperrealistic digital illustration depicts a shiny, chrome-like mouse character, standing confidently in a martial arts gi against a subtly rendered, dark background of what appears to be an arena. The character, positioned centrally in the frame, faces forward with a slight tilt of its head to the right. Its body is composed of a highly reflective, polished silver material, giving it a metallic, almost liquid sheen.\n\nThe mouse has large, round ears that match its reflective silver body. Its face is characterized by large, expressive eyes with black pupils surrounded by a thin white iris, and a faint, thin black eyebrow line above each eye. A small, dark triangular nose sits above a tiny, closed mouth. Whiskers, depicted as thin black lines, extend from its cheeks. The overall expression of the mouse is one of determination or seriousness.\n\nIt wears a dark, possibly black or very dark gray, martial arts gi. The gi consists of a wrap-around top with a V-neck opening and wide sleeves, secured at the waist by a tied belt with a knot at the front. The fabric of the gi has visible texture, with distinct lines and shading suggesting folds and creases, giving it a somewhat sketch-like or illustrated appearance in contrast to the smooth, reflective quality of the mouse's skin. The gi extends down to just above its feet. The mouse's feet are clad in simple, low-top white sneakers with dark soles, contrasting with the dark gi.\n\nThe background is dark and desaturated, creating a stark contrast with the shiny character. It suggests the interior of an arena or training dojo, with a circular, slightly elevated platform visible in the foreground where the mouse stands. The background features blurred architectural elements, possibly seating or walls, rendered in shades of dark gray and black. A faint \"SU\" logo, stylized in white, is visible in the upper right corner of the image. The lighting appears to come from the front and slightly above, accentuating the metallic sheen of the mouse and casting subtle shadows.")
            
            if not upload_data:
                log_error(f"Không thể upload ảnh: {image_path}")
                pbar.update(1)
                continue
            # print('UPLOAD ẢNH LÊN GOOGLE LABS',upload_data)
            # Tạo ảnh từ ảnh
            result = generate_image_from_image(access_token, upload_data, prompt, seed)
            
            if result and 'imagePanels' in result:
                for panel in result['imagePanels']:
                    if 'generatedImages' in panel:
                        for img in panel['generatedImages']:
                            if 'encodedImage' in img:
                                filename = sanitize_filename(stt, prompt)
                                # Lưu ảnh từ base64 vào folder được chọn
                                save_base64_image(img['encodedImage'], filename, output_folder)
            
            # Tăng seed cho lần tiếp theo
            seed += 1
            pbar.update(1)
    
    log_success("Hoàn thành tạo ảnh từ Excel Image-to-Image!")

if __name__ == "__main__":
    main()
