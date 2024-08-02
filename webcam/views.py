import os
from django.shortcuts import render, redirect
import requests
from django.contrib import messages
import boto3
from dotenv import load_dotenv


# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수에서 AWS 자격 증명 및 기타 설정 가져오기
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION', 'ap-northeast-2')

# AWS S3 클라이언트 설정
s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

bucket_name = 'poksin'
s3_folder = 'violence-frames/'


# MySQL 데이터베이스 연결 설정
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}


def webcam_stream(request, id):
    # HTML 페이지 렌더링
    return render(request, 'webcam.html', {"id" : id})


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
            messages.error(request, f'로그인에 실패했습니다: 상태 코드 {response.status_code}\n아이디와 비밀번호를 확인하세요')

    except requests.RequestException as e:
        # 요청 중 오류가 발생한 경우
        messages.error(request, f'요청 중 오류가 발생했습니다: {e}')

    except ValueError as e:
        messages.error(request, f'요청 중 오류가 발생했습니다: {e}')

    return redirect('login')