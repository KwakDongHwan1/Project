import cv2, numpy as np
import cctv_detector
import using_telegram
import threading
import play_sound
from PIL import ImageGrab
from flask import Flask, render_template, Response, request, flash
import menu_main


"""
이 파일을 실행해주세요.
"""

app = Flask(__name__)

@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_frames(): # generate frame by frame from camera
    f = open('screen_xy.txt', 'r')
    x1, y1, x2, y2 = map(int, f.readline().split())
    f.close()

    while True:
        src = cv2.cvtColor(np.array(ImageGrab.grab(bbox=(x1, y1, x2, y2))), cv2.COLOR_BGR2RGB)
        det = cctv_detector.detect(src)

        if det is not None:
            dst = cctv_detector.draw_boxes(src, det)
        else: 
            dst = src.copy()

        ret, buffer = cv2.imencode('.jpg', dst)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/occur')
def occur():
    return render_template('occur.html')

@app.route('/result')
def result():
    return render_template('result.html')

@app.route('/user')
def user():
    return render_template('user.html')

def app_run():
    app.run(host='0.0.0.0', port=5000)

def start_menu():
    menu_thread = threading.Thread(target = menu_main.main, args=()) # 시간이 오래 걸리는 부분을 스레딩으로 처리하여 성능 향상.
    menu_thread.daemon = True # if문에서 30초에 한번씩 보내기로 하였는데 그 30초 사이에 끄고 싶을 수 있기 때문에 데몬 스레드로 설정하여 메인 스레드가 꺼지면 꺼지게 하였다.
    menu_thread.start()

if __name__ == '__main__':
    using_telegram.init()
    play_sound.init()
    start_menu()
    app_run()

    using_telegram.save()