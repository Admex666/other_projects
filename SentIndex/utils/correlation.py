import pandas as pd

def calculate_pearson_correlation(df):
    """
    Calculates the Pearson Correlation Coefficient between 'Probability' and 'AssetPrice'.
    """
    if len(df) < 2:
        return 0.0
    
    correlation = df['Probability'].corr(df['AssetPrice'])
    if pd.isna(correlation):
        return 0.0
    return round(float(correlation), 3)

def get_correlation_interpretation(val, market_name, asset_name):
    """
    Returns a human-readable interpretation of the correlation coefficient
    tailored to the selected Polymarket event and financial asset.
    """
    abs_val = abs(val)
    
    if abs_val < 0.2:
        strength = "hanyagolható (gyenge)"
    elif abs_val < 0.5:
        strength = "mérsékelt"
    elif abs_val < 0.7:
        strength = "közepesen erős"
    else:
        strength = "nagyon erős"
        
    direction = "pozitív" if val > 0 else "negatív"
    
    explanation = ""
    is_geopolitics = "war" in market_name.lower() or "conflict" in market_name.lower() or "ceasefire" in market_name.lower()
    is_ceasefire = "ceasefire" in market_name.lower() or "peace" in market_name.lower()
    
    if "HUF" in asset_name:
        if is_geopolitics:
            if not is_ceasefire: # e.g. War probability
                if val > 0.5:
                    explanation = (
                        "**Gazdasági magyarázat:** A feszültség emelkedése (magasabb esély) növeli a globális kockázatkerülést (Risk-Off hangulat). "
                        "Ilyenkor a befektetők menekülnek az olyan fejlődő piaci devizákból, mint a forint, és biztonságos menedékbe (dollár) váltanak, "
                        "ami az USD/HUF árfolyam emelkedését (a forint gyengülését) idézi elő. Ez a tankönyvi összefüggés."
                    )
            else: # Ceasefire probability
                if val < -0.5:
                    explanation = (
                        "**Gazdasági magyarázat:** A béke/fegyverszünet esélyének növekedése javítja a globális befektetői étvágyat (Risk-On). "
                        "Ennek hatására a forint erősödik, és az USD/HUF vagy EUR/HUF árfolyam csökken. Így a negatív korreláció teljesen logikus."
                    )
        elif "BTC" in market_name or "Bitcoin" in market_name:
            explanation = (
                "**Gazdasági magyarázat:** A Bitcoin szárnyalásának esélye és a forint árfolyama közötti korreláció a globális likviditás függvénye. "
                "Ha a kripto optimizmus magas, az általában egy általános kockázatvállaló (Risk-On) hangulatot jelez, ami a forintot is erősíteni szokta (alacsonyabb USD/HUF)."
            )
            
    if not explanation:
        if val > 0.4:
            explanation = f"**Gazdasági magyarázat:** A két mutató között szoros **együttmozgás** figyelhető meg. Amikor a Polymarket esemény valószínűsége emelkedik, a(z) {asset_name} árfolyama is vele együtt növekszik."
        elif val < -0.4:
            explanation = f"**Gazdasági magyarázat:** A két mutató között **ellentétes irányú** kapcsolat van. Amikor az esemény esélye növekszik, a(z) {asset_name} árfolyama csökken (pl. kockázatkerülés vagy menedék-eszköz átcsoportosítás miatt)."
        else:
            explanation = f"**Gazdasági magyarázat:** Nincs egyértelmű lineáris kapcsolat a két mutató között. Rövid távon más piaci tényezők dominálnak."
            
    return {
        "strength": strength,
        "direction": direction,
        "explanation": explanation
    }
