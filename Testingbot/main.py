import subprocess
import tkinter as tk
from tkinter import ttk
import cv2
import threading
import time
import os
import urllib.parse

def detect_emulators(adb_path):
    try:
        result = subprocess.run([adb_path, 'devices'], capture_output=True, text=True, check=True)
        devices = result.stdout.splitlines()
        emulator_ids = [line.split()[0] for line in devices[1:] if line and line.split()[0].startswith('127.0.0.1')]
        
        if not emulator_ids:
            return []
        emulator_names = [f"emulator-{str(i+1).zfill(2)}" for i in range(len(emulator_ids))]
        return dict(zip(emulator_names, emulator_ids))
    except subprocess.CalledProcessError as e:
        print(f"Error menjalankan ADB: {e}")
        return []

def stop_application(adb_path, emulator_id, main_package):
    try:
        subprocess.run([adb_path, '-s', emulator_id, 'shell', 'am', 'force-stop', main_package], check=True)
        return f"Berhenti aplikasi di {emulator_id}"
    except subprocess.CalledProcessError as e:
        return f"Error menghentikan aplikasi pada {emulator_id}: {e}"

def start_application(adb_path, emulator_id, main_package, activity_name):
    try:
        subprocess.run([adb_path, '-s', emulator_id, 'shell', 'am', 'start', '-n', f'{main_package}/{activity_name}'], check=True)
        return f"Membuka aplikasi di {emulator_id}"
    except subprocess.CalledProcessError as e:
        return f"Error menjalankan aplikasi pada {emulator_id}: {e}"

def take_screenshot(adb_path, emulator_id, filename='screen.png'):
    try:
        subprocess.run([adb_path, '-s', emulator_id, 'shell', 'screencap', '-p', '/sdcard/screen.png'], check=True)
        subprocess.run([adb_path, '-s', emulator_id, 'pull', '/sdcard/screen.png', filename], check=True)
        image = cv2.imread(filename)
        return image
    except subprocess.CalledProcessError as e:
        print(f"Error mengambil screenshot pada {emulator_id}: {e}")
        return None

