import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import math
from utils.calculations import calc_heat_loss, musson_power, calculate_heating_economics
from utils.constants import MATERIALS, MUSSON_MODELS, FUEL_TYPES

# Настройка страницы
st.set_page_config(
    page_title="Калькулятор печи Муссон",
    page_icon="🔥",
    layout="wide"
)

# Загрузка стилей
def load_css():
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        color: #2E86AB;
    }
    .stButton>button {
        background-color: #2E86AB;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #1a5a7a;
    }
    </style>
    """, unsafe_allow_html=True)

load_css()

# Основная функция приложения
def main():
    st.title("🔥 Калькулятор подбора печи Муссон")

    # Боковая панель
    render_sidebar()
    
    # Параметры из сессии
    params = get_parameters_from_session()
    
    # Расчеты
    if st.sidebar.button("🔄 Рассчитать", type="primary"):
        calculate_and_display_results(params)

def render_sidebar():
    st.sidebar.header("🏭 ХАРАКТЕРИСТИКИ ПОМЕЩЕНИЯ")
    st.sidebar.markdown("---")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        area_m2 = st.number_input("Площадь помещения (м²)", 20, 500, 100, key="area")
    with col2:
        height_m = st.number_input("Высота потолков (м)", 2.0, 5.0, 3.5, key="height")

    material = st.sidebar.selectbox("Материал стен", list(MATERIALS.keys()), key="material")
    wall_thickness = st.sidebar.slider("Толщина стен (см)", 10, 100, 40, key="wall_thickness") / 100

    st.sidebar.markdown("---")
    st.sidebar.header("🪟 ОКНА И ДВЕРИ")
    windows_m2 = st.sidebar.number_input("Площадь окон (м²)", 0, 50, 10, key="windows")
    doors_m2 = st.sidebar.number_input("Площадь дверей (м²)", 0, 10, 3, key="doors")
    roof_insulation = st.sidebar.checkbox("Утеплённая крыша", value=False, key="roof")

    st.sidebar.markdown("---")
    st.sidebar.header("🌡️ ТЕМПЕРАТУРЫ")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        t_in = st.sidebar.slider("Внутренняя температура (°C)", 10, 25, 18, key="t_in")
    with col2:
        t_out = st.sidebar.slider("Наружная температура (°C)", -50, 10, -15, key="t_out")

    st.sidebar.markdown("---")
    st.sidebar.header("⚡ РЕЖИМ РАБОТЫ")
    working_hours = st.sidebar.selectbox("Рабочий день (часов)", [8, 12, 16], index=0, key="working_hours")

    st.sidebar.markdown("---")
    st.sidebar.header("🪵 ТОПЛИВО")
    fuel_type = st.sidebar.selectbox("Тип топлива", list(FUEL_TYPES.keys()), key="fuel_type")
    fill_fraction = st.sidebar.slider("Заполнение топки (%)", 50, 100, 90, key="fill_fraction") / 100
    efficiency = st.sidebar.slider("КПД котла (%)", 70, 95, 85, key="efficiency") / 100
    burn_hours = st.sidebar.selectbox("Время горения (ч)", [2, 4, 6, 12], index=2, key="burn_hours")

    # Сохраняем в сессию
    st.session_state.params = {
        'area_m2': area_m2, 'height_m': height_m, 'material': material,
        'wall_thickness': wall_thickness, 'windows_m2': windows_m2,
        'doors_m2': doors_m2, 'roof_insulation': roof_insulation,
        't_in': t_in, 't_out': t_out, 'working_hours': working_hours,
        'fuel_type': fuel_type, 'fill_fraction': fill_fraction,
        'efficiency': efficiency, 'burn_hours': burn_hours
    }

def get_parameters_from_session():
    return st.session_state.get('params', {})

def calculate_and_display_results(params):
    if not params:
        st.warning("⚠️ Заполните параметры и нажмите 'Рассчитать'")
        return

    heat_loss_kw = calc_heat_loss(
        params['area_m2'], params['height_m'], params['wall_thickness'], 
        params['material'], params['t_in'], params['t_out'], 
        params['windows_m2'], params['doors_m2'], params['roof_insulation']
    )

    volume_m3 = params['area_m2'] * params['height_m']

    display_main_metrics(heat_loss_kw, volume_m3)
    display_models_comparison(heat_loss_kw, params)
    display_recommendations(heat_loss_kw, params)

def display_main_metrics(heat_loss_kw, volume_m3):
    st.header("📊 РЕЗУЛЬТАТЫ")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Теплопотери", f"{heat_loss_kw:.1f} кВт")
    with col2:
        st.metric("Рекомендуемая мощность", f"{heat_loss_kw * 1.2:.1f} кВт")
    with col3:
        st.metric("Объём", f"{volume_m3:.0f} м³")

def display_models_comparison(heat_loss_kw, params):
    st.subheader("🔥 СРАВНЕНИЕ МОДЕЛЕЙ")

    results = []
    for model, mp in MUSSON_MODELS.items():
        useful_kwh, p_kw, m_fuel = musson_power(
            mp["volume_l"], params['fill_fraction'], 
            params['fuel_type'], params['efficiency'], params['burn_hours']
        )
        results.append({
            "model": model, 
            "power": p_kw, 
            "fuel_per_load": m_fuel,
            "volume_l": mp["volume_l"],
            "price": mp["price"]
        })

    df = pd.DataFrame(results)
    df["Соответствие"] = df["power"] >= heat_loss_kw * 1.2
    df["Рекомендация"] = df["Соответствие"].map({True: "✅ Подходит", False: "❌ Слабая"})

    show_df = df[["model", "power", "fuel_per_load", "Рекомендация"]].copy()
    show_df.columns = ["Модель", "Мощность (кВт)", "Топливо (кг)", "Рекомендация"]
    show_df["Мощность (кВт)"] = show_df["Мощность (кВт)"].round(1)
    show_df["Топливо (кг)"] = show_df["Топливо (кг)"].round(1)

    st.dataframe(show_df, use_container_width=True)

    fig, ax = plt.subplots(figsize=(8, 4))
    models = [r["model"] for r in results]
    powers = [r["power"] for r in results]
    colors = ['green' if p >= heat_loss_kw * 1.2 else 'red' for p in powers]

    bars = ax.bar(models, powers, color=colors, alpha=0.7)
    ax.axhline(y=heat_loss_kw * 1.2, color="blue", linestyle="--", 
               label=f"Требуется: {heat_loss_kw * 1.2:.1f} кВт")
    ax.set_ylabel("Мощность, кВт")
    ax.set_title("Мощность моделей")
    ax.legend()
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', alpha=0.3)

    for bar, power in zip(bars, powers):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.1,
                f'{power:.1f}', ha='center', va='bottom')

    plt.tight_layout()
    st.pyplot(fig)

def display_recommendations(heat_loss_kw, params):
    st.subheader("💡 РЕКОМЕНДАЦИИ")

    results = []
    for model, mp in MUSSON_MODELS.items():
        useful_kwh, p_kw, m_fuel = musson_power(
            mp["volume_l"], params['fill_fraction'], 
            params['fuel_type'], params['efficiency'], params['burn_hours']
        )
        results.append({"model": model, "power": p_kw, "price": mp["price"]})

    suitable = [r for r in results if r["power"] >= heat_loss_kw * 1.2]

    if suitable:
        best = min(suitable, key=lambda x: x["price"])
        display_best_model_info(best, heat_loss_kw, params)
    else:
        st.error("❌ Нет подходящей модели")
        st.write("Рекомендации: увеличьте КПД, топливо, утепление, закладку.")

def display_best_model_info(best_model, heat_loss_kw, params):
    st.success(f"**Рекомендуемая модель: {best_model['model']}**")
    st.write(f"• Мощность: {best_model['power']:.1f} кВт (нужно {heat_loss_kw*1.2:.1f} кВт)")
    st.write(f"• Время горения: до {params['burn_hours']} ч")
    st.write(f"• Цена: {best_model['price']:,} руб.".replace(',', ' '))

    economics = calculate_heating_economics(
        heat_loss_kw, best_model['power'], params['working_hours'],
        params['fuel_type'], params['efficiency'], 
        FUEL_TYPES[params['fuel_type']]["price_per_ton"]
    )
    loads = max(1, math.ceil(params['working_hours'] / params['burn_hours']))

    st.write("**Расход топлива:**")
    st.write(f"• Закладок: {loads}")
    st.write(f"• В день: {economics['daily_fuel_kg']:.1f} кг")
    st.write(f"• В месяц: {economics['daily_fuel_kg']*22:.0f} кг")
    st.write(f"• За сезон: {economics['daily_fuel_kg']*22*7:.0f} кг")

    st.write("**Стоимость отопления:**")
    st.write(f"• В день: {economics['daily_cost']:.0f} руб.")
    st.write(f"• В месяц: {economics['monthly_cost']:.0f} руб.")
    st.write(f"• За сезон: {economics['seasonal_cost']:.0f} руб.")

if __name__ == "__main__":
    main()
