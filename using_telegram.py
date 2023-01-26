import telegram
import cv2
import time
import cvlib
import os

def init():
    global bot
    global user_id_list, user_id_codes, user_send_cats
    global cat_msg
    global occur

    user_id_list, user_id_codes, user_send_cats = [], [], []
    now = time.localtime(time.time())

    occur = {
        'date': str(now.tm_year) + (str(now.tm_mon) if now.tm_mon>9 else ('0'+str(now.tm_mon))) + (str(now.tm_mday) if now.tm_mday>9 else ('0'+str(now.tm_mday))),
        'assault': 0, 
        'fainting': 0, 
        'property_damage': 0, 
        'stairway_fall': 0,
        'turnstile_trespassing': 0
    }

    f = open('telegraminfo.txt', 'r')
    TOKEN = f.readline()
    bot = telegram.Bot(TOKEN)
    f.close()

    f = open('id_list.txt', 'r', encoding="UTF-8")
    user_id_list = f.readlines()
    f.close()
    
    for v in user_id_list:
        _, user_send_cat, user_id_code = v.split()
        user_send_cats.append(user_send_cat.split(','))
        user_id_codes.append(str(int(user_id_code)))

    # print(user_id_list)

    cat_msg = {
       'assault': '폭행이 감지된 상황입니다.', 
       'fainting': '실신이 감지된 상황입니다.', 
       'property_damage': '기물파손이 감지된 상황입니다.', 
       'stairway_fall': '이용객이 계단에서 넘어진 상황입니다.',
       'turnstile_trespassing': '개집표기 무단진입이 감지된 상황입니다.'
    }
    del_old_file()
    print('텔레그램 초기화 완료')

def del_old_file(): # CCTV 이미지 데이터 보관시간은 일주일이기때문에, 일주일이 지나면 지운다.
    now = time.localtime(time.time())
    compare = str(now.tm_year) + (str(now.tm_mon) if now.tm_mon>9 else ('0'+str(now.tm_mon))) + (str(now.tm_mday) if now.tm_mday>9 else ('0'+str(now.tm_mday))) \
                    + (str(now.tm_hour) if now.tm_hour>9 else ('0'+str(now.tm_hour))) + (str(now.tm_min) if now.tm_min>9 else ('0'+str(now.tm_min))) + '.jpg'

    for root, dirs, filenames in os.walk('send_image'):
        for filename in filenames:
            if int(compare[:8]) - int(filename[:8]) > 7: # 파일이름이 year(4) + month(2) + day(2) = 8 이기 때문에 8까지 잘라서 일주일인지 확인
                os.remove(os.path.join(root,filename))

def data_processing(src): # 이미지 처리하는 부분
    #현재 시간으로 이름 저장
    now = time.localtime(time.time())
    image_name = str(now.tm_year) + (str(now.tm_mon) if now.tm_mon>9 else ('0'+str(now.tm_mon))) + (str(now.tm_mday) if now.tm_mday>9 else ('0'+str(now.tm_mday))) \
                    + (str(now.tm_hour) if now.tm_hour>9 else ('0'+str(now.tm_hour))) + (str(now.tm_min) if now.tm_min>9 else ('0'+str(now.tm_min))) + '.jpg'

    # 얼굴 모자이크 하기 위한 이미지 처리
    faces, confidences = cvlib.detect_face(src, 0.2) # 0.2는 임계값
    # print(confidences)
    if len(faces) > 0:
        for (x1, y1, x2, y2) in faces: # lefttop, rightbottom
            mosaic_loc = src[y1:y2, x1:x2]
            mosaic_loc = cv2.blur(mosaic_loc,(50, 50))
            src[y1:y2, x1:x2] = mosaic_loc

    cv2.imwrite('send_image/'+ image_name, src) # 이미지 저장

    return image_name, src

def resend(queue_list, temp):
    time.sleep(30)
    for v, flag in zip(queue_list, temp):
        if flag:
            v.get()
            
def check_id(id):
    global bot
    try:
        bot.send_message(chat_id=str(int(id)), text='아이디가 있는지 확인하는 메시지입니다.')
        return True
    except:
        return False

def save():
    global occur
    f = open('occur.txt', 'r')
    dates = f.readlines()
    f.close()
    f = open('occur.txt', 'w')
    if len(dates):
        if occur['date'] in dates[-1]:
            date, o1, o2, o3, o4, o5= dates[-1].split()
            dates[-1] = '%s %s %s %s %s %s\n' % (date, str(int(o1)+occur['assault']), str(int(o2)+occur['fainting']), str(int(o3)+occur['property_damage']), str(int(o4)+occur['stairway_fall']), str(int(o5)+occur['turnstile_trespassing']))
        else:
            dates.append('%s %s %s %s %s %s\n' % (date, str(occur['assault']), str(occur['fainting']), str(occur['property_damage']), str(occur['stairway_fall']), str(occur['turnstile_trespassing'])))

        for v in dates:
            f.write(v)
    else:
        f.write('%s %s %s %s %s %s\n' % (occur['date'], str(occur['assault']), str(occur['fainting']), str(occur['property_damage']), str(occur['stairway_fall']), str(occur['turnstile_trespassing'])))

    f.close()

def send_msg(action_list, dst, queue_list, temp):
    global bot
    global cat_msg
    global user_id_list, user_id_codes, user_send_cats
    global occur

    text = "전송한 이미지는 아래와 같은 상황이 있습니다.\n"
    image_name, dst = data_processing(dst)
    cat = ''
    for i, msg in enumerate(action_list):
        cat, conf = msg.split()
        occur[cat] += 1
        conf = float(conf)*100 # 0.27 을 27로 만들어줌
        text += str(i+1) + '번째, ' + str(conf) + '%로 ' + cat_msg[cat] + '\n'

    for user,send_cat in zip(user_id_codes,user_send_cats):
        if cat in send_cat:
            bot.send_photo(chat_id=user, photo=open('send_image/'+image_name,'rb'))
            bot.send_message(chat_id=user, text=text)
    
    # 나에게만 보내는 테스트라인
    # user = user_id_list[0]
    # bot.send_photo(chat_id=user, photo=open('send_image/'+image_name,'rb'))
    # bot.send_message(chat_id=user, text=text)

    resend(queue_list, temp)

"""
추가 해야 할 것.
1. 현재시간에서 같은 클래스가 검출될 경우에는 1분의 재전송 시간이 필요하게 해야함. O -> 08/09
2. 이미지 데이터베이스에서는 일주일이 지난 사진은 지운다.
3. 해당 부서의 담장자와, 총 책임자에게만 메세지를 전달한다. ing
"""

if __name__ == '__main__':
    init()
    print(check_id('5184853548'))