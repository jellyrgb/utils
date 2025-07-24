import streamlit as st
from datetime import datetime
import pandas as pd
import math

class WorkTimeCalculatorStreamlit:
    def __init__(self):
        self.days = ['월요일', '화요일', '수요일', '목요일', '금요일']
    
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
    
    # 세션 상태 초기화
    if 'work_times' not in st.session_state:
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
            start_time = st.text_input(
                "출근시간",
                key=start_key,
                placeholder="09:30",
                label_visibility="collapsed"
            )
            st.session_state.work_times[day]['start'] = start_time
        
        with col3:
            end_key = f"end_{day}"
            end_time = st.text_input(
                "퇴근시간",
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
    
    # 초기화 버튼
    if st.button("초기화"):
        for day in calculator.days:
            st.session_state.work_times[day] = {'start': '', 'end': ''}
        st.rerun()
    
if __name__ == "__main__":
    main()
