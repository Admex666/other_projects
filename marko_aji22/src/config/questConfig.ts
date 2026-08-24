import { QuestConfig } from '../types/quest';

/**
 * ============================================================================
 * 🎯 MARKO 22ND BIRTHDAY QUEST CONFIGURATION
 * ============================================================================
 * Ebben a fájlban találhatók az alkalmazás szövegei és a
 * [PLACEHOLDER] / [DUMMY] adatok (jelszó, helyszínek, opciók, GPS koordináták).
 */
export const defaultQuestConfig: QuestConfig = {
  meta: {
    birthdayPerson: 'Markó',
    turningAge: 22,
    year: 2026,
    title: 'Markó 22. Születésnapi Program',
    subtitle: 'Közös szülinapi este & kihívások',
    eventDate: '2026. augusztus 19.',
  },

  security: {
    // 🔑 PLACEHOLDER JELSZÓ: Ezt kell beírni a Teaser képernyőn a feloldáshoz
    unlockCode: '1899',
    allowOverride: true,
  },

  stages: {
    teaser: {
      title: 'Születésnapi Este Zárolva',
      lockedMessage: 'Isten éltessen Markó! A mai program zárolva van. A feloldó kódot a találkozáskor kapod meg Ádámtól.',
      hint: 'Kérd el a 4 számjegyű kódot Ádámtól!',
    },

    intro: {
      title: 'Isten éltessen 22. születésnapodon!',
      briefing: [
        'Ma egy cseppet csapdába csaltunk, ugyanis nem hagyományos kocsmázás vár rád.',
        'Ahhoz, hogy eljuss a végső célhoz, meg kell csinálnod a yearly questjeidet.',
        'Minden állomáson Ádám állja a számlát, neked csak választanod és vezetned a csapatot.'
      ],
      rules: [
        'Markó pénztárcája ma este pihen.',
        'Hajrá szex!',
        'Jóisten a mennybe, emide menj be!'
      ],
      inventory: [
        '🎳 Bowling pálya & versenyszellem',
        '🍔 Választott szülinapi vacsora',
        '🍻 Titkos kocsma hideg-meleg kereső',
        '👥 A legjobb baráti társaság'
      ]
    },

    // 1. ÁLLOMÁS: BOWLING (Fix program, térkép és "itt találkozunk" nélkül)
    bowling: {
      title: '1. Állomás: Bowling Showdown',
      venueName: 'Strike Bowling Club [PLACEHOLDER]',
      venueAddress: '1117 Budapest, Október huszonharmadika u. 8-10. [PLACEHOLDER]',
      meetingTime: '18:00 [PLACEHOLDER]',
      description: 'Gurítsunk minél több strike-ot a 22. születésnap méltó megünneplésére!',
      challenge: {
        goalText: 'Gyűjts össze legalább 3 Strike-ot vagy Spare-t a meccs alatt!',
        targetStrikes: 3
      },
      // 🎭 VICCES ARCFELISMERÉS
      faceScan: {
        title: 'BIOMETRIKUS AZONOSÍTÁS',
        subtitle: 'Kérlek nézz a kamerába a születésnapi jogosultság igazolásához...',
        imagePath: '/images/marko_funny.jpg',
        soundPath: '/sounds/omg-bruh-oh-hell-nah.mp3',
        identifiedName: 'MARKÓ (22 ÉVES GYANÚSÍTOTT)',
        caption: '⚠️ FIGYELEM: Az arcfelismerő Markó későbbi állapotát ismerte fel! Azonnali bowlingozásra lettél kötelezve.'
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
            lat: 47.4765, // PLACEHOLDER koordináta
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
            lat: 47.4840, // PLACEHOLDER koordináta
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
            lat: 47.4920, // PLACEHOLDER koordináta
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
            lat: 47.4990, // PLACEHOLDER koordináta
            lng: 19.0650,
          }
        }
      ]
    },

    // 3. ÁLLOMÁS: KOCSMÁZÁS (CSAK HIDEG-MELEG + MYSTERY MONDATOK)
    bar: {
      title: '3. Állomás: A Titkos Kocsma Kereső',
      riddle: 'Válasszátok ki a záró kocsma rejtélyes jeligéjét, majd kövessétek a Hideg-Meleg jelzést a célba érésig!',
      options: [
        {
          id: 'bar_1',
          mysteryPhrase: 'az xG mindig nyüzsgő otthona',
          note: 'A Grund, Corvin negyed',
          venueName: 'A Grund [PLACEHOLDER]',
          venueAddress: '1082 Budapest, Nagytemplom u. 30. [PLACEHOLDER]',
          mapsUrl: 'https://maps.google.com/?q=A+Grund+Budapest',
          targetLocation: {
            lat: 47.4862, // DUMMY KOORDINÁTA - Írd át szabadon!
            lng: 19.0760, // DUMMY KOORDINÁTA - Írd át szabadon!
          }
        },
        {
          id: 'bar_2',
          mysteryPhrase: 'Choose your character',
          note: 'BarCraft Corvin',
          venueName: 'BarCraft Corvin [PLACEHOLDER]',
          venueAddress: '1092 Budapest, Ferenc krt. 34. [PLACEHOLDER]',
          mapsUrl: 'https://maps.google.com/?q=BarCraft+Corvin+Budapest',
          targetLocation: {
            lat: 47.4850, // DUMMY KOORDINÁTA - Írd át szabadon!
            lng: 19.0690, // DUMMY KOORDINÁTA - Írd át szabadon!
          }
        },
        {
          id: 'bar_3',
          mysteryPhrase: 'nyugalom a káoszban',
          note: '7ker pub (Blaha)',
          venueName: '7ker Pub [PLACEHOLDER]',
          venueAddress: '1072 Budapest, Blaha Lujza tér környéke [PLACEHOLDER]',
          mapsUrl: 'https://maps.google.com/?q=7ker+Pub+Budapest',
          targetLocation: {
            lat: 47.4960, // DUMMY KOORDINÁTA - Írd át szabadon!
            lng: 19.0680, // DUMMY KOORDINÁTA - Írd át szabadon!
          }
        },
        {
          id: 'bar_4',
          mysteryPhrase: 'irány a romok közé',
          note: 'Füge Udvar romkocsma',
          venueName: 'Füge Udvar [PLACEHOLDER]',
          venueAddress: '1072 Budapest, Klauzál u. 19. [PLACEHOLDER]',
          mapsUrl: 'https://maps.google.com/?q=Fuge+Udvar+Budapest',
          targetLocation: {
            lat: 47.4990, // DUMMY KOORDINÁTA - Írd át szabadon!
            lng: 19.0640, // DUMMY KOORDINÁTA - Írd át szabadon!
          }
        },
        {
          id: 'bar_5',
          mysteryPhrase: 'bort iszik és vizet prédikál',
          note: 'Humbák Borkápolna',
          venueName: 'Humbák Borkápolna [PLACEHOLDER]',
          venueAddress: '1074 Budapest, Dohány u. / Erzsébet krt. [PLACEHOLDER]',
          mapsUrl: 'https://maps.google.com/?q=Humbak+Borkapolna+Budapest',
          targetLocation: {
            lat: 47.4975, // DUMMY KOORDINÁTA - Írd át szabadon!
            lng: 19.0655, // DUMMY KOORDINÁTA - Írd át szabadon!
          }
        }
      ],
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
