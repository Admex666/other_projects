import { QuestConfig } from '../types/quest';

/**
 * ============================================================================
 * 🎯 MARKO 22ND BIRTHDAY QUEST CONFIGURATION
 * ============================================================================
 * Ebben a fájlban találhatók az alkalmazás szövegei és a
 * [PLACEHOLDER] adatok (jelszó, helyszínek, opciók, GPS koordináták).
 */
export const defaultQuestConfig: QuestConfig = {
  meta: {
    birthdayPerson: 'Markó',
    turningAge: 22,
    year: 2026,
    title: 'Markó 22. Születésnapi Program',
    subtitle: 'Közös szülinapi este & kihívások',
    eventDate: '2026. Május / Nyár [PLACEHOLDER]',
  },

  security: {
    // 🔑 PLACEHOLDER JELSZÓ: Ezt kell beírni a Teaser képernyőn a feloldáshoz
    unlockCode: '2208',
    allowOverride: true,
  },

  stages: {
    teaser: {
      title: 'Születésnapi Este Zárolva',
      lockedMessage: 'Isten éltessen Markó! A mai program zárolva van az indulásig. A feloldó kódot a találkozáskor kapod meg.',
      hint: 'Kérd el a 4 számjegyű kódot a csapattól az ajándék átadásakor!',
    },

    intro: {
      title: 'Isten éltessen 22. szülinapodon!',
      briefing: [
        'A mai este nem a sablonos meghívásról szól: egy közös estélyi programot raktunk össze neked.',
        'Minden állomáson mi álljuk a számlát és a programot, neked csak választanod és vezetned kell a csapatot.',
        'Gurítsunk, vacsorázzunk egy jót, majd kutassuk fel a titkos kocsmát a koccintáshoz!'
      ],
      rules: [
        'A szülinapos pénztárcája ma este pihen.',
        'A kihívások becsülettel teljesítendők.',
        'A jókedv és a koccintás kötelező!'
      ],
      inventory: [
        '🎳 Bowling pálya & versenyszellem',
        '🍔 Választott szülinapi vacsora',
        '🍻 Titkos kocsma hideg-meleg kereső',
        '👥 A legjobb baráti társaság'
      ]
    },

    // 1. ÁLLOMÁS: BOWLING (Fix program)
    bowling: {
      title: '1. Állomás: Bowling',
      venueName: 'Strike Bowling Club [PLACEHOLDER]',
      venueAddress: '1117 Budapest, Október huszonharmadika u. 8-10. [PLACEHOLDER]',
      meetingTime: '18:00 [PLACEHOLDER]',
      mapsUrl: 'https://maps.google.com/?q=Strike+Bowling+Club+Budapest',
      description: 'Itt találkozunk és indul az este! Gurítsunk minél több strike-ot a 22. születésnap megünneplésére!',
      challenge: {
        goalText: 'Gyűjts össze legalább 3 Strike-ot vagy Spare-t a meccs alatt!',
        targetStrikes: 3
      },
      // 🎭 VICCES ARCFELISMERÉS (PLACEHOLDER kép és hang)
      faceScan: {
        title: 'BIOMETRIKUS AZONOSÍTÁS',
        subtitle: 'Kérlek nézz a kamerába a születésnapi jogosultság igazolásához...',
        imagePath: '/images/marko_funny.jpg', // Ide másold be a képet: public/images/marko_funny.jpg
        soundPath: '/sounds/omg-bruh-oh-hell-nah.mp3', // Ide másold be a hangot: public/sounds/omg-bruh-oh-hell-nah.mp3
        identifiedName: 'MARKÓ (22 ÉVES GYANÚSÍTOTT)',
        caption: '⚠️ FIGYELEM: Az arcfelismerő Markó későbbi állapotát ismerte fel! Azonnali bowlingozásra kötelezve.'
      }
    },

    // 2. ÁLLOMÁS: BOWLING UTÁNI TÁPLÁLKOZÁSI STRATÉGIA
    food: {
      title: 'BOWLING UTÁNI TÁPLÁLKOZÁSI STRATÉGIA',
      introText: 'Sportolás után szükséges a megfelelő (vagy kevésbé megfelelő) táplálkozás. Tiéd a választás lehetősége.',
      options: [
        {
          id: 'strategy_1',
          title: '1 — Felelős döntés',
          category: 'Könnyű & Egészséges',
          description: 'Friss salátatál, grillezett csirkemell, semmi zsíros túlzás. A tested holnap megköszöni.',
          badge: '🥗 FELELŐS',
          image: '🥗',
          venueName: 'Fresh & Fit Bistro [PLACEHOLDER]',
          venueAddress: '1117 Budapest, Október 23. u. [PLACEHOLDER]',
          mapsUrl: 'https://maps.google.com/?q=Fresh+Fit+Budapest',
          targetLocation: {
            lat: 47.4765,
            lng: 19.0520,
          }
        },
        {
          id: 'strategy_2',
          title: '2 — Normális ember',
          category: 'Tartalmas & Finom',
          description: 'Gőzölgő ázsiai ramen vagy egy jó tésztaétel. Nem éhezel, de nem is dőlsz ki tőle.',
          badge: '🍜 NORMÁLIS',
          image: '🍜',
          venueName: 'Ramen & Noodle Bar [PLACEHOLDER]',
          venueAddress: '1092 Budapest, Ráday utca [PLACEHOLDER]',
          mapsUrl: 'https://maps.google.com/?q=Ramen+Budapest',
          targetLocation: {
            lat: 47.4840,
            lng: 19.0620,
          }
        },
        {
          id: 'strategy_3',
          title: '3 — Leszarom',
          category: 'Szaftos Burger & Sültkrumpli',
          description: 'Dupla marhahúsos smash burger, olvasztott cheddar sajt és ropogós sültkrumpli.',
          badge: '🍔 LESZAROM',
          image: '🍔',
          venueName: 'Epic Smash Burger [PLACEHOLDER]',
          venueAddress: '1053 Budapest, Kálvin tér környéke [PLACEHOLDER]',
          mapsUrl: 'https://maps.google.com/?q=Burger+Kalvin+Budapest',
          targetLocation: {
            lat: 47.4920,
            lng: 19.0560,
          }
        },
        {
          id: 'strategy_4',
          title: '4 — Holnap megbánom',
          category: 'Extrém Kalóriabomba',
          description: 'Mindenből a legnagyobb adag, extra csípős fűszerezés, tripla sajt. Ma este élünk!',
          badge: '💀 MEGBÁNOM',
          image: '💀',
          venueName: 'Monster BBQ & Feast [PLACEHOLDER]',
          venueAddress: '1074 Budapest, Kazinczy u. [PLACEHOLDER]',
          mapsUrl: 'https://maps.google.com/?q=Kazinczy+Budapest',
          targetLocation: {
            lat: 47.4990,
            lng: 19.0650,
          }
        }
      ]
    },

    // 3. ÁLLOMÁS: KOCSMÁZÁS (CSAK HIDEG-MELEG)
    bar: {
      title: '3. Állomás: A Titkos Kocsma Kereső',
      riddle: 'Itt már nincs nyíl vagy térkép: csak a hideg-meleg jelzés vezet el a záró koccintás helyszínéhez!',
      clues: [
        '1. Nyom: Keresd a belváros legélettelibb macskaköves utcáit...',
        '2. Nyom: Egy hangulatos belső udvar vagy cégér jelzi a bejáratot...',
        '3. Nyom: Ha már lángol a jelzés, 30 méteren belül vagytok a csapolt söröktől!'
      ],
      targetLocation: {
        lat: 47.4984, // PLACEHOLDER LAT
        lng: 19.0583, // PLACEHOLDER LNG
      },
      venueNameRevealed: 'Központ Bar / Hops Beer Bar [PLACEHOLDER]',
      venueAddressRevealed: '1075 Budapest, Madách Imre út [PLACEHOLDER]',
      mapsUrl: 'https://maps.google.com/?q=Madach+ter+Budapest',
      thresholdsMeters: {
        burning: 30,
        hot: 100,
        warm: 250,
        cold: 500,
      }
    },

    // 4. LEZÁRÁS: GRAND FINALE
    finale: {
      title: 'Küldetés Teljesítve',
      celebrationTitle: 'Boldog 22. Születésnapot, Markó!',
      message: [
        'Sikeresen végigjártuk a tervezett állomásokat: a bowlingot, a vacsorát és a kocsmát is!',
        'Nagyon örülünk, hogy együtt ünnepelhetünk veled. Isten éltessen még nagyon sokáig!',
        'Most már nincs több küldetés: élvezd az estét és a közös koccintást! 🍻🎉'
      ],
      badges: [
        {
          title: 'Strike Master',
          icon: '🎳',
          desc: 'Sikeres dobások a bowling pályán'
        },
        {
          title: 'Stratégiai Gasztro',
          icon: '👑',
          desc: 'Tökéletesen megválasztott születésnapi vacsora'
        },
        {
          title: 'Mesterfelderítő',
          icon: '🧭',
          desc: 'Célba érés a radar és a hideg-meleg alapján'
        },
        {
          title: '22 Éves Legenda',
          icon: '⭐',
          desc: 'Hivatalosan feloldva és megünnepelve'
        }
      ]
    }
  }
};
