import sys
import os
import time
# キー入力監視
import keyboard
# 表情認識
from feat import Detector
import matplotlib.pyplot as plt
# webカメラ
import cv2
# 音声DL
import requests
# 音声再生
import subprocess
import time
import vlc # pip install python-vlc
# alert dialog
import tkinter as tk
import tkinter.messagebox as messagebox

# OK の時に音を流すかのフラグ
OK_SOUND = True

# 識別機 すごく時間がかかる 
# 導入の簡単のためにpy-featを選択しているが
# レスポンスを求める場合はCV2などで置き換えるとよい
detector = Detector()

# カメラインスタンス
# カメラデバイスidは基本0だけど、ダメなときはここを見直す
cam_id = 0
cap = cv2.VideoCapture(cam_id)


# VLC instance
instance = vlc.Instance()
player = instance.media_player_new()


# 顔ない (横転) 
# ワロタ ワロス 草 笑 
# 泣いた 
# magao
# ひっかける言葉
kaonai_str = ['k', 'a', 'o', 'n', 'a', 'i']
warota_str = ['w','a','r','o','t','a']
warosu_str = ['w','a','r','o','s','u']
kusa_str = ['k','u','s','a']
wara_str = ['w','a','r','a']
naita_str = ['n','a','i','t','a']
magao_str = ['m','a','g','a','o']


# 狩る言葉を追加する場合は上にstr作ってここ2つに追加
#              顔ない        ワロタ      ワロス          草          わら         泣いた     真顔
words_list = [kaonai_str, warota_str,  warosu_str,   kusa_str,    wara_str,    naita_str, magao_str]
keys_list = [ 'no_face'    ,'happiness', 'happiness', 'happiness', 'happiness', 'sadness' ,'neutral']

# 日本語との対応
face_dic = {'anger':'怒り顔', 'disgust':'嫌な顔', 'fear':'怯えた顔', 'happiness':'笑顔', 'sadness':'泣き顔', 'surprise':'驚き顔', 'neutral':'真顔'}

# 画像から表情認識  結構時間かかる
def face_cap(path):
    print(f'path = {path}')
    start = time.time()  # 現在時刻（処理開始前）を取得
    result = detector.detect_image(path)
    end = time.time()  # 現在時刻（処理完了後）を取得
    time_diff = end - start  # 処理完了後の時刻から処理開始前の時刻を減算する
    print(f'cheak time :{time_diff}')  # 処理にかかった時間データを使用
    print(f'result , type={type(result)}')
    count = 0
    #        怒り       嫌悪      恐怖      幸福         悲しみ      驚き        真顔
    keys = ['anger', 'disgust', 'fear', 'happiness', 'sadness', 'surprise', 'neutral']
    
    emo = result.emotions
    print(f'{emo}')
    # No Face Detect
    num_NaN = emo.isna().values.sum()
    if num_NaN > 0:
        print(f'NaN')
        return keys_list[0], result # 'NONE'
    else:
        max = 0
        ind = 0
        # 一番評価値がデカいのが、表情検知結果
        for i in range(len(keys)):
            val = emo[keys[i]].values[0]
            print(f'{keys[i]} : {val:.6f}')
            
            if val > max:
                max = val
                ind = i
        
        print(f'Emotion is {keys[ind]} : {max:.6f}')
        return keys[ind], result

# 画像を撮影保存
def cap_img(path):
    if cap.isOpened():
        ret, frame = cap.read()
        play(0)
        #frame = cv2.resize(frame, dsize=None, fx=0.5, fy=0.5)
        cv2.imwrite(path, frame)
    return 

# 感情不一致を通知
def alert(word_str, emo_txt, emo_pic, res):
    if emo_pic=='no_face':
        print(f'顔を検出できません')
        return 0
    play(1)
    say = ''
    for w in word_str:
        say = say + w
    mess = f'You say \"{say} ({emo_txt})\",\n But your face is \"{emo_pic}\"!!'
    print(mess)
    root = tk.Tk()
    root.attributes('-topmost', True)
    root.withdraw()
    # tk.Tk().withdraw()
    mess2 = f"誇張した入力を検知しました。\nあなたは「{say}」と入力しましたが、あなたの顔は「{face_dic[emo_pic]}」です。\n過度な誇張表現は避けましょう。 "
    res = messagebox.showwarning('誇張入力検知', mess2)
    return res

def main():
    counter = 0
    q = []

    warota_flag = False
    naita_flag = False
    quit_flag = False
    
    # queueの大きさの決定
    max_len = 0
    for word in words_list:
        if len(word) > max_len:
            max_len =  len(word)
    
    # 撮影画像の保存先
    path = 'now.jpg'
    
    while True:
        # キー入力
        if keyboard.read_event().event_type == keyboard.KEY_DOWN: 
            #print(f'keyboard.read_key() = {keyboard.read_key()}')
            key = keyboard.read_key()
            if key == 'backspace' and len(q)>0: # バックスペースでキューも消す
                q.pop(-1)
            elif len(q) == max_len: # キューがいっぱいなら FIFO
                q.pop(0)
                q.append(key)
            else: # キューが満タンになるまでは普通に追加
                q.append(key)
            print(f'q : {q}\n')
            
            # queueを監視して 例の単語が入力されたことを検知
            for i in range(len(words_list)): 
                word_str = words_list[i] # 判定したい文字列
                if q[-len(word_str):] == word_str: # 判定文字列が入力されてたら
                    print(f'{word_str}')
                    # 文字列の感情
                    emo_txt = keys_list[i]
                    print(f'emotion maybe {emo_txt}')
                    # 撮影
                    cap_img(path)
                    # 画像解析
                    emo_pic, res = face_cap(path)
                    # アラート
                    if emo_pic!=emo_txt: # 文章と感情の不一致時
                        alert(word_str, emo_txt, emo_pic, res)
                    else: # 一致時
                        if OK_SOUND:
                            play(2)
                        print(f'same emotion txt-face')
                        pass

# 音を鳴らす
def play(ind):
    path_list = ['camera-shutter1.mp3', 'decision13.mp3', 'correct2.mp3']
    media = instance.media_new(path_list[ind])
    player.set_media(media)
    player.play()
    time.sleep(1)
    player.stop()

# 音声ファイルのダウンロード
def init_():
    print('======== init DL ========')
    # 効果音ラボからDL
    url = 'https://soundeffect-lab.info/sound/machine/mp3/camera-shutter1.mp3'
    filename='camera-shutter1.mp3'
    is_file = os.path.isfile(filename)
    if not is_file:
        urlData = requests.get(url).content
        with open(filename ,mode='wb') as f: # wb でバイト型を書き込める
            f.write(urlData)
        
    url = 'https://soundeffect-lab.info/sound/button/mp3/decision13.mp3'
    filename='decision13.mp3'
    is_file = os.path.isfile(filename)
    if not is_file:
        urlData = requests.get(url).content
        with open(filename ,mode='wb') as f: # wb でバイト型を書き込める
            f.write(urlData)
        
    url = 'https://soundeffect-lab.info/sound/anime/mp3/correct2.mp3'
    filename='correct2.mp3'
    is_file = os.path.isfile(filename)
    if not is_file:
        urlData = requests.get(url).content
        with open(filename ,mode='wb') as f: # wb でバイト型を書き込める
            f.write(urlData)



if __name__ == "__main__": 
    init_()
    play(2) # 音が鳴ったら 準備OK 
    print('======== main ========')
    # face_cap('img.jpg')
    main() 
