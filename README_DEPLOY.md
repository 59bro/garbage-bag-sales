# 🌐 24시간 영구 무료 모바일 웹 서버 배포 가이드 (Render)

PC를 켜두지 않아도 **스마트폰/모바일 브라우저에서 24시간 365일 어디서나 접속할 수 있는 무료 클라우드 배포 가이드**입니다.

---

## 🚀 3분 완성 무료 배포 절차 (Render.com)

Render는 전 세계 개발자들이 사용하는 **100% 영구 무료(Always Free)** 웹 호스팅 서비스입니다.

### 1단계: GitHub에 소스코드 올리기
1. [GitHub.com](https://github.com) 회원가입 및 로그인
2. 상단 `+` ➡️ `New repository` 클릭
3. Repository name: `garbage-bag-sales` 입력 후 `Create repository` 클릭
4. 현재 프로젝트 폴더 전체를 GitHub에 업로드 (push)

### 2단계: Render.com 서비스 생성
1. [Render.com](https://render.com) 접속 후 GitHub 계정으로 간편 로그인
2. Dashboard에서 **`New +`** ➡️ **`Web Service`** 클릭
3. 방금 올린 `garbage-bag-sales` 리포지토리 선택
4. 설정값 확인:
   - **Name**: `garbage-bag-sales` (원하는 이름)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn web_server:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: **`Free`** (0원 선택)
5. 하단 **`Create Web Service`** 버튼 클릭!

---

## 🎉 배포 완료!

약 1~2분 후 배포가 완료되면 Render 상단에 전용 접속 주소가 생성됩니다.
> 예시: `https://garbage-bag-sales.onrender.com`

* **스마트폰 접속**: 위 생성된 주소를 카카오톡으로 전달하거나 스마트폰 크롬/사파리에 입력하면 24시간 언제 어디서나 접속 가능합니다!
* **앱처럼 사용**: 스마트폰 브라우저 메뉴 ➡️ **'홈 화면에 추가'**
