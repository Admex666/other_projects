// Leaderboard API – statikus dummy adatok a landing page-hez.
// A valós Google Sheets integráció a jövőbeni, bejelentkezett felhasználói
// ranglistához lesz elkészítve.

const finishers = [
    { name: "Eszter",   county: "Győr-Moson-Sopron", distance: "15 km", completedDateLabel: "2026. máj. 28." },
    { name: "Zoltán",   county: "Pest",               distance: "20 km", completedDateLabel: "2026. máj. 29." },
    { name: "Katalin",  county: "Budapest",            distance: "10 km", completedDateLabel: "2026. máj. 30." },
    { name: "Attila",   county: "Fejér",               distance: "25 km", completedDateLabel: "2026. máj. 31." },
    { name: "István",   county: "Komárom-Esztergom",   distance: "15 km", completedDateLabel: "2026. jún. 1."  },
    { name: "Veronika", county: "Veszprém",             distance: "20 km", completedDateLabel: "2026. jún. 1."  },
    { name: "Tamás",    county: "Budapest",             distance: "25 km", completedDateLabel: "2026. jún. 2."  },
    { name: "Nikolett", county: "Pest",                 distance: "10 km", completedDateLabel: "2026. jún. 4."  },
    { name: "Balázs",   county: "Somogy",               distance: "20 km", completedDateLabel: "2026. jún. 5."  },
    { name: "Réka",     county: "Hajdú-Bihar",          distance: "15 km", completedDateLabel: "2026. jún. 6."  },
    { name: "Gábor",    county: "Budapest",             distance: "25 km", completedDateLabel: "2026. jún. 7."  },
    { name: "Orsolya",  county: "Bács-Kiskun",          distance: "15 km", completedDateLabel: "2026. jún. 8."  },
    { name: "Péter",    county: "Pest",                 distance: "20 km", completedDateLabel: "2026. jún. 9."  },
    { name: "Adrienn",  county: "Győr-Moson-Sopron",   distance: "10 km", completedDateLabel: "2026. jún. 10." },
    { name: "László",   county: "Csongrád-Csanád",      distance: "15 km", completedDateLabel: "2026. jún. 11." },
    { name: "Zsuzsa",   county: "Budapest",             distance: "20 km", completedDateLabel: "2026. jún. 13." },
    { name: "Norbert",  county: "Komárom-Esztergom",   distance: "25 km", completedDateLabel: "2026. jún. 14." },
    { name: "Ágnes",    county: "Pest",                 distance: "15 km", completedDateLabel: "2026. jún. 15." },
    { name: "Roland",   county: "Fejér",                distance: "20 km", completedDateLabel: "2026. jún. 17." },
    { name: "Tímea",    county: "Veszprém",             distance: "10 km", completedDateLabel: "2026. jún. 18." },
    { name: "Csaba",    county: "Budapest",             distance: "25 km", completedDateLabel: "2026. jún. 19." },
];

const inProgress = [
    { name: "Krisztina", county: "Pest",               distance: "15 km" },
    { name: "Dániel",    county: "Borsod-Abaúj-Zemplén", distance: "20 km" },
    { name: "Judit",     county: "Budapest",            distance: "10 km" },
    { name: "Márton",    county: "Vas",                 distance: "25 km" },
    { name: "Enikő",     county: "Zala",                distance: "15 km" },
    { name: "Viktor",    county: "Pest",                distance: "20 km" },
    { name: "Szilvia",   county: "Győr-Moson-Sopron",  distance: "15 km" },
    { name: "Bence",     county: "Budapest",            distance: "10 km" },
    { name: "Fanni",     county: "Tolna",               distance: "20 km" },
    { name: "Imre",      county: "Heves",               distance: "15 km" },
    { name: "Bernadett", county: "Pest",                distance: "25 km" },
    { name: "Ádám",      county: "Komárom-Esztergom",  distance: "20 km" },
];

module.exports = async (req, res) => {
    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    const allUsers = [
        ...finishers.map((u, i) => ({
            rank: i + 1,
            name: u.name,
            county: u.county,
            distance: u.distance,
            status: 'finished',
            completedDateLabel: u.completedDateLabel,
        })),
        ...inProgress.map(u => ({
            rank: null,
            name: u.name,
            county: u.county,
            distance: u.distance,
            status: 'in_progress',
            completedDateLabel: null,
        })),
    ];

    res.status(200).json({
        users: allUsers,
        finisherCount: finishers.length,
        totalCount: allUsers.length,
    });
};
