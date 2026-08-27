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
      lockedMessage: 'Isten éltessen Lukács! A mai program zárolva van az indulásig. A feloldó kódot a találkozáskor kapod meg.',
      hint: 'Kérd el a 4 számjegyű kódot Ádámtól az ajándék átadásakor!',
    },

    intro: {
      title: 'Isten éltessen 22. szülinapodon!',
      briefing: [
        'A mai este egy kisebb quest sorozatot raktunk össze neked.',
        'Minden állomáson Ádám állja a számládat, neked csak választanod és vezetned kell a csapatot.',
        'Készülj lélekben az állomasokra!'
      ],
      rules: [
        'Markó pénztárcája ma este pihen.',
        'Hajrá szex!',
        'Jóisten a mennybe, emide menj be!'
      ],
      inventory: [
        '🎱 Biliárd asztal & dákópárbaj',
        '🥙 Születésnapi vacsora választás',
        '🍻 3 Kocsma hideg-meleg kereső',
        '👥 A legjobb baráti társaság'
      ]
    },

    // 1. ÁLLOMÁS: BILIÁRD SHOWDOWN (All-inn Pub, Kálvin tér, cím nélkül)
    billiard: {
      title: '1. Állomás: Biliárd',
      venueName: 'All-inn Pub',
      meetingTime: '18:30',
      targetLocation: {
        lat: 47.4892848,
        lng: 19.0628989,
      },
      description: 'Kezdjük az estét egy jó öreg biliárd partival a 22. születésnap méltó megünneplésére!',
      // 🎭 VICCES ARCFELISMERÉS
      faceScan: {
        title: 'BIOMETRIKUS AZONOSÍTÁS',
        subtitle: 'Kérlek nézz a kamerába a születésnapi jogosultság igazolásához...',
        imagePath: '/images/marko_funny.jpg',
        soundPath: '/sounds/omg-bruh-oh-hell-nah.mp3',
        identifiedName: 'MARKÓ (22 ÉVES GYANÚSÍTOTT)',
        caption: '⚠️ FIGYELEM: Az arcfelismerő Markó későbbi állapotát ismerte fel! Azonnali biliárdozásra lettél kötelezve.'
      }
    },

    // 2. ÁLLOMÁS: BILIÁRD UTÁNI TÁPLÁLKOZÁSI STRATÉGIA (Kálvin tér gasztro)
    food: {
      title: 'BILIÁRD UTÁNI TÁPLÁLKOZÁSI STRATÉGIA',
      introText: 'Sportolás után szükséges a megfelelő (vagy kevésbé megfelelő) táplálkozás. A Kálvin Kebab az örök favorit, de van itt még pár komoly versenyző a Kálvin téren:',
      options: [
        {
          id: 'food_kebab',
          title: 'Kálvin Kebab',
          category: 'A Verhetetlen Favorit',
          description: 'A legendás Kálvin Kebab: szaftos hús, ropogós zöldségek, tökéletes szószok. Nem vitás, a szív erre vágyik (no nem a zsírok miatt).',
          badge: '🥙 FAVORIT',
          image: '🥙',
          venueName: 'Kálvin Kebab',
          venueAddress: '1053 Budapest, Kálvin tér 2.',
          mapsUrl: 'https://maps.google.com/?q=Kalvin+Kebab+Budapest',
          targetLocation: {
            lat: 47.4896,
            lng: 19.0592,
          }
        },
        {
          id: 'food_wrapido',
          title: 'Wrapido',
          category: 'Mexikói Étterem',
          description: 'Burritók, quesadillák, tacók és fűszeres mexikói ízkavalkád egyenesen a Kálvin térnél.',
          badge: '🌯 MEXIKÓI',
          image: '🌯',
          venueName: 'Wrapido Mexikói Étterem',
          venueAddress: '1092 Budapest, Ráday u. 1-3. (Kálvin tér)',
          mapsUrl: 'https://maps.google.com/?q=Wrapido+Budapest',
          targetLocation: {
            lat: 47.4890,
            lng: 19.0601,
          }
        },
        {
          id: 'food_heybao',
          title: 'Heybao',
          category: 'Kínai Bao Étterem',
          description: 'Autentikus gőzölt bao bucik, gazdag húsos és zöldséges töltelékek Ázsia szívéből.',
          badge: '🥟 HEYBAO',
          image: '🥟',
          venueName: 'Heybao Kínai Étterem',
          venueAddress: '1053 Budapest, Múzeum krt. / Kálvin tér',
          mapsUrl: 'https://maps.google.com/?q=Heybao+Budapest',
          targetLocation: {
            lat: 47.4912,
            lng: 19.0608,
          }
        },
        {
          id: 'food_bk',
          title: 'Burger King',
          category: 'Kálvin tér',
          description: 'Lángon grillezett marhahúsos Whopper, ropogós hagymakarikák és klasszikus gyorséttermi élvezet.',
          badge: '🍔 BK GRILL',
          image: '🍔',
          venueName: 'Burger King Kálvin tér',
          venueAddress: '1085 Budapest, Kálvin tér 9.',
          mapsUrl: 'https://maps.google.com/?q=Burger+King+Kalvin+ter+Budapest',
          targetLocation: {
            lat: 47.4898,
            lng: 19.0605,
          }
        }
      ]
    },

    // 🍻 4 KOCSMA ÁLLOMÁS A KELETI FELÉ (MINDENGYIKNÉL 3 VÁLASZTÁSI LEHETŐSÉG)
    bars: {
      thresholdsMeters: {
        burning: 30,
        hot: 100,
        warm: 250,
        cold: 500,
      },
      stages: [
        // 3. ÁLLOMÁS: 1. KOCSMA
        {
          id: 'bar1',
          title: '3. Állomás: 1. Kocsma',
          riddle: 'Válaszd ki az 1. kocsma jeligéjét, majd kövesd a Hideg-Meleg jelzést!',
          options: [
            {
              id: 'bar1_opt1',
              mysteryPhrase: 'Imádom Csehországot',
              venueName: 'Prága Pub',
              targetLocation: { lat: 47.48969006241866, lng: 19.06392063313614 }
            },
            {
              id: 'bar1_opt2',
              mysteryPhrase: 'Imádom Írországot',
              venueName: 'Harat’s Pub Budapest',
              targetLocation: { lat: 47.48907362739634, lng: 19.06164956530825 }
            },
            {
              id: 'bar1_opt3',
              mysteryPhrase: 'Csapról kérném',
              venueName: 'MONYO Tap House',
              targetLocation: { lat: 47.488715833121496, lng: 19.061126454185892 }
            }
          ]
        },

        // 4. ÁLLOMÁS: 2. KOCSMA
        {
          id: 'bar2',
          title: '4. Állomás: 2. Kocsma',
          riddle: 'Válaszd ki a 2. kocsma jeligéjét, majd indulhat a Hideg-Meleg keresés!',
          options: [
            {
              id: 'bar2_opt1',
              mysteryPhrase: 'Irány bölcsészkedni',
              venueName: 'Zuzmó',
              targetLocation: { lat: 47.48727557025906, lng: 19.070044755840495 }
            },
            {
              id: 'bar2_opt2',
              mysteryPhrase: 'Choose your character',
              venueName: 'BarCraft Corvin',
              targetLocation: { lat: 47.484505564631526, lng: 19.069262890441227 }
            },
            {
              id: 'bar2_opt3',
              mysteryPhrase: 'az xG-kért bármit megteszek',
              venueName: 'A Grund',
              targetLocation: { lat: 47.48519255558903, lng: 19.076712767309782 }
            }
          ]
        },

        // 5. ÁLLOMÁS: 3. KOCSMA
        {
          id: 'bar3',
          title: '5. Állomás: 3. Kocsma',
          riddle: 'Válaszd ki a 3. kocsma jeligéjét, és kövesd a hőmérsékletjelzőt!',
          options: [
            {
              id: 'bar3_opt1',
              mysteryPhrase: 'Nyugalom a káoszban',
              venueName: 'Hétker pub',
              targetLocation: { lat: 47.49773118720746, lng: 19.069439627701048 }
            },
            {
              id: 'bar3_opt2',
              mysteryPhrase: 'Irány a romok közé',
              venueName: 'Füge Udvar',
              targetLocation: { lat: 47.49843850710749, lng: 19.06655678333415 }
            },
            {
              id: 'bar3_opt3',
              mysteryPhrase: 'Bort iszik és vizet prédikál',
              venueName: 'Humbák Borkápolna',
              targetLocation: { lat: 47.50023239166089, lng: 19.06986446792354 }
            }
          ]
        }
      ]
    },

    // 6. LEZÁRÁS: GRAND FINALE
    finale: {
      title: 'Küldetés Teljesítve',
      celebrationTitle: 'Boldog 22. Születésnapot, Markó!',
      message: [
        'Sikeresen végigjártuk a tervezett állomásokat: a biliárdot, a vacsorát és a 3 kocsmát is!',
        'Nagyon örülünk, hogy együtt ünnepelhetünk veled. Isten éltessen még nagyon sokáig!',
        'Most már nincs több küldetés: élvezd az estét és a közös koccintást! 🍻🎉'
      ],
      badges: [
        {
          title: 'Biliárd Mester',
          icon: '🎱',
          desc: 'Közös játék az All-inn Pub asztalainál'
        },
        {
          title: 'Kálvin Gasztro Király',
          icon: '👑',
          desc: 'Tökéletesen megválasztott születésnapi vacsora'
        },
        {
          title: 'Kocsmatúra Bajnok',
          icon: '🍻',
          desc: '3 sikeres kocsmaállomás teljesítve a Hideg-Meleg alapján'
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
