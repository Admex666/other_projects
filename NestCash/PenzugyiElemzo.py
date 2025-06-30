import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class PenzugyiElemzo:
    """
    Átfogó pénzügyi elemző osztály user-szintű elemzésekhez
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Inicializálja az elemzőt a pénzügyi adatokkal
        
        Args:
            df: DataFrame a pénzügyi tranzakciókkal
        """
        self.df = df.copy()
        self.df['datum'] = pd.to_datetime(self.df['datum'])
        self.prepare_data()
    
    def prepare_data(self):
        """Előkészíti az adatokat az elemzésekhez"""
        # Bevételek és kiadások szétválasztása
        self.bevetel = self.df[self.df['bev_kiad_tipus'] == 'bevetel'].copy()
        self.kiadas = self.df[self.df['bev_kiad_tipus'] == 'szukseglet'].copy()
        self.luxus = self.df[self.df['bev_kiad_tipus'] == 'luxus'].copy()
        
        # Havi összesítések készítése
        self.havi_osszesites = self._havi_osszesites()
        
    def _havi_osszesites(self) -> pd.DataFrame:
        """Havi pénzügyi összesítés készítése"""
        monthly_data = []
        
        for user_id in self.df['user_id'].unique():
            user_df = self.df[self.df['user_id'] == user_id]
            
            for honap in user_df['honap'].unique():
                havi_df = user_df[user_df['honap'] == honap]
                
                bevetel_sum = havi_df[havi_df['bev_kiad_tipus'] == 'bevetel']['osszeg'].sum()
                szukseglet_sum = abs(havi_df[havi_df['bev_kiad_tipus'] == 'szukseglet']['osszeg'].sum())
                luxus_sum = abs(havi_df[havi_df['bev_kiad_tipus'] == 'luxus']['osszeg'].sum())
                
                # likvid az adott hónap végén
                likvid = havi_df['likvid'].iloc[-1] if len(havi_df) > 0 else 0
                assets = havi_df['assets'].iloc[-1] if len(havi_df) > 0 else 0
                
                monthly_data.append({
                    'user_id': user_id,
                    'honap': honap,
                    'bevetel': bevetel_sum,
                    'szukseglet': szukseglet_sum,
                    'luxus': luxus_sum,
                    'total_kiadas': szukseglet_sum + luxus_sum,
                    'netto_cashflow': bevetel_sum - (szukseglet_sum + luxus_sum),
                    'likvid': likvid,
                    'total_assets': assets,
                    'profil': havi_df['profil'].iloc[0] if len(havi_df) > 0 else 'ismeretlen'
                })
        
        return pd.DataFrame(monthly_data)

    # ============= CASH FLOW MANAGEMENT =============
    
    def burn_rate_kalkulation(self, user_id: int) -> Dict:
        """
        Burn rate kalkuláció - havi átlagos kiadás
        
        Args:
            user_id: Felhasználó azonosító
            
        Returns:
            Dictionary a burn rate adatokkal
        """
        user_data = self.havi_osszesites[self.havi_osszesites['user_id'] == user_id]
        
        if user_data.empty:
            return {'error': f'Nincs adat a {user_id} felhasználóhoz'}
        
        # Havi átlagos kiadások
        atlag_szukseglet = user_data['szukseglet'].mean()
        atlag_luxus = user_data['luxus'].mean()
        total_burn_rate = atlag_szukseglet + atlag_luxus
        
        # Trend elemzés
        if len(user_data) > 1:
            trend_szukseglet = np.polyfit(range(len(user_data)), user_data['szukseglet'], 1)[0]
            trend_luxus = np.polyfit(range(len(user_data)), user_data['luxus'], 1)[0]
        else:
            trend_szukseglet = trend_luxus = 0
        
        return {
            'user_id': user_id,
            'havi_atlag_szukseglet': round(atlag_szukseglet, 0),
            'havi_atlag_luxus': round(atlag_luxus, 0),
            'total_burn_rate': round(total_burn_rate, 0),
            'szukseglet_trend': 'növekvő' if trend_szukseglet > 1000 else 'csökkenő' if trend_szukseglet < -1000 else 'stabil',
            'luxus_trend': 'növekvő' if trend_luxus > 1000 else 'csökkenő' if trend_luxus < -1000 else 'stabil',
            'profil': user_data['profil'].iloc[0]
        }
    
    def runway_analysis(self, user_id: int) -> Dict:
        """
        Runway analysis - mennyire tartanak a megtakarítások
        
        Args:
            user_id: Felhasználó azonosító
            
        Returns:
            Dictionary a runway elemzéssel
        """
        burn_rate_data = self.burn_rate_kalkulation(user_id)
        if 'error' in burn_rate_data:
            return burn_rate_data
        
        user_data = self.havi_osszesites[self.havi_osszesites['user_id'] == user_id]
        current_likvid = user_data['likvid'].iloc[-1]
        current_assets = user_data['total_assets'].iloc[-1]
        
        burn_rate = burn_rate_data['total_burn_rate']
        
        # Különböző forgatókönyvek
        scenarios = {
            'csak_keszpenz': current_likvid / burn_rate if burn_rate > 0 else float('inf'),
            'osszes_asset': current_assets / burn_rate if burn_rate > 0 else float('inf'),
            'csak_szukseglet': current_likvid / burn_rate_data['havi_atlag_szukseglet'] if burn_rate_data['havi_atlag_szukseglet'] > 0 else float('inf')
        }
        
        return {
            'user_id': user_id,
            'jelenlegi_likvid': current_likvid,
            'osszes_asset': current_assets,
            'havi_burn_rate': burn_rate,
            'runway_honapok': {
                'csak_keszpenz': round(scenarios['csak_keszpenz'], 1),
                'osszes_asset': round(scenarios['osszes_asset'], 1),
                'csak_szukseglet': round(scenarios['csak_szukseglet'], 1)
            },
            'veszelyeztettseg': 'magas' if scenarios['csak_keszpenz'] < 3 else 'kozepes' if scenarios['csak_keszpenz'] < 6 else 'alacsony',
            'ajanlasok': self._runway_ajanlasok(scenarios['csak_keszpenz'])
        }
    
    def _runway_ajanlasok(self, honapok: float) -> List[str]:
        """Runway alapú ajánlások"""
        if honapok < 3:
            return [
                'SÜRGŐS: Növelje a bevételeit!',
                'Csökkentse a luxuskiadásokat azonnal',
                'Tekintse át az összes nem létfontosságú kiadást',
                'Fontolja meg a mellékjövedelem lehetőségeit'
            ]
        elif honapok < 6:
            return [
                'Építsen fel sürgősen tartalékot',
                'Csökkentse a luxuskiadásokat',
                'Optimalizálja a fix költségeket'
            ]
        else:
            return [
                'Jó pénzügyi helyzetben van',
                'Fontolja meg a befektetési lehetőségeket',
                'Tartsa fenn a jelenlegi megtakarítási szintet'
            ]
    
    def emergency_fund_adequacy(self, user_id: int) -> Dict:
        """
        Vészhelyzeti tartalék megfelelősségének elemzése
        
        Args:
            user_id: Felhasználó azonosító
            
        Returns:
            Dictionary a tartalék elemzéssel
        """
        burn_rate_data = self.burn_rate_kalkulation(user_id)
        if 'error' in burn_rate_data:
            return burn_rate_data
        
        user_data = self.havi_osszesites[self.havi_osszesites['user_id'] == user_id]
        current_likvid = user_data['likvid'].iloc[-1]
        havi_szukseglet = burn_rate_data['havi_atlag_szukseglet']
        
        # Ajánlott tartalék: 3-6 hónap szükséglet
        ajanlott_min = havi_szukseglet * 3
        ajanlott_max = havi_szukseglet * 6
        
        jelenlegi_fedezet = current_likvid / havi_szukseglet if havi_szukseglet > 0 else float('inf')
        
        return {
            'user_id': user_id,
            'jelenlegi_tartalek': current_likvid,
            'havi_szukseglet': havi_szukseglet,
            'ajanlott_minimum': ajanlott_min,
            'ajanlott_optimalis': ajanlott_max,
            'jelenlegi_fedezet_honapok': round(jelenlegi_fedezet, 1),
            'megfeleloseg': 'megfelelő' if jelenlegi_fedezet >= 3 else 'eleg' if jelenlegi_fedezet >= 1.5 else 'elegtelen',
            'hiany': max(0, ajanlott_min - current_likvid),
            'ajanlasok': self._emergency_fund_ajanlasok(jelenlegi_fedezet)
        }
    
    def _emergency_fund_ajanlasok(self, fedezet_honapok: float) -> List[str]:
        """Vészhelyzeti tartalék ajánlások"""
        if fedezet_honapok < 1.5:
            return [
                'KRITIKUS: Azonnali tartalékképzés szükséges!',
                'Havi bevétel 20-30%-át tegye félre',
                'Csökkentse minden luxuskiadást',
                'Automatikus megtakarítást állítson be'
            ]
        elif fedezet_honapok < 3:
            return [
                'Növelje a tartalékot legalább 3 hónapra',
                'Havi bevétel 15-20%-át tegye félre',
                'Optimalizálja a kiadásokat'
            ]
        elif fedezet_honapok < 6:
            return [
                'Jó úton van, törekedjen a 6 hónapos tartalékra',
                'Folytassa a rendszeres megtakarítást'
            ]
        else:
            return [
                'Kiváló tartalékkal rendelkezik!',
                'Fontolja meg a befektetési lehetőségeket',
                'Egy részét befektetheti magasabb hozamért'
            ]

    # ============= SPÓROLÁSI OPTIMALIZÁCIÓ =============
    
    def pareto_analysis(self, user_id: int) -> Dict:
        """
        Pareto elemzés (80/20 szabály) a költésekben
        
        Args:
            user_id: Felhasználó azonosító
            
        Returns:
            Dictionary a Pareto elemzéssel
        """
        user_df = self.df[(self.df['user_id'] == user_id) & 
                         (self.df['bev_kiad_tipus'].isin(['szukseglet', 'luxus']))]
        
        if user_df.empty:
            return {'error': f'Nincs kiadási adat a {user_id} felhasználóhoz'}
        
        # Kategóriánkénti összesítés
        kategoria_osszeg = user_df.groupby('kategoria')['osszeg'].sum().abs().sort_values(ascending=False)
        
        # Kumulatív százalék számítása
        total_kiadas = kategoria_osszeg.sum()
        kategoria_osszeg_pct = (kategoria_osszeg / total_kiadas * 100).round(1)
        kumulative_pct = kategoria_osszeg_pct.cumsum()
        
        # Top 20% kategóriák, amik a kiadások 80%-át teszik ki
        pareto_kategoriak = kumulative_pct[kumulative_pct <= 80].index.tolist()
        
        # Ha kevesebb mint 80%, akkor vegyük a következőt is
        if len(pareto_kategoriak) < len(kategoria_osszeg) and kumulative_pct.iloc[len(pareto_kategoriak)] < 90:
            pareto_kategoriak.append(kumulative_pct.index[len(pareto_kategoriak)])
        
        pareto_osszeg = kategoria_osszeg[pareto_kategoriak].sum()
        pareto_arany = (pareto_osszeg / total_kiadas * 100).round(1)
        
        return {
            'user_id': user_id,
            'total_kiadas': total_kiadas,
            'pareto_kategoriak': pareto_kategoriak,
            'pareto_osszeg': pareto_osszeg,
            'pareto_arany_pct': pareto_arany,
            'kategoria_reszletek': {
                kat: {
                    'osszeg': kategoria_osszeg[kat],
                    'arany_pct': kategoria_osszeg_pct[kat],
                    'kumulativ_pct': kumulative_pct[kat]
                } for kat in kategoria_osszeg.index[:10]  # Top 10
            },
            'ajanlasok': self._pareto_ajanlasok(pareto_kategoriak, kategoria_osszeg)
        }
    
    def _pareto_ajanlasok(self, pareto_kategoriak: List[str], kategoria_osszeg: pd.Series) -> List[str]:
        """Pareto elemzés alapú ajánlások"""
        ajanlasok = ['FÓKUSZ a következő kategóriákra (legnagyobb hatás):']
        
        for i, kat in enumerate(pareto_kategoriak[:3]):  # Top 3
            osszeg = kategoria_osszeg[kat]
            if kat in ['etterem', 'kave', 'csoki']:
                ajanlasok.append(f'{kat}: {osszeg:,.0f} Ft - Csökkentse a külső étkezést')
            elif kat == 'rezsi':
                ajanlasok.append(f'{kat}: {osszeg:,.0f} Ft - Energiahatékonyság, szolgáltató váltás')
            elif kat == 'kozlekedes':
                ajanlasok.append(f'{kat}: {osszeg:,.0f} Ft - Tömegközlekedés, autómegosztás')
            else:
                ajanlasok.append(f'{kat}: {osszeg:,.0f} Ft - Részletes áttekintés javasolt')
        
        return ajanlasok
    
    def low_hanging_fruit_identification(self, user_id: int) -> Dict:
        """
        Könnyen csökkenthető kiadások azonosítása
        
        Args:
            user_id: Felhasználó azonosító
            
        Returns:
            Dictionary a könnyen csökkenthető kiadásokkal
        """
        user_df = self.df[(self.df['user_id'] == user_id) & 
                         (self.df['bev_kiad_tipus'] == 'luxus')]
        
        if user_df.empty:
            return {'error': f'Nincs luxuskiadási adat a {user_id} felhasználóhoz'}
        
        # Impulzus vásárlások
        impulzus_kiadas = user_df[user_df['tipus'] == 'impulzus']
        impulzus_osszeg = abs(impulzus_kiadas['osszeg'].sum())
        
        # Apró, gyakori kiadások (kávé, csokoládé, stb.)
        apro_kategoriak = ['kave', 'csoki']
        apro_kiadas = user_df[user_df['kategoria'].isin(apro_kategoriak)]
        apro_osszeg = abs(apro_kiadas['osszeg'].sum())
        apro_darab = len(apro_kiadas)
        
        # Éttermi kiadások
        etterem_kiadas = user_df[user_df['kategoria'] == 'etterem']
        etterem_osszeg = abs(etterem_kiadas['osszeg'].sum())
        etterem_darab = len(etterem_kiadas)
        
        # Potenciális megtakarítások
        potencialis_megtakaritas = {
            'impulzus_50pct': impulzus_osszeg * 0.5,
            'apro_30pct': apro_osszeg * 0.3,
            'etterem_25pct': etterem_osszeg * 0.25
        }
        
        total_potencial = sum(potencialis_megtakaritas.values())
        
        return {
            'user_id': user_id,
            'low_hanging_fruits': {
                'impulzus_vasarlasok': {
                    'osszeg': impulzus_osszeg,
                    'darab': len(impulzus_kiadas),
                    'potencial_megtakaritas': potencialis_megtakaritas['impulzus_50pct'],
                    'javaslat': 'Várjon 24 órát impulzus vásárlások előtt'
                },
                'apro_kiadas': {
                    'osszeg': apro_osszeg,
                    'darab': apro_darab,
                    'potencial_megtakaritas': potencialis_megtakaritas['apro_30pct'],
                    'javaslat': 'Otthoni kávé/snack készítés'
                },
                'ettermi_kiadas': {
                    'osszeg': etterem_osszeg,
                    'darab': etterem_darab,
                    'potencial_megtakaritas': potencialis_megtakaritas['etterem_25pct'],
                    'javaslat': 'Otthoni főzés növelése, heti 1-2 étterem helyett'
                }
            },
            'total_potencial_megtakaritas': total_potencial,
            'havi_potencial': total_potencial,  # Assuming monthly data
            'evi_potencial': total_potencial * 12,
            'prioritas_sorrend': sorted(potencialis_megtakaritas.items(), key=lambda x: x[1], reverse=True)
        }
    
    def category_wise_savings_opportunities(self, user_id: int) -> Dict:
        """
        Kategóriánkénti spórolási lehetőségek elemzése
        
        Args:
            user_id: Felhasználó azonosító
            
        Returns:
            Dictionary a kategóriánkénti spórolási lehetőségekkel
        """
        user_df = self.df[(self.df['user_id'] == user_id) & 
                         (self.df['bev_kiad_tipus'].isin(['szukseglet', 'luxus']))]
        
        if user_df.empty:
            return {'error': f'Nincs kiadási adat a {user_id} felhasználóhoz'}
        
        # Hasonló profilú felhasználók átlagai (benchmark)
        user_profil = user_df['profil'].iloc[0]
        benchmark_df = self.df[self.df['profil'] == user_profil]
        
        kategoria_elemzes = {}
        
        for kategoria in user_df['kategoria'].unique():
            user_kat_osszeg = abs(user_df[user_df['kategoria'] == kategoria]['osszeg'].sum())
            
            # Benchmark számítás
            benchmark_kat = benchmark_df[benchmark_df['kategoria'] == kategoria]
            if not benchmark_kat.empty:
                benchmark_atlag = abs(benchmark_kat.groupby('user_id')['osszeg'].sum().mean())
                kulonbseg = user_kat_osszeg - benchmark_atlag
                kulonbseg_pct = (kulonbseg / benchmark_atlag * 100) if benchmark_atlag > 0 else 0
            else:
                benchmark_atlag = 0
                kulonbseg = 0
                kulonbseg_pct = 0
            
            # Spórolási potenciál
            if kulonbseg > 0:  # Ha átlag felett költenek
                potencial_megtakaritas = kulonbseg * 0.3  # 30%-os csökkentés célja
                nehezsseg = self._sporolas_nehezsseg(kategoria)
            else:
                potencial_megtakaritas = 0
                nehezsseg = 'nem_szukseges'
            
            kategoria_elemzes[kategoria] = {
                'user_osszeg': user_kat_osszeg,
                'benchmark_atlag': benchmark_atlag,
                'kulonbseg': kulonbseg,
                'kulonbseg_pct': round(kulonbseg_pct, 1),
                'potencial_megtakaritas': potencial_megtakaritas,
                'nehezsseg': nehezsseg,
                'prioritas': 'magas' if kulonbseg_pct > 50 and nehezsseg == 'konnyu' else 
                           'kozepes' if kulonbseg_pct > 20 else 'alacsony',
                'ajanlasok': self._kategoria_ajanlasok(kategoria, kulonbseg_pct)
            }
        
        # Prioritás szerint rendezés
        sorted_kategoriak = sorted(
            kategoria_elemzes.items(),
            key=lambda x: x[1]['potencial_megtakaritas'],
            reverse=True
        )
        
        return {
            'user_id': user_id,
            'user_profil': user_profil,
            'kategoria_elemzes': kategoria_elemzes,
            'top_sporolasi_lehetosegek': dict(sorted_kategoriak[:5]),
            'total_potencial': sum(k['potencial_megtakaritas'] for k in kategoria_elemzes.values()),
            'osszefoglalo_ajanlasok': self._osszefoglalo_sporolas_ajanlasok(sorted_kategoriak[:3])
        }
    
    def _sporolas_nehezsseg(self, kategoria: str) -> str:
        """Spórolás nehézségének meghatározása kategóriánként"""
        konnyu = ['kave', 'csoki', 'etterem']
        kozepes = ['kozlekedes', 'elelmiszer']
        nehez = ['rezsi', 'lakber', 'fizetes']
        
        if kategoria in konnyu:
            return 'konnyu'
        elif kategoria in kozepes:
            return 'kozepes'
        else:
            return 'nehez'
    
    def _kategoria_ajanlasok(self, kategoria: str, kulonbseg_pct: float) -> List[str]:
        """Kategória-specifikus spórolási ajánlások"""
        if kulonbseg_pct < 10:
            return ['Megfelelő szinten költekezik ebben a kategóriában']
        
        ajanlasok = {
            'etterem': [
                'Csökkentse a külső étkezések számát',
                'Válasszon olcsóbb éttermeket',
                'Használjon éttermi kuponokat/akciókat'
            ],
            'kave': [
                'Készítsen otthon kávét',
                'Vásároljon kávégépet hosszú távú megtakarításért',
                'Csökkentse a napi kávé mennyiségét'
            ],
            'kozlekedes': [
                'Használjon tömegközlekedést',
                'Fontolja meg a kerékpározást',
                'Carpooling/autómegosztás'
            ],
            'rezsi': [
                'Energiahatékony készülékek',
                'Szolgáltató összehasonlítás',
                'Hőmérséklet optimalizáció'
            ]
        }
        
        return ajanlasok.get(kategoria, ['Tekintse át ezt a kategóriát részletesen'])

    def _osszefoglalo_sporolas_ajanlasok(self, top_kategoriak: List[Tuple]) -> List[str]:
        """Összefoglaló spórolási ajánlások"""
        ajanlasok = ['TOP SPÓROLÁSI PRIORITÁSOK:']
        
        for i, (kategoria, adatok) in enumerate(top_kategoriak):
            if adatok['potencial_megtakaritas'] > 1000:
                ajanlasok.append(
                    f"{i+1}. {kategoria}: {adatok['potencial_megtakaritas']:,.0f} Ft potenciál "
                    f"({adatok['kulonbseg_pct']:+.1f}% az átlagtól)"
                )
        
        return ajanlasok

    # ============= BEFEKTETÉSI ELEMZÉS =============
    
    def portfolio_allocation_suggestions(self, user_id: int) -> Dict:
        """
        Portfólió allokációs javaslatok
        
        Args:
            user_id: Felhasználó azonosító
            
        Returns:
            Dictionary a portfólió javaslatokkal
        """
        user_data = self.havi_osszesites[self.havi_osszesites['user_id'] == user_id]
        
        if user_data.empty:
            return {'error': f'Nincs adat a {user_id} felhasználóhoz'}
        
        current_likvid = user_data['likvid'].iloc[-1]
        current_assets = user_data['total_assets'].iloc[-1]
        
        # Jelenlegi allokáció a CSV-ből
        latest_data = self.df[self.df['user_id'] == user_id].iloc[-1]
        befektetes = latest_data['befektetes']
        megtakaritas = latest_data['megtakaritas']
        keszpenz = current_likvid
        
        total_assets = befektetes + megtakaritas + keszpenz
        
        jelenlegi_allokaciok = {
            'keszpenz': keszpenz / total_assets * 100 if total_assets > 0 else 0,
            'befektetes': befektetes / total_assets * 100 if total_assets > 0 else 0,
            'megtakaritas': megtakaritas / total_assets * 100 if total_assets > 0 else 0
        }
        
        # Kockázattűrés felmérés
        risk_tolerance = self._assess_risk_tolerance(user_id)
        
        # Életkor alapú becslés (profil alapján)
        age_estimate = self._estimate_age_from_profile(user_data['profil'].iloc[0])
        
        # Javasolt allokáció
        javasolt_allokaciok = self._calculate_target_allocation(risk_tolerance, age_estimate)
        
        # Átbalansírozási javaslatok
        rebalancing_actions = self._calculate_rebalancing_actions(
            current_assets, jelenlegi_allokaciok, javasolt_allokaciok
        )
        
        return {
            'user_id': user_id,
            'total_assets': total_assets,
            'jelenlegi_allokaciok': {k: round(v, 1) for k, v in jelenlegi_allokaciok.items()},
            'javasolt_allokaciok': {k: round(v, 1) for k, v in javasolt_allokaciok.items()},
            'risk_tolerance': risk_tolerance,
            'becsult_eletkor': age_estimate,
            'rebalancing_actions': rebalancing_actions,
            'specifikus_ajanlasok': self._portfolio_ajanlasok(risk_tolerance, age_estimate),
            'vart_hozam': self._calculate_expected_return(javasolt_allokaciok)
        }
    
    def _assess_risk_tolerance(self, user_id: int) -> str:
        """Kockázattűrés felmérés költési minták alapján"""
        user_df = self.df[self.df['user_id'] == user_id]
        
        # Luxuskiadások aránya
        total_kiadas = abs(user_df[user_df['bev_kiad_tipus'].isin(['szukseglet', 'luxus'])]['osszeg'].sum())
        luxus_kiadas = abs(user_df[user_df['bev_kiad_tipus'] == 'luxus']['osszeg'].sum())
        luxus_arany = luxus_kiadas / total_kiadas if total_kiadas > 0 else 0
        
        # Impulzus vásárlások
        impulzus_arany = len(user_df[user_df['tipus'] == 'impulzus']) / len(user_df) if len(user_df) > 0 else 0
        
        # Jövedelmi profil
        profil = user_df['profil'].iloc[0] if len(user_df) > 0 else 'kozeposztaly'
        
        # Megtakarítási ráta
        user_monthly = self.havi_osszesites[self.havi_osszesites['user_id'] == user_id]
        if not user_monthly.empty:
            avg_savings_rate = user_monthly['netto_cashflow'].mean() / user_monthly['bevetel'].mean()
        else:
            avg_savings_rate = 0
        
        # Kockázattűrés pontszám
        risk_score = 0
        
        # Profil alapján
        if profil == 'magas_jov':
            risk_score += 3
        elif profil == 'kozeposztaly':
            risk_score += 2
        else:  # alacsony_jov, arerzekeny
            risk_score += 1
        
        # Luxuskiadások alapján (magasabb = magasabb kockázatvállalás)
        if luxus_arany > 0.3:
            risk_score += 2
        elif luxus_arany > 0.15:
            risk_score += 1
        
        # Impulzivitás (alacsonyabb = magasabb kockázatvállalás a befektetésben)
        if impulzus_arany < 0.2:
            risk_score += 2
        elif impulzus_arany < 0.4:
            risk_score += 1
        
        # Megtakarítási ráta
        if avg_savings_rate > 0.2:
            risk_score += 2
        elif avg_savings_rate > 0.1:
            risk_score += 1
        
        # Kategorizálás
        if risk_score >= 7:
            return 'agressziv'
        elif risk_score >= 5:
            return 'kozepes'
        else:
            return 'konzervativ'
    
    def _estimate_age_from_profile(self, profil: str) -> int:
        """Életkor becslés profil alapján"""
        age_mapping = {
            'alacsony_jov': 28,  # Fiatal, karrierkezdo
            'kozeposztaly': 35,  # Középkorú
            'magas_jov': 42,     # Tapasztalt, magasabb pozíció
            'arerzekeny': 50     # Óvatosabb, esetleg idősebb
        }
        return age_mapping.get(profil, 35)
    
    def _calculate_target_allocation(self, risk_tolerance: str, age: int) -> Dict[str, float]:
        """Célallokáció számítása kockázattűrés és életkor alapján"""
        # Alap szabály: 100 - életkor = részvény %
        base_equity = max(20, min(80, 100 - age))
        
        # Kockázattűrés módosítás
        if risk_tolerance == 'agressziv':
            equity_pct = min(90, base_equity + 20)
        elif risk_tolerance == 'konzervativ':
            equity_pct = max(10, base_equity - 20)
        else:  # kozepes
            equity_pct = base_equity
        
        # Allokáció
        bond_other_pct = min(30, (100 - equity_pct) * 0.6)
        cash_pct = 100 - equity_pct - bond_other_pct
        
        return {
            'befektetes': equity_pct,
            'megtakaritas': bond_other_pct,
            'keszpenz': cash_pct
        }
    
    def _calculate_rebalancing_actions(self, total_assets: float, current: Dict, target: Dict) -> List[str]:
        """Átbalansírozási műveletek számítása"""
        actions = []
        threshold = 5  # 5%-os eltérés küszöb
        
        for asset_type in current.keys():
            diff = target[asset_type] - current[asset_type]
            if abs(diff) > threshold:
                amount = total_assets * (diff / 100)
                action = 'vásároljon' if diff > 0 else 'adjon el'
                actions.append(
                    f"{asset_type}: {action} ~{abs(amount):,.0f} Ft-ot "
                    f"({diff:+.1f}%-pont eltérés)"
                )
        
        if not actions:
            actions.append("A portfólió megfelelően kiegyensúlyozott.")
        
        return actions
    
    def _portfolio_ajanlasok(self, risk_tolerance: str, age: int) -> List[str]:
        """Portfólió-specifikus ajánlások"""
        ajanlasok = []
        
        if risk_tolerance == 'agressziv':
            ajanlasok.extend([
                "Növelje a részvény allokációt",
                "Fontolja meg a növekedési részvényeket",
                "ETF-ek diverzifikációhoz",
                "Kis részben kockázatos befektetések (crypto, startup)"
            ])
        elif risk_tolerance == 'konzervativ':
            ajanlasok.extend([
                "Állampapírok biztonságos alapként",
                "Vállalati kötvények mérsékelten magasabb hozamért",
                "Ingatlan befektetési alapok (REIT)",
                "Magas megtakarítási kamatok keresése"
            ])
        else:  # kozepes
            ajanlasok.extend([
                "Kiegyensúlyozott részvény-kötvény portfólió",
                "Széles körben diverzifikált ETF-ek",
                "Fokozatos kockázatnövelés idővel",
                "Rendszeres újraegyensúlyozás"
            ])
        
        # Életkor-specifikus ajánlások
        if age < 35:
            ajanlasok.append("Fiatal korában vállalhat magasabb kockázatot")
        elif age > 50:
            ajanlasok.append("Fokozatosan csökkentse a kockázatos befektetéseket")
        
        return ajanlasok
    
    def _calculate_expected_return(self, allocation: Dict) -> Dict:
        """Várható hozam számítása allokáció alapján"""
        # Feltételezett éves hozamok (%)
        expected_returns = {
            'befektetes': 8.0,      # Hosszú távú részvénypiaci átlag
            'megtakaritas': 4.0, # Kötvények/alternatív befektetések
            'keszpenz': 1.0         # Betéti kamatok
        }
        
        # Súlyozott átlag
        weighted_return = sum(
            allocation[asset] * expected_returns[asset] / 100
            for asset in allocation.keys()
        )
        
        return {
            'vart_eves_hozam_pct': round(weighted_return, 1),
            'konzervatir_forgatokonyv': round(weighted_return * 0.7, 1),
            'optimista_forgatokonyv': round(weighted_return * 1.3, 1),
            'kockazat_szint': 'alacsony' if weighted_return < 4 else 'kozepes' if weighted_return < 7 else 'magas'
        }
    
    def risk_tolerance_assessment_detailed(self, user_id: int) -> Dict:
        """
        Részletes kockázattűrés felmérés költési minták alapján
        
        Args:
            user_id: Felhasználó azonosító
            
        Returns:
            Dictionary a részletes kockázattűrés elemzéssel
        """
        user_df = self.df[self.df['user_id'] == user_id]
        
        if user_df.empty:
            return {'error': f'Nincs adat a {user_id} felhasználóhoz'}
        
        # Pénzügyi stabilitás mutatók
        user_monthly = self.havi_osszesites[self.havi_osszesites['user_id'] == user_id]
        
        # 1. Jövedelem stabilitás
        if len(user_monthly) > 1:
            income_volatility = user_monthly['bevetel'].std() / user_monthly['bevetel'].mean()
        else:
            income_volatility = 0
        
        # 2. Kiadási fegyelem
        total_expenses = abs(user_df[user_df['bev_kiad_tipus'].isin(['szukseglet', 'luxus'])]['osszeg'].sum())
        luxury_ratio = abs(user_df[user_df['bev_kiad_tipus'] == 'luxus']['osszeg'].sum()) / total_expenses if total_expenses > 0 else 0
        
        # 3. Impulzivitás mértéke
        impulse_ratio = len(user_df[user_df['tipus'] == 'impulzus']) / len(user_df) if len(user_df) > 0 else 0
        
        # 4. Megtakarítási képesség
        avg_savings_rate = user_monthly['netto_cashflow'].mean() / user_monthly['bevetel'].mean() if not user_monthly.empty and user_monthly['bevetel'].mean() > 0 else 0
        
        # 5. Vészhelyzeti tartalék
        emergency_fund_data = self.emergency_fund_adequacy(user_id)
        emergency_months = emergency_fund_data.get('jelenlegi_fedezet_honapok', 0) if 'error' not in emergency_fund_data else 0
        
        # Pontszám számítás (0-100)
        risk_score = 0
        
        # Jövedelem stabilitás (0-20 pont)
        if income_volatility < 0.1:
            risk_score += 20
        elif income_volatility < 0.3:
            risk_score += 15
        elif income_volatility < 0.5:
            risk_score += 10
        else:
            risk_score += 5
        
        # Kiadási fegyelem (0-20 pont)
        if luxury_ratio < 0.15:
            risk_score += 20
        elif luxury_ratio < 0.25:
            risk_score += 15
        elif luxury_ratio < 0.35:
            risk_score += 10
        else:
            risk_score += 5
        
        # Impulzivitás (fordított, 0-20 pont)
        if impulse_ratio < 0.2:
            risk_score += 20
        elif impulse_ratio < 0.3:
            risk_score += 15
        elif impulse_ratio < 0.4:
            risk_score += 10
        else:
            risk_score += 5
        
        # Megtakarítási ráta (0-20 pont)
        if avg_savings_rate > 0.25:
            risk_score += 20
        elif avg_savings_rate > 0.15:
            risk_score += 15
        elif avg_savings_rate > 0.05:
            risk_score += 10
        else:
            risk_score += 5
        
        # Vészhelyzeti tartalék (0-20 pont)
        if emergency_months >= 6:
            risk_score += 20
        elif emergency_months >= 3:
            risk_score += 15
        elif emergency_months >= 1:
            risk_score += 10
        else:
            risk_score += 5
        
        # Kockázattűrés kategória
        if risk_score >= 80:
            risk_category = 'agressziv'
        elif risk_score >= 60:
            risk_category = 'kozepes-agressziv'
        elif risk_score >= 40:
            risk_category = 'kozepes'
        elif risk_score >= 20:
            risk_category = 'kozepes-konzervativ'
        else:
            risk_category = 'konzervativ'
        
        return {
            'user_id': user_id,
            'risk_score': risk_score,
            'risk_category': risk_category,
            'reszletes_ertekeles': {
                'jovedelem_stabilitas': {
                    'volatilitas': round(income_volatility, 3),
                    'ertekeles': 'stabil' if income_volatility < 0.2 else 'kozepes' if income_volatility < 0.4 else 'ingadozo'
                },
                'kiadasi_fegyelem': {
                    'luxus_arany': round(luxury_ratio * 100, 1),
                    'ertekeles': 'kiváló' if luxury_ratio < 0.15 else 'jó' if luxury_ratio < 0.3 else 'fejlesztendő'
                },
                'impulzivitas': {
                    'impulzus_arany': round(impulse_ratio * 100, 1),
                    'ertekeles': 'alacsony' if impulse_ratio < 0.2 else 'kozepes' if impulse_ratio < 0.4 else 'magas'
                },
                'megtakaritasi_kepesseg': {
                    'megtakaritasi_rata': round(avg_savings_rate * 100, 1),
                    'ertekeles': 'kiváló' if avg_savings_rate > 0.2 else 'jó' if avg_savings_rate > 0.1 else 'fejlesztendő'
                },
                'veszhelyzeti_tartalek': {
                    'fedezet_honapok': round(emergency_months, 1),
                    'ertekeles': 'megfelelő' if emergency_months >= 3 else 'elegtelen'
                }
            },
            'befektetesi_ajanlasok': self._risk_based_investment_recommendations(risk_category, risk_score),
            'fejlesztesi_javaslatok': self._risk_improvement_suggestions(risk_score, {
                'income_volatility': income_volatility,
                'luxury_ratio': luxury_ratio,
                'impulse_ratio': impulse_ratio,
                'savings_rate': avg_savings_rate,
                'emergency_months': emergency_months
            })
        }
    
    def _risk_based_investment_recommendations(self, risk_category: str, risk_score: int) -> List[str]:
        """Kockázattűrés alapú befektetési ajánlások"""
        recommendations = []
        
        if risk_category == 'agressziv':
            recommendations.extend([
                "70-90% részvény allokáció ajánlott",
                "Növekedési részvények, technológiai ETF-ek",
                "Nemzetközi diverzifikáció",
                "Kis részben alternatív befektetések (REIT, commodity)"
            ])
        elif risk_category == 'kozepes-agressziv':
            recommendations.extend([
                "60-70% részvény allokáció",
                "Kiegyensúlyozott növekedési és értékpapírok",
                "Közepes kockázatú kötvények",
                "Rendszeres újraegyensúlyozás"
            ])
        elif risk_category == 'kozepes':
            recommendations.extend([
                "40-60% részvény allokáció",
                "Diverzifikált ETF portfólió",
                "Kormány- és vállalati kötvények keveréke",
                "Fokozatos kockázatépítés"
            ])
        elif risk_category == 'kozepes-konzervativ':
            recommendations.extend([
                "20-40% részvény allokáció",
                "Osztalékfizető részvények",
                "Magas minőségű kötvények",
                "Stabil értékpapírok előnyben"
            ])
        else:  # konzervativ
            recommendations.extend([
                "10-30% részvény allokáció maximum",
                "Állampapírok és bankbetétek hangsúlyosan",
                "Rövid távú, likvid befektetések",
                "Tőkevédelem prioritás"
            ])
        
        return recommendations
    
    def _risk_improvement_suggestions(self, risk_score: int, metrics: Dict) -> List[str]:
        """Kockázattűrés javítási javaslatok"""
        suggestions = []
        
        if metrics['income_volatility'] > 0.3:
            suggestions.append("Stabilizálja jövedelmét - esetleg több jövedelemforrás")
        
        if metrics['luxury_ratio'] > 0.3:
            suggestions.append("Csökkentse a luxuskiadásokat a magasabb megtakarításért")
        
        if metrics['impulse_ratio'] > 0.3:
            suggestions.append("Dolgozzon az impulzusvásárlások csökkentésén")
        
        if metrics['savings_rate'] < 0.1:
            suggestions.append("Növelje a megtakarítási rátát legalább 10%-ra")
        
        if metrics['emergency_months'] < 3:
            suggestions.append("Építsen fel 3-6 hónapos vészhelyzeti tartalékot")
        
        if risk_score < 60:
            suggestions.append("A pénzügyi stabilitás növelésével magasabb hozamú befektetések válnak elérhetővé")
        
        return suggestions if suggestions else ["Kiváló pénzügyi fegyelemmel rendelkezik!"]

    # ============= ÁLTALÁNOS JELENTÉS ÉS VIZUALIZÁCIÓ =============
    
    def generate_comprehensive_report(self, user_id: int) -> Dict:
        """
        Átfogó pénzügyi jelentés generálása
        
        Args:
            user_id: Felhasználó azonosító
            
        Returns:
            Dictionary az átfogó jelentéssel
        """
        report = {
            'user_id': user_id,
            'riport_datum': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'executive_summary': {},
            'cash_flow_elemzes': {},
            'sporolas_optimalizacio': {},
            'befektetesi_elemzes': {},
            'prioritas_ajanlasok': [],
            'kockazati_figyelmeztetesek': []
        }
        
        try:
            # Cash Flow elemzések
            burn_rate = self.burn_rate_kalkulation(user_id)
            runway = self.runway_analysis(user_id)
            emergency_fund = self.emergency_fund_adequacy(user_id)
            
            report['cash_flow_elemzes'] = {
                'burn_rate': burn_rate,
                'runway': runway,
                'emergency_fund': emergency_fund
            }
            
            # Spórolási elemzések
            pareto = self.pareto_analysis(user_id)
            low_hanging = self.low_hanging_fruit_identification(user_id)
            savings_opportunities = self.category_wise_savings_opportunities(user_id)
            
            report['sporolas_optimalizacio'] = {
                'pareto_analysis': pareto,
                'low_hanging_fruits': low_hanging,
                'savings_opportunities': savings_opportunities
            }
            
            # Befektetési elemzések
            portfolio = self.portfolio_allocation_suggestions(user_id)
            risk_assessment = self.risk_tolerance_assessment_detailed(user_id)
            
            report['befektetesi_elemzes'] = {
                'portfolio_suggestions': portfolio,
                'risk_assessment': risk_assessment
            }
            
            # Executive Summary
            report['executive_summary'] = self._create_executive_summary(report)
            
            # Prioritás ajánlások
            report['prioritas_ajanlasok'] = self._create_priority_recommendations(report)
            
            # Kockázati figyelmeztetések
            #report['kockazati_figyelmeztetesek'] = self._create_risk_warnings(report)
            
        except Exception as e:
            report['error'] = f"Hiba a jelentés generálása során: {str(e)}"
        
        return report
    
    def _create_executive_summary(self, report: Dict) -> Dict:
        """Executive summary létrehozása"""
        summary = {}
        
        try:
            cf = report['cash_flow_elemzes']
            sp = report['sporolas_optimalizacio']
            bf = report['befektetesi_elemzes']
            
            # Pénzügyi egészség pontszám (0-100)
            health_score = 0
            
            # Runway alapján
            runway_months = cf['runway']['runway_honapok']['csak_keszpenz']
            if runway_months >= 6:
                health_score += 25
            elif runway_months >= 3:
                health_score += 15
            elif runway_months >= 1:
                health_score += 5
            
            # Emergency fund alapján
            if cf['emergency_fund']['megfeleloseg'] == 'megfelelő':
                health_score += 25
            elif cf['emergency_fund']['megfeleloseg'] == 'eleg':
                health_score += 15
            
            # Spórolási potenciál alapján
            if 'error' not in sp['low_hanging_fruits']:
                savings_potential = sp['low_hanging_fruits']['total_potencial_megtakaritas']
                burn_rate = cf['burn_rate']['total_burn_rate']
                if savings_potential / burn_rate < 0.1:
                    health_score += 25  # Kevés pazarlás
                elif savings_potential / burn_rate < 0.2:
                    health_score += 15
            
            # Kockázattűrés alapján
            if 'error' not in bf['risk_assessment']:
                risk_score = bf['risk_assessment']['risk_score']
                if risk_score >= 60:
                    health_score += 25
                elif risk_score >= 40:
                    health_score += 15
            
            summary = {
                'penzugyi_egeszseg_pontszam': min(100, health_score),
                'altalanos_ertekeles': 'kiváló' if health_score >= 80 else 'jó' if health_score >= 60 else 'kozepes' if health_score >= 40 else 'fejlesztendő',
                'fo_erosegek': self._identify_strengths(report),
                'fo_kihivasok': self._identify_challenges(report),
                'legfontosabb_ajanlasok': self._top_recommendations(report)
            }
            
        except Exception as e:
            summary['error'] = f"Executive summary hiba: {str(e)}"
        
        return summary
    
    def _create_priority_recommendations(self, report: Dict) -> List[Dict]:
        """Prioritásos ajánlások létrehozása"""
        recommendations = []
        
        try:
            # Kritikus problémák (Prioritás 1)
            cf = report['cash_flow_elemzes']
            if 'error' not in cf['runway']:
                runway_months = cf['runway']['runway_honapok']['csak_keszpenz']
                if runway_months < 3:
                    recommendations.append({
                        'prioritas': 1,
                        'kategoria': 'Kritikus',
                        'cim': 'Sürgős pénzügyi stabilizáció szükséges',
                        'leiras': f'Csak {runway_months:.1f} hónapra elegendő tartalék',
                        'konkret_lepesek': cf['runway']['ajanlasok']
                    })
            
            # Spórolási lehetőségek (Prioritás 2)
            sp = report['sporolas_optimalizacio']
            if 'error' not in sp['low_hanging_fruits']:
                potential = sp['low_hanging_fruits']['total_potencial_megtakaritas']
                if potential > 10000:  # Ha több mint 10k Ft spórolási potenciál
                    recommendations.append({
                        'prioritas': 2,
                        'kategoria': 'Spórolás',
                        'cim': f'{potential:,.0f} Ft könnyen elérhető megtakarítás',
                        'leiras': 'Gyors nyerések a költségcsökkentésben',
                        'konkret_lepesek': [
                            f"Impulzus vásárlások: {sp['low_hanging_fruits']['low_hanging_fruits']['impulzus_vasarlasok']['potencial_megtakaritas']:,.0f} Ft",
                            f"Apró kiadások: {sp['low_hanging_fruits']['low_hanging_fruits']['apro_kiadas']['potencial_megtakaritas']:,.0f} Ft",
                            f"Éttermi kiadások: {sp['low_hanging_fruits']['low_hanging_fruits']['ettermi_kiadas']['potencial_megtakaritas']:,.0f} Ft"
                        ]
                    })
            
            # Befektetési optimalizáció (Prioritás 3)
            bf = report['befektetesi_elemzes']
            if 'error' not in bf['portfolio_suggestions']:
                rebalancing = bf['portfolio_suggestions']['rebalancing_actions']
                if len(rebalancing) > 1 or (len(rebalancing) == 1 and "megfelelően kiegyensúlyozott" not in rebalancing[0]):
                    recommendations.append({
                        'prioritas': 3,
                        'kategoria': 'Befektetés',
                        'cim': 'Portfólió optimalizáció javasolt',
                        'leiras': 'A befektetési allokáció finomhangolása',
                        'konkret_lepesek': rebalancing
                    })
            
        except Exception as e:
            recommendations.append({
                'prioritas': 0,
                'kategoria': 'Hiba',
                'cim': 'Ajánlások generálási hiba',
                'leiras': str(e),
                'konkret_lepesek': []
            })
        
        return sorted(recommendations, key=lambda x: x['prioritas'])
    
    def _identify_strengths(self, report: Dict) -> List[str]:
        """Erősségek azonosítása"""
        strengths = []
        
        try:
            cf = report['cash_flow_elemzes']
            
            # Runway ellenőrzés
            if 'error' not in cf['runway']:
                runway_months = cf['runway']['runway_honapok']['csak_keszpenz']
                if runway_months >= 3:
                    strengths.append(f"Kiváló tartalékkal rendelkezik ({runway_months:.1f} hónap)")
            
            # Emergency fund
            if 'error' not in cf['emergency_fund']:
                if cf['emergency_fund']['megfeleloseg'] == 'megfelelő':
                    strengths.append("Megfelelő vészhelyzeti tartalék")
            
            # Kockázattűrés
            bf = report['befektetesi_elemzes']
            if 'error' not in bf['risk_assessment']:
                if bf['risk_assessment']['risk_score'] >= 70:
                    strengths.append("Kiváló pénzügyi fegyelem és stabilitás")
        
        except:
            pass
        
        return strengths if strengths else ["Fejlődés lehetősége"]
    
    def _identify_challenges(self, report: Dict) -> List[str]:
        """Kihívások azonosítása"""
        challenges = []
        
        try:
            cf = report['cash_flow_elemzes']
            
            # Runway problémák
            if 'error' not in cf['runway']:
                runway_months = cf['runway']['runway_honapok']['csak_keszpenz']
                if runway_months < 3:
                    challenges.append(f"Alacsony tartalék ({runway_months:.1f} hónap)")
            
            # Spórolási lehetőségek
            sp = report['sporolas_optimalizacio']
            if 'error' not in sp['low_hanging_fruits']:
                potential = sp['low_hanging_fruits']['total_potencial_megtakaritas']
                if potential > 20000:
                    challenges.append(f"Jelentős spórolási potenciál kihasználatlan ({potential:,.0f} Ft)")
        
        except:
            pass
        
        return challenges if challenges else ["Nincsenek jelentős kihívások azonosítva"]
    
    def _top_recommendations(self, report: Dict) -> List[str]:
        """Top ajánlások"""
        recommendations = []
        
        try:
            # 1. Vészhelyzeti tartalék ellenőrzése
            cf = report['cash_flow_elemzes']
            if 'error' not in cf['emergency_fund']:
                if cf['emergency_fund']['megfeleloseg'] != 'megfelelő':
                    recommendations.append("Építsen fel 3-6 hónapos vészhelyzeti tartalékot")
            
            # 2. Runway (pénzügyi tartózkodási idő) ellenőrzése
            if 'error' not in cf['runway']:
                runway_months = cf['runway']['runway_honapok']['csak_keszpenz']
                if runway_months < 3:
                    recommendations.append(f"Sürgősen növelje a likvid tartalékot! (Jelenleg csak {runway_months:.1f} hónapra elegendő)")
            
            # 3. Spórolási lehetőségek
            sp = report['sporolas_optimalizacio']
            if 'error' not in sp['low_hanging_fruits']:
                potential = sp['low_hanging_fruits']['total_potencial_megtakaritas']
                if potential > 10000:
                    recommendations.append(f"Könnyen megvalósítható megtakarítás: {potential:,.0f} Ft/hó")
            
            # 4. Befektetési optimalizáció
            bf = report['befektetesi_elemzes']
            if 'error' not in bf['portfolio_suggestions']:
                rebalancing = bf['portfolio_suggestions']['rebalancing_actions']
                if any("vásároljon" in action or "adjon el" in action for action in rebalancing):
                    recommendations.append("Portfólió átstrukturálás szükséges a célallokáció eléréséhez")
            
            # 5. Kockázattűrés javítása
            if 'error' not in bf['risk_assessment']:
                if bf['risk_assessment']['risk_score'] < 40:
                    recommendations.append("Alacsony kockázattűrés: dolgozzon a pénzügyi stabilitás javításán")
            
            # Ha nincs más ajánlás, pozitív visszajelzés
            if not recommendations:
                recommendations.append("Kiváló pénzügyi helyzet! Tartsa fenn a jelenlegi stratégiát")
        
        except Exception as e:
            recommendations.append(f"Hiba az ajánlások generálásában: {str(e)}")
        
        return recommendations