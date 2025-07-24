#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

class ProbabilityConverter:
    def __init__(self):
        self.MAX_PROBABILITY = 1000000000  # 십억분율 (1,000,000,000 = 100%)
        self.scale_name = "십억분율"
    
    def percentage_to_parts(self, percentage):
        """백분율을 설정된 스케일로 변환"""
        return int(percentage * (self.MAX_PROBABILITY / 100))
    
    def parts_to_percentage(self, parts):
        """설정된 스케일을 백분율로 변환"""
        return parts / (self.MAX_PROBABILITY / 100)
    
    def calculate_item_probability(self, group_total_probability, item_percentage):
        """
        그룹 내 아이템의 개별 확률을 전체 확률 기준으로 계산
        
        Args:
            group_total_probability (int): 그룹의 전체 확률 (설정된 스케일)
            item_percentage (float): 그룹 내 아이템의 확률 (백분율)
        
        Returns:
            int: 전체 확률 기준 아이템 확률 (설정된 스케일)
        """
        # 그룹 확률의 백분율 계산
        group_percentage = self.parts_to_percentage(group_total_probability)
        
        # 전체 기준 아이템 확률 계산
        total_item_percentage = (group_percentage * item_percentage) / 100
        
        # 설정된 스케일로 변환
        total_item_probability = self.percentage_to_parts(total_item_percentage)
        
        return total_item_probability
    
    def calculate_multiple_items(self, group_total_probability, items):
        """
        여러 아이템의 확률을 한번에 계산
        
        Args:
            group_total_probability (int): 그룹의 전체 확률 (설정된 스케일)
            items (dict): {아이템_id: 그룹내_확률(백분율)} 형태
        
        Returns:
            dict: {아이템_id: 전체_확률(설정된 스케일)} 형태
        """
        results = {}
        
        for item_id, item_percentage in items.items():
            item_probability = self.calculate_item_probability(group_total_probability, item_percentage)
            results[item_id] = item_probability
        
        return results
    
    def validate_percentages(self, percentages):
        """그룹 내 확률의 합이 100%인지 검증"""
        total = sum(percentages.values())
        return abs(total - 100.0) < 0.01, total  # 소수점 오차 고려


def main():
    st.set_page_config(
        page_title="드랍률 계산기",
        page_icon="🎲",
        layout="wide"
    )
    
    st.title("🎲 드랍률 계산기")
    st.markdown("---")
    
    converter = ProbabilityConverter()
    
    # 메인 컨텐츠
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("⚙️ 설정")
        
        # 그룹 전체 확률 입력
        group_total = st.number_input(
            f"그룹 전체 확률 ({converter.scale_name})",
            min_value=1,
            max_value=converter.MAX_PROBABILITY,
            value=500000000,
            step=10000000
        )
        
        group_percentage = converter.parts_to_percentage(group_total)
        st.info(f"그룹 확률: {group_percentage:.3f}%")
        
        st.subheader("🎯 아이템 정보")
        
        # 세션 상태 초기화
        if 'items' not in st.session_state:
            st.session_state['items'] = {}
        
        # 아이템 추가 폼
        with st.form("add_item_form"):
            col_id, col_prob = st.columns([1, 1])
            
            with col_id:
                item_id = st.text_input("아이템 ID")
            
            with col_prob:
                item_prob = st.number_input(
                    "그룹 내 확률 (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=0.01,
                    format="%.2f"
                )
            
            submit_button = st.form_submit_button("아이템 추가")
            
            if submit_button and item_id:
                if item_id in st.session_state['items']:
                    st.error(f"'{item_id}'는 이미 존재하는 아이템 ID입니다.")
                else:
                    st.session_state['items'][item_id] = item_prob
                    st.success(f"'{item_id}' 아이템이 추가되었습니다.")
                    st.rerun()
        
        # 현재 아이템 목록
        if st.session_state['items']:
            st.subheader("📝 현재 아이템 목록")
            
            items_data = []
            for item_id, prob in st.session_state['items'].items():
                items_data.append({"아이템 ID": item_id, "그룹 내 확률 (%)": prob})
            
            df_items = pd.DataFrame(items_data)
            st.dataframe(df_items, use_container_width=True)
            
            # 아이템 삭제
            item_to_remove = st.selectbox("삭제할 아이템 선택", ["선택하세요"] + list(st.session_state['items'].keys()))
            
            if st.button("선택한 아이템 삭제") and item_to_remove != "선택하세요":
                del st.session_state['items'][item_to_remove]
                st.success(f"'{item_to_remove}' 아이템이 삭제되었습니다.")
                st.rerun()
            
            # 모든 아이템 삭제
            if st.button("모든 아이템 삭제", type="secondary"):
                st.session_state['items'] = {}
                st.success("모든 아이템이 삭제되었습니다.")
                st.rerun()
    
    with col2:
        st.header("📊 계산 결과")
        
        if st.session_state['items']:
            # 확률 검증
            is_valid, total_percentage = converter.validate_percentages(st.session_state['items'])
            
            if not is_valid:
                st.warning(f"⚠️ 그룹 내 확률의 합이 100%가 아닙니다. (현재: {total_percentage:.2f}%)")
            else:
                st.success("✅ 그룹 내 확률의 합이 100%입니다.")
            
            # 계산 수행
            results = converter.calculate_multiple_items(group_total, st.session_state['items'])
            
            # 결과 테이블 생성
            result_data = []
            total_calculated = 0
            
            for item_id, group_prob in st.session_state['items'].items():
                total_prob = results[item_id]
                total_percentage_calc = converter.parts_to_percentage(total_prob)
                total_calculated += total_prob
                
                result_data.append({
                    "아이템 ID": item_id,
                    "그룹 내 확률 (%)": f"{group_prob:.2f}%",
                    f"전체 확률 ({converter.scale_name})": f"{total_prob:,}",
                    "전체 확률 (%)": f"{total_percentage_calc:.4f}%"
                })
            
            # 합계 행 추가
            result_data.append({
                "아이템 ID": "합계",
                "그룹 내 확률 (%)": "100.00%",
                f"전체 확률 ({converter.scale_name})": f"{total_calculated:,}",
                "전체 확률 (%)": f"{converter.parts_to_percentage(total_calculated):.4f}%"
            })
            
            df_results = pd.DataFrame(result_data)
            st.dataframe(df_results, use_container_width=True)
            
            # 시각화
            st.subheader("📈 시각화")
            
            # 파이 차트용 데이터 준비
            chart_data = []
            for item_id, group_prob in st.session_state['items'].items():
                total_prob = results[item_id]
                total_percentage_calc = converter.parts_to_percentage(total_prob)
                chart_data.append({
                    "아이템": item_id,
                    "전체 확률 (%)": total_percentage_calc,
                    converter.scale_name: total_prob
                })
            
            df_chart = pd.DataFrame(chart_data)
            
            # 파이 차트
            fig_pie = px.pie(
                df_chart, 
                values="전체 확률 (%)", 
                names="아이템",
                title="아이템별 전체 확률 분포",
                hover_data=[converter.scale_name]
            )
            fig_pie.update_traces(textinfo='label+percent')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("아이템을 추가하여 계산을 시작하세요.")


if __name__ == "__main__":
    main()
