
import os
import cv2
import json
import qrcode
import shutil
import base64
import hashlib
import datetime
import numpy as np
from tqdm import tqdm
import concurrent.futures

chunk_size = 2048
img_d = 1770
tmp_dir = "AD_Temp"
enc_dir = "AD_Encodes"
dec_dir = "AD_Decodes"

def generate_code(data, path):
    qr = qrcode.QRCode(
        version=40,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=0,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(path)

def sha256_sum(file_path):
    h = hashlib.sha256()
    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def encode_c(input_file):
    file = open(input_file, "rb")
    data = file.read()
    encoded_data = base64.b64encode(data)
    file_name = str(os.path.splitext(os.path.basename(input_file))[0])
    file_type = str(os.path.splitext(file_path)[1])
    file_size = str(len(data)) + " Bytes"
    file_hash = str(sha256_sum(input_file))
    file_date = str(datetime.datetime.now().replace(microsecond=0))
    print("Total Bytes:", len(data))
    header = '{"name": "' + file_name + '", "type": "' + file_type + '", "size": "' + file_size + '", "date": "' + file_date + '", "hash": "' + file_hash + '"}'
    header_data = header.encode("utf-8")
    generate_code(base64.b64encode(header_data), f"{tmp_dir}/qr-0.png")
    print("Initialising...")
    data_chunks = [encoded_data[i:i + chunk_size] for i in range(0, len(encoded_data), chunk_size)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        process = []
        for i, d in enumerate(data_chunks):
            process.append(executor.submit(generate_code, d, f"{tmp_dir}/qr-{i+1}.png"))
        x = 0
        pbar = tqdm(desc="Generating ADCode", ncols=100, total=len(process), unit=" code")
        while x < len(process):
            if process[x].done() == False:
                continue
            pbar.update(1)
            x += 1
        pbar.close()
    codes = []
    for i in tqdm(range(len(data_chunks) + 1), desc="Finalising ADCode", ncols=100, total=len(data_chunks) + 1, unit=" code"):
        codes.append(cv2.imread(f"{tmp_dir}/qr-{i}.png"))
    adcode_file = input("Enter name for ADCode File : ")
    data_code = np.vstack((codes))
    cv2.imwrite(f"{enc_dir}/{adcode_file}.png", data_code)
    shutil.rmtree(tmp_dir)
    os.mkdir(tmp_dir)
    print(f"ADCode generated successfully: {enc_dir}/{adcode_file}.png\n")

def decode_c(path):
    data = b""
    image = cv2.imread(path)
    detector = cv2.wechat_qrcode_WeChatQRCode("detect.prototxt", "detect.caffemodel", "sr.prototxt", "sr.caffemodel")
    height, width, _ = image.shape
    if (height % img_d == 0 and width % img_d == 0):
        header_capture = True
        n = int(height / img_d)
        for i in tqdm(range(n), desc="Decoding ADCode", ncols=100, unit=" code"):
            y1 = img_d * i
            y2 = img_d + (img_d * i)
            code = image[y1:y2, 0:img_d]
            dst = None
            top, bottom, left, right = 5, 5, 5, 5
            borderType = cv2.BORDER_CONSTANT
            value=[255, 255, 255]
            hexcode = cv2.copyMakeBorder(code, top, bottom, left, right, borderType, dst, value)
            data_capture = base64.b64decode(detector.detectAndDecode(hexcode)[0][0])
            if header_capture:
                header = json.loads(data_capture)
                header_capture = False
            else:
                data += data_capture
        print("-" * 24 + " Encoded File Details " + "-" * 24)
        print(f"Name: {header['name']}")
        print(f"Type: {header['type']}")
        print(f"Size: {header['size']}")
        print(f"Date: {header['date']}")
        print(f"Hash: {header['hash']}")
        print("-" * 70)
        decoded_file = input(f"Enter name for Decoded File ({header['name'] + header['type']}): ")
        with open(f"{dec_dir}/{decoded_file if decoded_file != '' else header['name'] + header['type']}", "wb") as f:
            f.write(data)
        print(f"ADCode decoded successfully: {dec_dir}/{decoded_file if decoded_file != '' else header['name'] + header['type']}\n")
    else:
        print("Invalid code format")

def make_directories():
    try:
        os.mkdir(tmp_dir)
    except:
        pass
    try:
        os.mkdir(enc_dir)
    except:
        pass
    try:
        os.mkdir(dec_dir)
    except:
        pass

print()
print(" ▄▄▄      ▓█████▄  ▄████▄   ▒█████  ▓█████▄ ▓█████  ▄████▄  ")
print("▒████▄    ▒██▀ ██▌▒██▀ ▀█  ▒██▒  ██▒▒██▀ ██▌▓█   ▀ ▒██▀ ▀█  ")
print("▒██  ▀█▄  ░██   █▌▒▓█    ▄ ▒██░  ██▒░██   █▌▒███   ▒▓█    ▄ ")
print("░██▄▄▄▄██ ░▓█▄   ▌▒▓▓▄ ▄██▒▒██   ██░░▓█▄   ▌▒▓█  ▄ ▒▓▓▄ ▄██▒")
print(" ▓█   ▓██▒░▒████▓ ▒ ▓███▀ ░░ ████▓▒░░▒████▓ ░▒████▒▒ ▓███▀ ░")
print(" ▒▒   ▓▒█░ ▒▒▓  ▒ ░ ░▒ ▒  ░░ ▒░▒░▒░  ▒▒▓  ▒ ░░ ▒░ ░░ ░▒ ▒  ░")
print("  ▒   ▒▒ ░ ░ ▒  ▒   ░  ▒     ░ ▒ ▒░  ░ ▒  ▒  ░ ░  ░  ░  ▒   ")
print("  ░   ▒    ░ ░  ░ ░        ░ ░ ░ ▒   ░ ░  ░    ░   ░        ")
print("      ░  ░   ░    ░ ░          ░ ░     ░       ░  ░░ ░      ")
print("           ░      ░                  ░             ░        ")
print("<<<<<<<<<<<<<< ADVANCED DATA TO PICTURE CODEC >>>>>>>>>>>>>>")
print()
make_directories()
while True:
    print("1. Convert Files to ADCode")
    print("2. Convert ADCode to Files")
    print("3. Exit")
    c = input(">> ")
    if c == "1":
        file_path = input("Enter Target File Path : ")
        encode_c(file_path)
    elif c == "2":
        adcode_path = input("Enter ADCode Path : ")
        decode_c(adcode_path)
    elif c == "3":
        print("Exiting...")
        exit()
    else:
        print("Invalid Option... Please try again\n")