def find_image_location(screen_img, template_img_path):
    template = cv2.imread(template_img_path, 0)
    if template is None:
        print(f"Error: Gambar template '{template_img_path}' tidak ditemukan atau tidak bisa dibaca.")
        return None
    gray_screen = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(gray_screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    threshold = 0.9
    if max_val >= threshold:
        return max_loc
    return None

def click_on_location(adb_path, emulator_id, location, template_img_path):
    if location is None:
        print(f"Error: Lokasi untuk gambar template '{template_img_path}' tidak ditemukan.")
        return
    x, y = location
    template_img = cv2.imread(template_img_path)
    if template_img is None:
        print(f"Error: Gambar template '{template_img_path}' tidak ditemukan atau tidak bisa dibaca.")
        return
    height, width = template_img.shape[:2]
    center_x = x + width // 2
    center_y = y + height // 2
    subprocess.run([adb_path, '-s', emulator_id, 'shell', 'input', 'tap', str(center_x), str(center_y)], check=True)
    print(f"Clicked on location ({center_x}, {center_y}) on {emulator_id}")




def send_text(adb_path, emulator_id, text):
    try:
        # Kirim teks
        subprocess.run([adb_path, '-s', emulator_id, 'shell', 'input', 'text', text], check=True)
        print(f"Sent text '{text}' on {emulator_id}")
    except subprocess.CalledProcessError as e:
        print(f"Error sending text on {emulator_id}: {e}")
def send_text_verif(adb_path, emulator_id, text):
    try:
        # Kirim teks
        subprocess.run([adb_path, '-s', emulator_id, 'shell', 'input', 'keyboard', text], check=True)
        print(f"Sent text '{text}' on {emulator_id}")
    except subprocess.CalledProcessError as e:
        print(f"Error sending text on {emulator_id}: {e}")

def clear_text(adb_path, emulator_id, count=100):
    try:
        for _ in range(count):
            subprocess.run([adb_path, '-s', emulator_id, 'shell', 'input', 'keyevent', 'KEYCODE_DEL'], check=True)
        print(f"Text cleared on {emulator_id}")
    except subprocess.CalledProcessError as e:
        print(f"Error clearing text on {emulator_id}: {e}")
    

def update_log(logs, emulator_id, message):
    if emulator_id in logs:
        logs[emulator_id].append(message)

def create_ui(emulators, logs, id_pass_queue):
    def on_start_button_click():
        nonlocal logs
        for name, id in emulators.items():
            stop_message = stop_application(adb_path, id, main_package)
            update_log(logs, id, stop_message)
            log_message = start_application(adb_path, id, main_package, activity_name)
            update_log(logs, id, log_message)
            thread = threading.Thread(target=perform_click, args=(id,))
            thread.start()

    
    def perform_click(emulator_id):
        while True:
            time.sleep(5)
            screen_img = take_screenshot(adb_path, emulator_id, 'screen.png')
            if screen_img is not None:
                update_log(logs, emulator_id, "Take Screenshot")
                found_match = False
                assets_path = './Assets'
                for filename in os.listdir(assets_path):
                    if filename.endswith('_screen.png'):
                        template_path = os.path.join(assets_path, filename)
                        location = find_image_location(screen_img, template_path)
                        if location:
                            found_match = True
                            if filename == 'speeder_screen.png':
                                activated_speeder_path = os.path.join(assets_path, 'speeder01_active.png')
                                activated_speeder_location = find_image_location(screen_img, activated_speeder_path)
                                if activated_speeder_location:
                                    click_on_location(adb_path, emulator_id, activated_speeder_location, activated_speeder_path)
                                    update_log(logs, emulator_id, "Speeder active")
                            elif filename == 'update_screen.png':
                                close_update_path = os.path.join(assets_path, 'closeupdate.png')
                                close_update_location = find_image_location(screen_img, close_update_path)
                                if close_update_location:
                                    click_on_location(adb_path, emulator_id, close_update_location, close_update_path)
                                    update_log(logs, emulator_id, "Close update action performed")
                            elif filename == 'home_screen.png':
                                id_login_path = os.path.join(assets_path, 'idlogin.png')
                                id_login_location = find_image_location(screen_img, id_login_path)
                                if id_login_location:
                                    click_on_location(adb_path, emulator_id, id_login_location, id_login_path)
                                    update_log(logs, emulator_id, "ID login action performed")
                            elif filename == 'login_screen.png':
                                input_id_path = os.path.join(assets_path, 'inputid.png')
                                input_id_location = find_image_location(screen_img, input_id_path)
                                if input_id_location:
                                    click_on_location(adb_path, emulator_id, input_id_location, input_id_path)
                                    update_log(logs, emulator_id, "Input ID action performed")
                                    if id_pass_queue:
                                        id_pass = id_pass_queue.pop(0)
                                        send_text(adb_path, emulator_id, id_pass['id'])
                                        time.sleep(2)
                                        input_pass_path = os.path.join(assets_path, 'inputpass.png')
                                        input_pass_location = find_image_location(screen_img, input_pass_path)
                                        if input_pass_location:
                                            click_on_location(adb_path, emulator_id, input_pass_location, input_pass_path)
                                            update_log(logs, emulator_id, "Input password action performed")
                                            send_text(adb_path, emulator_id, id_pass['pass'])     
                                            submit_login_path = os.path.join(assets_path, 'submit_login.png')
                                            submit_login_location = find_image_location(screen_img, submit_login_path)
                                            if submit_login_location:
                                                click_on_location(adb_path, emulator_id, submit_login_location, submit_login_path)
                                                update_log(logs, emulator_id, "Submit ID & Password")
                            elif filename == 'verif_layer_screen.png':
                                clicked_verif_path = os.path.join(assets_path, 'verif_layer_clicked.png')
                                clicked_verif_location = find_image_location(screen_img, clicked_verif_path)
                                if clicked_verif_location:
                                    click_on_location(adb_path, emulator_id, clicked_verif_location, clicked_verif_path)
                                    update_log(logs, emulator_id, "Verification layer clicked")
                            elif filename == 'verifinput_screen.png':
                                input_verif_path = os.path.join(assets_path, 'test.png')
                                input_verif_location = find_image_location(screen_img, input_verif_path)
                                input_verif2_path = os.path.join(assets_path, 'verifinput02.png')
                                input_verif2_location = find_image_location(screen_img, input_verif2_path)
                                if input_verif_location:
                                    click_on_location(adb_path, emulator_id, input_verif_location, input_verif_path)             
                                    update_log(logs, emulator_id, "Input verif action performed")
                                    if id_pass_queue:
                                        send_text(adb_path, emulator_id, id_pass['answer'])
                                        send_text_verif(adb_path, emulator_id, id_pass['answer'])
                                        click_on_location(adb_path, emulator_id, input_verif_location, input_verif_path)   
                                        send_text(adb_path, emulator_id, id_pass['answer'])
                                        id_pass_queue.append(id_pass)
                                        time.sleep(1)
                                   
            if not found_match:
                subprocess.run([adb_path, '-s', emulator_id, 'shell', 'input', 'keyevent', 'KEYCODE_HOME'], check=True)
                subprocess.run([adb_path, '-s', emulator_id, 'shell', 'am', 'force-stop', 'com.higgs.domino'], check=True)
                subprocess.run([adb_path, '-s', emulator_id, 'logcat', '-c'], check=True)
                update_log(logs, emulator_id, "Semua aplikasi ditutup, kembali ke home")
                time.sleep(3)
                start_message = start_application(adb_path, emulator_id, main_package, activity_name)
                update_log(logs, emulator_id, start_message)
            root.after(0, update_ui_logs)


    def update_ui_logs():
        for item in tree.get_children():
            emulator_id = tree.item(item, "values")[0]
            if emulator_id in logs and logs[emulator_id]:
                latest_log = logs[emulator_id][-1]
                tree.item(item, values=(emulator_id, latest_log))
    
    root = tk.Tk()
    root.title("Emulator Log")

    tree = ttk.Treeview(root, columns=("Emulator", "Log"), show='headings')
    tree.heading("Emulator", text="Emulator")
    tree.heading("Log", text="Log")
    tree.pack(fill=tk.BOTH, expand=True)

    for emulator_name, emulator_id in emulators.items():
        tree.insert("", tk.END, iid=emulator_id, values=(emulator_id, ""))

    start_button = tk.Button(root, text="Mulai", command=on_start_button_click)
    start_button.pack(pady=10)

    def refresh_logs():
        update_ui_logs()
        root.after(1000, refresh_logs)

    refresh_logs()
    root.mainloop()

def main():
    global adb_path, main_package, activity_name
    adb_path = './adb/adb.exe'
    main_package = 'com.higgs.domino'
    activity_name = 'com.pokercity.lobby.lobby'
    
    emulators = detect_emulators(adb_path)
    logs = {id: [] for id in emulators.values()}  

    id_pass_list = [
        {'id': '589631885', 'pass': 'null00', 'answer': 'aaa'},
        {'id': '7879743667', 'pass': 'null02', 'answer': 'titit'},
        {'id': '7879786686', 'pass': 'null03', 'answer': 'titit'},
        {'id': '7879787667', 'pass': 'null04', 'answer': 'titit'},
        {'id': '7879346667', 'pass': 'null05', 'answer': 'titit'}
    ]
    id_pass_queue = id_pass_list.copy()

    if emulators:
        create_ui(emulators, logs, id_pass_queue)
    else:
        print("Tidak ada emulator yang terdeteksi.")

if __name__ == "__main__":
    main()
