import sys
import json
import requests
from datetime import datetime, date, timedelta

# Full list of networks supported by Menetrendek.hu
# 1: Volánbusz helyközi
# 2: MÁV-START vasút
# 3: Hajó / Ferry
# 10: BKK Agglomerációs buszok (pl. 218, 60-as járatok)
# 11: Trolibusz
# 12: Villamos (1, 1A, stb.)
# 13: HÉV (H5, H6, H7, H8, H9)
# 14: Metró (M1, M2, M3, M4)
# 24: BKK HÉV állomások / megállók
# 25: Vonatpótló buszok
# 26: Kisvasút
ALL_NETWORKS = [1, 2, 3, 10, 11, 12, 13, 14, 24, 25, 26]

def query_menetrendek(from_station_text, to_station_text, search_date_str=None, hour="08", min="00"):
    """
    Directly query Menetrendek.hu's live route planning engine (JSON API)
    with ALL networks enabled (HÉV, BKK villamos/busz, MÁV vasút, Volánbusz).
    """
    if not search_date_str or search_date_str == "ma":
        search_date_str = date.today().strftime("%Y-%m-%d")

    s = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': 'https://menetrendek.hu/',
        'Origin': 'https://menetrendek.hu',
        'X-Requested-With': 'XMLHttpRequest'
    }

    # 1. Initialize session cookies
    s.get('https://menetrendek.hu/', headers=headers)

    # 2. Resolve From station with full networks
    p_from = {
        'func': 'getStationOrAddrByText',
        'params': {
            'inputText': from_station_text,
            'searchIn': ['stations'],
            'searchDate': search_date_str,
            'maxResults': 5,
            'networks': ALL_NETWORKS
        }
    }
    r1 = s.post('https://menetrendek.hu/menetrend/newinterface/index.php', json=p_from, headers=headers).json()
    if not r1.get('results'):
        print(f"❌ Nem található megálló: {from_station_text}")
        return
    
    # Prefer HÉV (net 13/24) or train (net 2) or bus station if searching a town
    res_list1 = r1['results']
    st_from = res_list1[0]
    for cand in res_list1:
        if cand.get('network_id') in (13, 24, 2) or 'HÉV' in cand.get('lsname', '') or 'vasút' in cand.get('lsname', ''):
            st_from = cand
            break

    # 3. Resolve To station with full networks
    p_to = {
        'func': 'getStationOrAddrByText',
        'params': {
            'inputText': to_station_text,
            'searchIn': ['stations'],
            'searchDate': search_date_str,
            'maxResults': 5,
            'networks': ALL_NETWORKS
        }
    }
    r2 = s.post('https://menetrendek.hu/menetrend/newinterface/index.php', json=p_to, headers=headers).json()
    if not r2.get('results'):
        print(f"❌ Nem található megálló: {to_station_text}")
        return
    
    res_list2 = r2['results']
    st_to = res_list2[0]
    for cand in res_list2:
        if cand.get('ls_id', 0) > 0:
            st_to = cand
            break

    print(f"\n=======================================================")
    print(f"🚆 MENETRENDEK.HU ÉLŐ ÚTVONALTERVEZŐ (TELJES HÁLÓZAT)")
    print(f"=======================================================")
    print(f"📍 Honnan: {st_from['lsname']} (ID: {st_from['ls_id']}, hálózat: {st_from.get('network_id')})")
    print(f"🏁 Hova:   {st_to['lsname']} (ID: {st_to['ls_id']}, hálózat: {st_to.get('network_id')})")
    print(f"📅 Dátum:  {search_date_str} | Időponttól: {hour}:{min}")
    print(f"🚋 Bekapcsolt hálózatok: HÉV, MÁV vonatok, Volánbusz, BKK villamos & busz\n")

    # 4. Query live routes
    p_route = {
        'func': 'getRoutes',
        'params': {
            'networks': ALL_NETWORKS,
            'datum': search_date_str,
            'erk_stype': 'megallo',
            'ext_settings': 'block',
            'filtering': 0,
            'helyi': 'No',
            'honnan': st_from['lsname'],
            'honnan_eovx': '',
            'honnan_eovy': '',
            'honnan_ls_id': st_from['ls_id'],
            'honnan_settlement_id': st_from['settlement_id'],
            'honnan_site_code': st_from.get('site_code', ''),
            'honnan_zoom': 0,
            'hour': f"{int(hour):02d}",
            'min': f"{int(min):02d}",
            'hova': st_to['lsname'],
            'hova_eovx': '',
            'hova_eovy': '',
            'hova_ls_id': st_to['ls_id'],
            'hova_settlement_id': st_to['settlement_id'],
            'hova_site_code': st_to.get('site_code', ''),
            'hova_zoom': 0,
            'ind_stype': 'megallo',
            'keresztul': '',
            'keresztul_eovx': '',
            'keresztul_eovy': '',
            'keresztul_ls_id': 0,
            'keresztul_settlement_id': 0,
            'keresztul_site_code': '',
            'keresztul_zoom': 0,
            'keresztul_stype': 'megallo',
            'maxatszallas': '5',
            'maxvar': '120',
            'maxwalk': '1500',
            'napszak': 3,
            'naptipus': 0,
            'odavissza': 0,
            'preferencia': 0,
            'rendezes': 1,  # 1 = Indulási idő szerint növekvő (08:01 S76-os csatlakozás előre sorolása!)
            'valasztottinterface': 'folyamatos'
        }
    }

    res = s.post('https://menetrendek.hu/menetrend/newinterface/index.php', json=p_route, headers=headers)
    data = res.json()
    talalatok = data.get('results', {}).get('talalatok', {})

    if not talalatok:
        print("⚠️ Nem érkezett találat a Menetrendek.hu-tól a megadott időpontban.")
        return

    print(f"Talált hivatalos útvonalak: {len(talalatok)} db\n")
    for i, (k, route) in enumerate(list(talalatok.items())[:5]):
        kifejtes = route.get('kifejtes_postjson', {})
        runs = kifejtes.get('runs', {})
        if not runs:
            continue

        first_leg = runs['0']
        last_leg = runs[str(len(runs)-1)]
        dep_str = f"{first_leg['6']//60:02d}:{first_leg['6']%60:02d}"
        arr_str = f"{last_leg['7']//60:02d}:{last_leg['7']%60:02d}"

        print(f"-------------------------------------------------------")
        print(f"🏆 {i+1}. OPCIÓ: {dep_str} ➔ {arr_str} (Összidő: {route.get('osszido')}, Átszállások: {route.get('atszallasok_szama')})")
        print(f"   Díj: {route.get('totalFare', 'N/A')} Ft | Táv: {route.get('ossztav', 'N/A')}")
        print(f"-------------------------------------------------------")

        for idx, (rk, r) in enumerate(runs.items()):
            l_dep = f"{r['6']//60:02d}:{r['6']%60:02d}"
            l_arr = f"{r['7']//60:02d}:{r['7']%60:02d}"
            j_szam = r.get('38') or r.get('15') or 'Járat'
            from_p = r.get('23', '')
            to_p = r.get('24', '')
            days = r.get('29', '')

            print(f"  {idx+1}. szakasz: [{j_szam}] {from_p} ({l_dep}) ➔ {to_p} ({l_arr})")
            if days:
                print(f"     Megjegyzés: {days}")
        print()

    print("=======================================================\n")

if __name__ == '__main__':
    from_arg = sys.argv[1] if len(sys.argv) > 1 else "Pomáz"
    to_arg = sys.argv[2] if len(sys.argv) > 2 else "Pilisborosjenő"
    date_arg = sys.argv[3] if len(sys.argv) > 3 else "2026-11-14"
    hour_arg = sys.argv[4] if len(sys.argv) > 4 else "08"
    min_arg = sys.argv[5] if len(sys.argv) > 5 else "00"
    query_menetrendek(from_arg, to_arg, date_arg, hour_arg, min_arg)
