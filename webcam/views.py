from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse
import cv2
from ultralytics import YOLO
import os
from datetime import datetime
import requests
from django.http import JsonResponse
from django.contrib import messages



# YOLO 모델 로드
model = YOLO('./model/best.pt')

# 웹캠 열기
cap = cv2.VideoCapture(0)

# 웹캠이 열렸는지 확인
if not cap.isOpened():
    raise RuntimeError("Error: Could not open webcam.")

# 폭력 감지 상태 추적 변수
consecutive_violence_count = 0
violence_threshold = 5  # 연속 감지 횟수를 5로 변경

# output 폴더 생성 (없으면)
output_folder = 'output'
os.makedirs(output_folder, exist_ok=True)

def generate_frames():
    global consecutive_violence_count

    while True:
        success, frame = cap.read()
        if not success:
            break

        # 객체 탐지 수행
        results = model.predict(frame)
        violence_detected = False

        # 탐지 결과 화면에 표시
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                label_idx = int(box.cls[0].item())  # 텐서 값을 정수형으로 변환
                label = model.names[label_idx]
                confidence = box.conf[0]

                # 폭력 감지 여부 판단 
                if confidence > 0.75:  # 신뢰도 기준
                    violence_detected = True

                # 사각형 그리기
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                # 레이블 및 신뢰도 표시
                cv2.putText(frame, f'{label} {confidence:.2f}', (int(x1), int(y1) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 폭력 감지된 경우 연속 횟수 카운트
        if violence_detected:
            consecutive_violence_count += 1
        else:
            consecutive_violence_count = 0

        # 연속으로 5번 이상 폭력 감지된 경우 프레임 저장
        if consecutive_violence_count >= violence_threshold:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(output_folder, f'violence_detected_{timestamp}.jpg')
            cv2.imwrite(file_path, frame)
            print(f'Violence detected. Frame saved to {file_path}')
            consecutive_violence_count = 0  # 카운트 리셋

        # 프레임을 JPEG 형식으로 인코딩
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue  # 인코딩 실패 시 프레임 전송하지 않음
        frame = buffer.tobytes()

        # 각 프레임을 클라이언트에 전송
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        

def webcam_stream(request, id):
    print(id)
    # HTML 페이지 렌더링
    return render(request, 'webcam.html')

def video_feed(request):
    # 비디오 피드를 클라이언트에 스트리밍
    return StreamingHttpResponse(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')


def index(request):
    return render(request, 'index.html')


def login(request):
    if request.method == "GET":
        return render(request, 'login.html')
    
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    # 외부 URL 설정
    url = 'https://poksin-backend.store/login'
    payload = {
        'username': username,
        'password': password
    }
    
    try:
        # POST 요청
        response = requests.post(url, data=payload)

        
        # 응답 상태 코드가 200이면 JSON 응답을 처리
        if response.status_code == 200:
            response_data = response.json()
            user_id = response_data.get('data', {}).get('userId')

            if user_id is not None:
                return redirect('webcam-stream', user_id)
            
            if user_id is None:
                messages.error(request, '로그인에 실패했습니다: userId를 찾을 수 없습니다.')

            else:
                messages.error(request, '로그인에 실패했습니다.')

        else:
            messages.error(request, f'로그인에 실패했습니다: 상태 코드 {response.status_code} 아이디와 비밀번호를 확인하세요')

    except requests.RequestException as e:
        # 요청 중 오류가 발생한 경우
        messages.error(request, f'요청 중 오류가 발생했습니다: {e}')

    except ValueError as e:
        messages.error(request, f'요청 중 오류가 발생했습니다: {e}')

    return redirect('login')
    




    