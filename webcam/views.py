import os
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import requests
from django.contrib import messages
import boto3
from dotenv import load_dotenv
from datetime import datetime
from .models import EvidenceEntity, CategoryEntity
import logging
import json

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
s3_folder = 'live/'

@csrf_exempt
def upload_video(request):
    logger.debug('upload_video called')
    
    if request.method == 'POST' and 'video' in request.FILES:
        video = request.FILES['video']
        user_id = request.POST.get('user_id')
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        s3_key = f"{s3_folder}{timestamp}.mp4"
        file_url = f"https://{bucket_name}.s3.{aws_region}.amazonaws.com/{s3_key}"
        file_url_list = json.dumps([file_url])  # Convert URL to JSON list

        logger.debug(f'Video received: {video}')
        logger.debug(f'S3 key: {s3_key}')
        logger.debug(f'File URL: {file_url}')
        logger.debug(f'User ID: {user_id}')

        try:
            s3_client.upload_fileobj(video, bucket_name, s3_key)
            logger.debug('Video uploaded to S3')

            # 카테고리 조회 (예: 'VIDEO' 카테고리)
            try:
                category = CategoryEntity.objects.get(name='VIDEO')
            except CategoryEntity.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Category not found.'})

            # 데이터베이스에 저장
            evidence = EvidenceEntity(
                description='Webcam video',
                fileUrls=file_url_list,  # Save as JSON list
                title=f"Video at {timestamp}",
                category_id=category,  # 올바른 카테고리 객체 사용
                user_id=user_id
            )
            evidence.save()
            logger.debug('Video saved to database')

            # 데이터 저장 후 POST 요청 보내기
            post_url = 'http://43.201.133.81/detect-violence/'
            payload = {
                'evidence_id': evidence.id,
                'file_name': s3_key.split('/')[1]
            }
            headers = {'Content-Type': 'application/json'}
            try:
                response = requests.post(post_url, data=json.dumps(payload), headers=headers)
                if response.status_code == 200:
                    logger.debug('POST request to detect-violence successful')
                else:
                    logger.error(f'POST request to detect-violence failed with status code {response.status_code}')
            except requests.RequestException as e:
                logger.error(f'Error sending POST request to detect-violence: {e}')

            return JsonResponse({'status': 'success', 'message': 'Video uploaded and saved successfully.'})
        except Exception as e:
            logger.error(f'Error uploading video: {e}')
            return JsonResponse({'status': 'error', 'message': str(e)})

    logger.error('Invalid request: no video found or method is not POST')
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

def webcam_stream(request, id):
    return render(request, 'webcam.html', {"id": id})

def index(request):
    return render(request, 'index.html')

def login(request):
    if request.method == "GET":
        return render(request, 'login.html')
    
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    url = 'https://poksin-backend.store/login'
    payload = {
        'username': username,
        'password': password
    }
    
    try:
        response = requests.post(url, data=payload)
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
        messages.error(request, f'요청 중 오류가 발생했습니다: {e}')
    except ValueError as e:
        messages.error(request, f'요청 중 오류가 발생했습니다: {e}')

    return redirect('login')
