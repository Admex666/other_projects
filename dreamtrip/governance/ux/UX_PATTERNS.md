---
id: ux-patterns
aliases:
  - UX_PATTERNS
type: governance
name: UX Patterns & Interaction Standards
status: active

description: A projektben használt kanonikus interakciós minták és viselkedési szabályok.

related:
  - "[[UX_PRINCIPLES]]"
  - "[[DESIGN_SYSTEM]]"
  - "[[master-planner-wizard]]"
---

# 🔄 UX Governance: Interaction Patterns

1. **Stepper / Wizard Minta:**
   * 4-lépéses folyamatjelző a fejléc alatt (`#stepNode0` - `#stepNode4`).
   * A befejezett lépések zöld pipát és `completed` státuszt kapnak, az aktív lépés világoskék kiemelést kap.
2. **Lebegő Kosársáv (Floating Trip Bar):**
   * Az oldal alján rögzített, diszkrét sáv, amely valós időben mutatja a kosárban lévő elemeket (📍 Célállomás, ✈️ Járat, 🏨 Szállás) és a becsült végösszeget.
   * Rákattintva kinyílik a részletes összegző fiók (`TripDrawer`).
3. **Döntési Kártyák (Advisor Cards):**
   * Célállomás-, járat- és szállásajánlatok egységes kártyaelrendezésben.
   * Fejléc: Név + Relevancia pontszám (`#1 Ajánlat`, `XX%`).
   * Törzs: Fontos attribútumok + Döntési indoklás doboz (Miért ajánljuk?).
   * Lábléc: Ár (összesen + /fő bontás) + Kijelölés gomb.
4. **Egységes Dátumválasztó Szabvány (Unified Date Picker Pattern):**
   * Tilos a böngésző natív `<input type="date">` mezőinek közvetlen használata, mivel platformonként eltérő, inkonzisztens és nem támogatja a többnapos vizuális sávkijelölést.
   * Minden dátum- és időintervallum-választáshoz a központi `.custom-date-display` komponenst és a magyarosított Flatpickr modult kell használni (`window.initAdvisorDatePicker`).
