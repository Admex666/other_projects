# Döntési Szabályrendszer (Decision Rules & Gates)

> **Verzió:** 1.0  
> **Dátum:** 2026-11-17  

---

## 1. Döntési Állapotok

A rendszer a vizsgálat végén az alábbi 6 állapot egyikét rendeli a projekthez:

1. **STOP:** A projekt leállítása javasolt. (Végzetes hiba, nem létező igény, jogi tilalom vagy elviselhetetlen CAC).
2. **RESEARCH:** Újabb asztali vagy szekunder kutatás szükséges a kritikus ismeretlenek tisztázására.
3. **VALIDATE:** A hipotézisek logikusak, de valós viselkedési tesztek szükségesek (interjú, landing page, előregisztráció).
4. **PILOT:** A modell készen áll az első fizetős vagy ingyenes éles tesztre 1-3 cégnél.
5. **BUILD:** A pilot visszaigazolta a koncepciót, indokolt a digitális termék és a facilitátori hálózat felépítése.
6. **SCALE:** A Go-To-Market és az unit economics bizonyított, jöhet a skálázás és terjeszkedés.

---

## 2. Kritikus Döntési Kapuk (Decision Gates) a PeerPlay esetében

* **Gate 1: The Buyer Gate (Vevői Kapu)**
  * *Feltétel:* Van-e konkrét, megnevezett gazdasági vevő (pl. HR vezető, Operatív igazgató), akinek rendelkezésére áll a 400-600e Ft-os büdzsé, és aki hajlandó ezért fizetni?
  * *Ha NEM:* -> **PIVOT / STOP**.

* **Gate 2: The Moat Gate (Másolhatósági Kapu)**
  * *Feltétel:* Védhető-e a formátum? Ha egy tapasztalt tréner részt vesz a játékon, lemásolhatja-e 2 hét múlva egy Google Formmal és papírokkal?
  * *Ha IGEN (könnyen másolható):* -> A digitális szoftver / ONA motor / benchmarking adatbázis értékét kell növelni!

* **Gate 3: The Scaling Gate (Skálázási Kapu)**
  * *Feltétel:* Képes-e a modell működni az alapító személyes fizikai jelenléte nélkül (külsős trénerek hálózatával / Train-the-trainer modell)?
  * *Ha NEM:* -> Ez egy prémium tanácsadó cég (Boutique Consulting), nem skálázható venture.
