# 🛡️ Ügyfélközpontú Fehér Címkés (White-Label) Szabvány & Belső Benchmark Tilalom

> **Státusz:** Inviolable Governance Rule (Megkerülhetetlen Termékszabály)  
> **Dátum:** 2026-11-14  
> **Cél:** Annak garantálása, hogy a PeerPlay felületein, kódjában és leírásaiban soha semmilyen belső összehasonlítás, külső cégre való utalás (pl. Stripe, Vercel, Mercury) vagy tervezési mankó ne jelenjen meg az ügyfelek számára.

---

## 1. Alapelv: A PeerPlay önálló, prémium termék

A platformot enterprise ügyfelek (HR vezetők, vezérigazgatók, szervezetfejlesztők) és workshop résztvevők használják.
- **Tilos az ügyfélfelületeken külső brandekre vagy mintákra hivatkozni:** Egyetlen képernyőn, címkében, láblécben, meta leírásban vagy felugró ablakban sem szerepelhet, hogy a dizájn vagy komponensrendszer kiről lett mintázva vagy milyen külső szabványt követ.
- **Natív terminológia:** Minden vizuális elem, token és elrendezés a **PeerPlay Design System** szerves, natív része. Nem "Stripe stílus", hanem a PeerPlay vállalati arculata.

---

## 2. Tiltott Kifejezések Ügyfélfelületeken

Az alábbi és hasonló hivatkozások szigorúan tilosak a `src/` és `public/` felhasználói rétegekben:
- ❌ *"Stripe Enterprise Standard"*
- ❌ *"Stripe stílus / Vercel stílus / Mercury stílus"*
- ❌ *"Kiről másoltuk"* / *"Benchmark minták"*
- ❌ *"Design Explorer"* vagy fejlesztői tesztcímkék éles nézeteken

---

## 3. Megengedett Belső Használat

A `knowledge/decisions/` archívumban az ADR dokumentumokban a döntések történeti kontextusaként megmaradhat a benchmark elemzés, de:
- A felhasználói felületeken (UI),
- A generált PDF és webes riportokban,
- A kérdőívekben és kísérő felületeken
kizárólag a PeerPlay saját identitása és szakmai diagnosztikai fogalmai jelenhetnek meg.
