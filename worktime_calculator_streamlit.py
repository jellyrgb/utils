import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta
import pandas as pd
import math
import json
import os
import uuid
import time

class WorkTimeCalculatorStreamlit:
    def __init__(self):
        self.days = ['월요일', '화요일', '수요일', '목요일', '금요일']
        self.data_dir = 'user_data'  # 사용자 데이터 저장 디렉토리
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """데이터 저장 디렉토리가 없으면 생성"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def get_user_id(self):
        """간단한 브라우저 세션 기반 사용자 ID 관리"""
        # URL 파라미터에서 사용자 ID 확인
        query_params = st.query_params
        url_user_id = query_params.get('uid')
        
        if url_user_id and 'user_id' not in st.session_state:
            # URL에 uid가 있으면 사용 (기존 사용자가 북마크한 경우)
            st.session_state.user_id = url_user_id
            
            # 데이터 파일 존재 여부로 신규/기존 판단
            data_file = os.path.join(self.data_dir, f"worktime_data_{url_user_id}.json")
            if os.path.exists(data_file):
                st.session_state.is_returning_user = True
            else:
                st.session_state.is_new_user = True
                
        elif 'user_id' not in st.session_state:
            # 새 사용자라면 ID 생성
            new_user_id = f"user{str(uuid.uuid4())[:8]}"
            st.session_state.user_id = new_user_id
            st.session_state.is_new_user = True
            
            # URL에 사용자 ID 추가
            st.query_params['uid'] = new_user_id
        
        return st.session_state.user_id
    
        return st.session_state.user_id
    
    def is_new_user(self):
        """새로운 사용자인지 확인"""
        return st.session_state.get('is_new_user', False)
    
    def is_returning_user(self):
        """돌아온 사용자인지 확인"""
        return st.session_state.get('is_returning_user', False)
    
    def get_user_data_file(self):
        """사용자별 데이터 파일 경로 반환"""
        user_id = self.get_user_id()
        filename = f"worktime_data_{user_id}.json"
        return os.path.join(self.data_dir, filename)
    
    def save_data_to_file(self, work_times, week_label):
        """근무시간 데이터를 사용자별 파일에 저장"""
        try:
            data_file = self.get_user_data_file()
            
            # 기존 데이터 로드
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
            else:
                saved_data = {}
            
            # 새 데이터 추가
            saved_data[week_label] = work_times
            
            # 파일에 저장
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(saved_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"데이터 저장 중 오류가 발생했습니다: {e}")
            return False
    
    def load_data_from_file(self):
        """사용자별 파일에서 저장된 근무시간 데이터를 불러오기"""
        try:
            data_file = self.get_user_data_file()
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
            return {}
    
    def get_saved_dates(self):
        """저장된 데이터의 날짜 목록 반환"""
        data = self.load_data_from_file()
        return list(data.keys()) if data else []
    
    def time_to_minutes(self, time_str):
        """시간 문자열을 분으로 변환"""
        try:
            if not time_str or not time_str.strip():
                return 0
            # HH:MM 형식 파싱
            if ':' in time_str:
                hour, minute = map(int, time_str.split(':'))
            else:
                return 0
            return hour * 60 + minute
        except:
            return 0
    
    def minutes_to_hours(self, minutes):
        """분을 시간(소수점)으로 변환"""
        return math.floor(minutes / 60 * 100) / 100
    
    def calculate_work_hours(self, start_time, end_time):
        """근무시간 계산 (점심시간, 저녁시간 제외)"""
        if not start_time or not end_time:
            return 0
        
        start_minutes = self.time_to_minutes(start_time)
        end_minutes = self.time_to_minutes(end_time)
        
        if start_minutes >= end_minutes:
            return 0
        
        total_minutes = end_minutes - start_minutes
        
        # 점심시간 제외 (12:30-13:30)
        lunch_start = 12 * 60 + 30  # 12:30
        lunch_end = 13 * 60 + 30    # 13:30
        
        if start_minutes < lunch_end and end_minutes > lunch_start:
            # 점심시간과 겹치는 경우
            overlap_start = max(start_minutes, lunch_start)
            overlap_end = min(end_minutes, lunch_end)
            total_minutes -= (overlap_end - overlap_start)
        
        # 저녁시간 제외 (18:30-19:30)
        dinner_start = 18 * 60 + 30  # 18:30
        dinner_end = 19 * 60 + 30    # 19:30
        
        if start_minutes < dinner_end and end_minutes > dinner_start:
            # 저녁시간과 겹치는 경우
            overlap_start = max(start_minutes, dinner_start)
            overlap_end = min(end_minutes, dinner_end)
            total_minutes -= (overlap_end - overlap_start)
        
        return max(0, total_minutes)
    
    def get_current_week_label(self):
        """현재 주차를 월별로 표현"""
        today = datetime.now()
        # 해당 월의 첫 번째 날
        first_day = today.replace(day=1)
        
        # 해당 월의 첫 번째 월요일 찾기
        # 만약 1일이 월요일이 아니라면, 다음 월요일을 찾음
        days_until_monday = (7 - first_day.weekday()) % 7
        if days_until_monday == 0 and first_day.weekday() != 0:
            days_until_monday = 7
        
        first_monday = first_day + timedelta(days=days_until_monday)
        
        # 현재 날짜가 첫 번째 월요일보다 이전이면 1주차
        if today < first_monday:
            week_number = 1
        else:
            # 첫 번째 월요일부터 몇 주가 지났는지 계산
            week_number = ((today - first_monday).days // 7) + 2
        
        return f"{today.month}월 {week_number}주차"
    
    def get_today_index(self):
        """오늘 요일의 인덱스 반환 (0=월요일)"""
        today = datetime.now().weekday()  # 0=월요일, 6=일요일
        return min(today, 4)  # 금요일까지만

def main():
    st.set_page_config(
        page_title="근무시간 계산기",
        page_icon="⏰",
        layout="centered"
    )
    
    calculator = WorkTimeCalculatorStreamlit()
    
    # 제목
    st.title("근무시간 계산기")
    
    # 사용자 자동 인식 및 표시
    user_id = calculator.get_user_id()
    
    # 사용자 정보를 상단에 간단히 표시
    col_user_info, col_user_actions = st.columns([3, 1])
    
    with col_user_info:
        if calculator.is_new_user():
            st.success(f"🎉 새로운 사용자로 등록되었습니다! (ID: **{user_id}**)")
            st.info("💡 **팁**: 이 페이지를 북마크해두시면 언제든 자신의 데이터에 접근할 수 있어요!")
            st.session_state.is_new_user = False  # 메시지 한 번만 표시
        elif calculator.is_returning_user():
            st.success(f"👋 다시 오신 것을 환영합니다! (ID: **{user_id}**)")
            st.session_state.is_returning_user = False  # 메시지 한 번만 표시
        else:
            st.info(f"👤 사용자 ID: **{user_id}**")
    
    with col_user_actions:
        # 고급 옵션을 expander로 숨김
        with st.expander("🔧 설정"):
            st.write("**사용자 ID 변경**")
            new_id = st.text_input("새 ID", value=user_id, key="new_user_id")
            if st.button("ID 변경") and new_id != user_id:
                st.session_state.user_id = new_id
                st.query_params['uid'] = new_id
                st.rerun()
            
            if st.button("새 ID 생성"):
                new_generated_id = f"user{str(uuid.uuid4())[:8]}"
                st.session_state.user_id = new_generated_id
                st.query_params['uid'] = new_generated_id
                st.rerun()
                st.rerun()
    
    st.markdown("---")
    
    # 데이터 저장/로드 섹션
    st.markdown("### 데이터 관리")
    
    col_load, col_delete = st.columns([1, 1])
    
    with col_load:
        # 저장된 데이터 로드
        saved_dates = calculator.get_saved_dates()
        if saved_dates:
            selected_date = st.selectbox("불러올 데이터", ["선택하세요"] + saved_dates)
            if selected_date != "선택하세요":
                if st.button("데이터 불러오기"):
                    saved_data = calculator.load_data_from_file()
                    if selected_date in saved_data:
                        # 세션 상태 업데이트
                        st.session_state.work_times = saved_data[selected_date]
                        
                        # 입력 필드 강제 업데이트를 위해 키 초기화
                        for day in calculator.days:
                            start_key = f"start_{day}"
                            end_key = f"end_{day}"
                            if start_key in st.session_state:
                                del st.session_state[start_key]
                            if end_key in st.session_state:
                                del st.session_state[end_key]
                        
                        st.success(f"{selected_date} 데이터를 불러왔습니다!")
                        st.rerun()
        else:
            st.info("저장된 데이터가 없습니다")
    
    with col_delete:
        # 저장된 데이터 삭제
        if saved_dates:
            delete_date = st.selectbox("삭제할 데이터", ["선택하세요"] + saved_dates, key="delete_select")
            if delete_date != "선택하세요":
                if st.button("데이터 삭제", type="secondary"):
                    saved_data = calculator.load_data_from_file()
                    if delete_date in saved_data:
                        del saved_data[delete_date]
                        # 파일에 다시 저장
                        data_file = calculator.get_user_data_file()
                        with open(data_file, 'w', encoding='utf-8') as f:
                            json.dump(saved_data, f, ensure_ascii=False, indent=2)
                        st.success(f"{delete_date} 데이터가 삭제되었습니다!")
                        st.rerun()
    
    st.markdown("---")
    
    # 세션 상태 초기화
    if 'work_times' not in st.session_state:
        # 저장된 데이터가 있다면 자동으로 최신 데이터 로드
        saved_data = calculator.load_data_from_file()
        if saved_data:
            # 가장 최근 주차 데이터 자동 로드
            latest_week = max(saved_data.keys()) if saved_data else None
            if latest_week:
                st.session_state.work_times = saved_data[latest_week]
                st.info(f"자동으로 {latest_week} 데이터를 불러왔습니다.")
            else:
                st.session_state.work_times = {}
                for day in calculator.days:
                    st.session_state.work_times[day] = {'start': '', 'end': ''}
        else:
            st.session_state.work_times = {}
            for day in calculator.days:
                st.session_state.work_times[day] = {'start': '', 'end': ''}
    
    # 헤더
    col1, col2, col3, col4 = st.columns([1.5, 2, 2, 1.5])
    with col1:
        st.markdown("<div style='text-align: center'><strong>요일</strong></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='text-align: center'><strong>출근시간</strong></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div style='text-align: center'><strong>퇴근시간</strong></div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div style='text-align: center'><strong>근무시간</strong></div>", unsafe_allow_html=True)
    
    st.markdown("<hr style='margin-top: 0px; margin-bottom: 1rem; border: none; border-top: 1px solid #e6e6e6;'>", unsafe_allow_html=True)
    
    # 테이블 형태로 입력 받기
    total_work_minutes = 0
    
    for i, day in enumerate(calculator.days):
        col1, col2, col3, col4 = st.columns([1.5, 2, 2, 1.5])
        
        with col1:
            st.write(f"**{day}**")
        
        with col2:
            start_key = f"start_{day}"
            # 세션 상태에서 기본값 가져오기
            default_start = st.session_state.work_times[day]['start'] if day in st.session_state.work_times else ''
            start_time = st.text_input(
                "출근시간",
                value=default_start,
                key=start_key,
                placeholder="09:30",
                label_visibility="collapsed"
            )
            st.session_state.work_times[day]['start'] = start_time
        
        with col3:
            end_key = f"end_{day}"
            # 세션 상태에서 기본값 가져오기
            default_end = st.session_state.work_times[day]['end'] if day in st.session_state.work_times else ''
            end_time = st.text_input(
                "퇴근시간",
                value=default_end,
                key=end_key,
                placeholder="18:30",
                label_visibility="collapsed"
            )
            st.session_state.work_times[day]['end'] = end_time
        
        with col4:
            # 일일 근무시간 계산
            work_minutes = calculator.calculate_work_hours(start_time, end_time)
            work_hours = calculator.minutes_to_hours(work_minutes)
            
            if work_hours > 0:
                st.write(f"**{work_hours:.2f}시간**")
                total_work_minutes += work_minutes
            else:
                st.write("0.00시간")
    
    # 결과 표시
    st.write("")
    
    # 전체 근무시간
    total_hours = calculator.minutes_to_hours(total_work_minutes)
    
    # 오늘까지 근무시간
    today_index = calculator.get_today_index()
    today_minutes = 0
    
    for i in range(today_index + 1):
        day = calculator.days[i]
        start_time = st.session_state.work_times[day]['start']
        end_time = st.session_state.work_times[day]['end']
        today_minutes += calculator.calculate_work_hours(start_time, end_time)
    
    today_hours = calculator.minutes_to_hours(today_minutes)
    today_name = calculator.days[today_index]
    
    # 결과 표시 (예쁘게)
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(
            f"""
            <div style='background-color: #f8f9fa; padding: 12px; border-radius: 6px; text-align: center; border-left: 4px solid #007bff;'>
                <div style='color: #6c757d; font-size: 13px; margin-bottom: 4px;'>총 근무시간</div>
                <div style='color: #007bff; font-size: 18px; font-weight: bold;'>{total_hours:.2f} 시간</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f"""
            <div style='background-color: #f8f9fa; padding: 12px; border-radius: 6px; text-align: center; border-left: 4px solid #28a745; margin-bottom: 20px;'>
                <div style='color: #6c757d; font-size: 13px; margin-bottom: 4px;'>{today_name}까지</div>
                <div style='color: #28a745; font-size: 18px; font-weight: bold;'>{today_hours:.2f} 시간</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # 버튼들
    col_reset, col_quick_save = st.columns([1, 1])
    
    with col_reset:
        # 초기화 버튼
        if st.button("초기화", type="secondary"):
            # 세션 상태 초기화
            for day in calculator.days:
                st.session_state.work_times[day] = {'start': '', 'end': ''}
            
            # 입력 필드 강제 업데이트를 위해 키 초기화
            for day in calculator.days:
                start_key = f"start_{day}"
                end_key = f"end_{day}"
                if start_key in st.session_state:
                    del st.session_state[start_key]
                if end_key in st.session_state:
                    del st.session_state[end_key]
            
            st.rerun()
    
    with col_quick_save:
        # 빠른 저장 버튼
        if st.button("입력 내용 저장", type="primary"):
            current_week = calculator.get_current_week_label()
            if calculator.save_data_to_file(st.session_state.work_times, current_week):
                st.success(f"{current_week} 데이터가 저장되었습니다!")
                st.rerun()
    
if __name__ == "__main__":
    main()
