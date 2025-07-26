import streamlit as st
import numpy as np
from scipy.stats import poisson

st.title("⚽ Élő Meccs Esélybecslő (Poisson + xG)")
st.markdown("Add meg a meccs aktuális adatait, és becsülünk valószínűségeket és fair oddsokat az 1/X/2 kimenetekre.")

# Bemenetek
xg_home_so_far = st.number_input("Hazai xG eddig", min_value=0.0, value=0.7, step=0.1)
xg_away_so_far = st.number_input("Vendég xG eddig", min_value=0.0, value=1.4, step=0.1)

goals_home = st.number_input("Hazai csapat aktuális góljai", min_value=0, value=1)
goals_away = st.number_input("Vendég csapat aktuális góljai", min_value=0, value=0)

minute = st.slider("Játékperc", min_value=15, max_value=90, value=30)

# Kiszámoljuk a teljes meccsre becsült xG-t lineárisan
factor = 90 / minute
projected_xg_home = xg_home_so_far * factor
projected_xg_away = xg_away_so_far * factor

# Még hátralévő xG
remaining_xg_home = max(projected_xg_home - xg_home_so_far, 0.01)
remaining_xg_away = max(projected_xg_away - xg_away_so_far, 0.01)

# Poisson: maradék meccsre szimuláció
# max_goals dinamikusan az elvárt teljes gólmennyiség alapján (pl. 99%-os valószínűség alatt maradjon)
total_expected_goals = remaining_xg_home + remaining_xg_away
max_goals = int(np.ceil(poisson.ppf(0.995, total_expected_goals))) + 1
max_goals = min(max_goals, 10)  # védelem: ne legyen túl nagy (pl. 15 percnél se szálljon el)


prob_matrix = np.zeros((max_goals+1, max_goals+1))
for i in range(max_goals + 1):
    for j in range(max_goals + 1):
        final_home_goals = i + goals_home
        final_away_goals = j + goals_away
        prob = poisson.pmf(i, remaining_xg_home) * poisson.pmf(j, remaining_xg_away)
        if final_home_goals <= max_goals and final_away_goals <= max_goals:
            prob_matrix[final_home_goals, final_away_goals] += prob

# 1 / X / 2 számítása
home_win = np.sum(np.tril(prob_matrix, -1))
draw = np.sum(np.diag(prob_matrix))
away_win = np.sum(np.triu(prob_matrix, 1))

# Fair oddsok
def prob_to_odds(p):
    return round(1 / p, 2) if p > 0 else float("inf")

odds_home = prob_to_odds(home_win)
odds_draw = prob_to_odds(draw)
odds_away = prob_to_odds(away_win)

# Eredmények megjelenítése
st.subheader("📊 Eredmények:")
st.markdown(f"- Hazai győzelem esélye: **{home_win:.1%}** → *odds*: `{odds_home}`")
st.markdown(f"- Döntetlen esélye: **{draw:.1%}** → *odds*: `{odds_draw}`")
st.markdown(f"- Vendég győzelem esélye: **{away_win:.1%}** → *odds*: `{odds_away}`")

# (Opcionálisan: teljes végeredmény-eloszlás megjelenítése)
if st.checkbox("📈 Mutasd a teljes eredmény mátrixot"):
    import pandas as pd
    goal_range = list(range(max_goals + 1))
    df_matrix = pd.DataFrame(prob_matrix, index=goal_range, columns=goal_range)
    st.dataframe(df_matrix.style.format("{:.2%}").background_gradient(cmap="Blues"), height=400)
