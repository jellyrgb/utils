import streamlit as st
import os
import json
import uuid
from datetime import datetime, timedelta

# --- 0. 사용자 목록 정의 (9명) ---
USER_LIST = ["이주호", "황인섭", "최태경", "김시우", "윤석준", "오진호", "김효민", "윤현준", "김재민"]
# ----------------------------------------------------------------------

# --- 1. Session State 초기화 및 사용자 관리 ---
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = USER_LIST[0]
if 'work_times' not in st.session_state:
    st.session_state.work_times = {}
# -----------------------------------------------

class WorkTimeCalculatorStreamlit:
    def __init__(self):
        self.days = ['월요일', '화요일', '수요일', '목요일', '금요일']
        self.data_dir = 'user_data'
        self.ensure_data_directory()

    def ensure_data_directory(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def get_user_data_file(self, username):
        filename = f"worktime_data_{username}.json"
        return os.path.join(self.data_dir, filename)

    def load_data_from_file(self, username):
        data_file = self.get_user_data_file(username)
        try:
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
            return {}

    def save_data_to_file(self, username, work_times, week_label):
        data_file = self.get_user_data_file(username)
        try:
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
            else:
                saved_data = {}
            saved_data[week_label] = work_times
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(saved_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"데이터 저장 중 오류가 발생했습니다: {e}")
            return False

    def get_saved_dates(self, username):
        data = self.load_data_from_file(username)
        return sorted(list(data.keys())) if data else []

    def calculate_work_hours(self, start_time, end_time):
        if not start_time or not end_time: return 0
        try:
            start_hour, start_minute = map(int, start_time.split(':'))
            end_hour, end_minute = map(int, end_time.split(':'))
            start_minutes = start_hour * 60 + start_minute
            end_minutes = end_hour * 60 + end_minute
            
            if start_minutes >= end_minutes: return 0
            
            total_minutes = end_minutes - start_minutes
            lunch_start = 12 * 60 + 30
            lunch_end = 13 * 60 + 30
            if start_minutes < lunch_end and end_minutes > lunch_start:
                total_minutes -= min(end_minutes, lunch_end) - max(start_minutes, lunch_start)

            dinner_start = 18 * 60 + 30
            dinner_end = 19 * 60 + 30
            if start_minutes < dinner_end and end_minutes > dinner_start:
                total_minutes -= min(end_minutes, dinner_end) - max(start_minutes, dinner_end)
            
            return max(0, total_minutes)
        except (ValueError, IndexError):
            return 0

    def minutes_to_hours(self, minutes):
        return round(minutes / 60, 2)

    def get_current_week_label(self):
        today = datetime.now()
        first_day_of_month = today.replace(day=1)
        first_monday_of_month = first_day_of_month + timedelta(days=(0 - first_day_of_month.weekday() + 7) % 7)
        if today < first_monday_of_month:
            week_number = 1
        else:
            week_number = ((today - first_monday_of_month).days // 7) + 2
        return f"{today.month}월 {week_number}주차"

def main():
    st.set_page_config(
        page_title="근무시간 계산기",
        page_icon="⏰",
        layout="centered"
    )
    
    calculator = WorkTimeCalculatorStreamlit()

    # --- 2. 3x3 버튼 레이아웃으로 사용자 선택 ---
    st.sidebar.title("사용자 선택")
    st.sidebar.write("본인 이름을 클릭하세요.")

    cols = st.sidebar.columns(3)
    for i, user in enumerate(USER_LIST):
        with cols[i % 3]:
            if st.button(user, key=f"user_btn_{user}", use_container_width=True):
                st.session_state.selected_user = user
                saved_data = calculator.load_data_from_file(user)
                latest_week = max(saved_data.keys(), default=None)
                if latest_week:
                    st.session_state.work_times = saved_data[latest_week]
                else:
                    st.session_state.work_times = {day: {'start': '', 'end': ''} for day in calculator.days}
                st.rerun()

    st.sidebar.success(f"현재 선택된 사용자: **{st.session_state.selected_user}**")
    
    # --- 메인 페이지 UI ---
    st.title(f"근무시간 계산기")
    st.subheader(f"({st.session_state.selected_user}님)")
    
    # 데이터 관리 섹션
    st.markdown("### 데이터 관리")
    col_load, col_delete = st.columns([1, 1])
    
    with col_load:
        saved_dates = calculator.get_saved_dates(st.session_state.selected_user)
        selected_date = st.selectbox("불러올 데이터", ["선택하세요"] + saved_dates, key="load_select")
        if selected_date != "선택하세요":
            if st.button("데이터 불러오기", key="load_btn"):
                saved_data = calculator.load_data_from_file(st.session_state.selected_user)
                st.session_state.work_times = saved_data.get(selected_date, {})
                st.success(f"**{selected_date}** 데이터를 불러왔습니다!")
                st.rerun()

    with col_delete:
        saved_dates_delete = calculator.get_saved_dates(st.session_state.selected_user)
        delete_date = st.selectbox("삭제할 데이터", ["선택하세요"] + saved_dates_delete, key="delete_select")
        if delete_date != "선택하세요":
            if st.button("데이터 삭제", type="secondary"):
                saved_data = calculator.load_data_from_file(st.session_state.selected_user)
                if delete_date in saved_data:
                    del saved_data[delete_date]
                    data_file = calculator.get_user_data_file(st.session_state.selected_user)
                    with open(data_file, 'w', encoding='utf-8') as f:
                        json.dump(saved_data, f, ensure_ascii=False, indent=2)
                    st.success(f"**{delete_date}** 데이터가 삭제되었습니다!")
                    st.rerun()

    st.markdown("---")
    
    # 데이터 입력 및 계산 섹션
    total_work_minutes = 0
    today_index = datetime.now().weekday() if datetime.now().weekday() < 5 else 4
    today_minutes = 0
    
    header_cols = st.columns([1.5, 2, 2, 1.5])
    with header_cols[0]: st.markdown("<div style='text-align: center'><strong>요일</strong></div>", unsafe_allow_html=True)
    with header_cols[1]: st.markdown("<div style='text-align: center'><strong>출근시간</strong></div>", unsafe_allow_html=True)
    with header_cols[2]: st.markdown("<div style='text-align: center'><strong>퇴근시간</strong></div>", unsafe_allow_html=True)
    with header_cols[3]: st.markdown("<div style='text-align: center'><strong>근무시간</strong></div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top: 0px; margin-bottom: 1rem; border: none; border-top: 1px solid #e6e6e6;'>", unsafe_allow_html=True)

    for i, day in enumerate(calculator.days):
        cols = st.columns([1.5, 2, 2, 1.5])
        with cols[0]: st.write(f"**{day}**")
        with cols[1]:
            start_key = f"start_{day}"
            start_value = st.session_state.work_times.get(day, {}).get('start', '')
            start_time = st.text_input("출근시간", value=start_value, key=start_key, placeholder="09:30", label_visibility="collapsed")
            st.session_state.work_times.setdefault(day, {})['start'] = start_time
        with cols[2]:
            end_key = f"end_{day}"
            end_value = st.session_state.work_times.get(day, {}).get('end', '')
            end_time = st.text_input("퇴근시간", value=end_value, key=end_key, placeholder="18:30", label_visibility="collapsed")
            st.session_state.work_times.setdefault(day, {})['end'] = end_time

        work_minutes = calculator.calculate_work_hours(start_time, end_time)
        with cols[3]:
            if work_minutes > 0:
                st.write(f"**{calculator.minutes_to_hours(work_minutes):.2f}시간**")
                total_work_minutes += work_minutes
            else:
                st.write("0.00시간")

        if i <= today_index:
            today_minutes += work_minutes

    st.markdown("---")
    
    col_total, col_today = st.columns([1, 1])
    with col_total:
        st.markdown(f"""
        <div style='background-color: #f8f9fa; padding: 12px; border-radius: 6px; text-align: center; border-left: 4px solid #007bff;'>
            <div style='color: #6c7d; font-size: 13px; margin-bottom: 4px;'>총 근무시간</div>
            <div style='color: #007bff; font-size: 18px; font-weight: bold;'>{calculator.minutes_to_hours(total_work_minutes):.2f} 시간</div>
        </div>
        """, unsafe_allow_html=True)

    with col_today:
        st.markdown(f"""
        <div style='background-color: #f8f9fa; padding: 12px; border-radius: 6px; text-align: center; border-left: 4px solid #28a745;'>
            <div style='color: #6c7d; font-size: 13px; margin-bottom: 4px;'>오늘까지 ({calculator.days[today_index]})</div>
            <div style='color: #28a745; font-size: 18px; font-weight: bold;'>{calculator.minutes_to_hours(today_minutes):.2f} 시간</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col_reset, col_save = st.columns([1, 1])
    with col_reset:
        if st.button("초기화", type="secondary"):
            st.session_state.work_times = {day: {'start': '', 'end': ''} for day in calculator.days}
            st.rerun()
    with col_save:
        if st.button("입력 내용 저장", type="primary"):
            current_week = calculator.get_current_week_label()
            if calculator.save_data_to_file(st.session_state.selected_user, st.session_state.work_times, current_week):
                st.success(f"**{st.session_state.selected_user}**님의 **{current_week}** 데이터가 저장되었습니다! 💾")
                st.rerun()

if __name__ == "__main__":
    main()