const nodemailer = require('nodemailer');

module.exports = async (req, res) => {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    try {
        const payload = req.body;
        const fields = payload?.data?.fields || [];

        let name = "Teljesítő";
        let recipientEmail = "";

        // Tally payload feldolgozása
        for (const field of fields) {
            // Tally-ben az email mező típusa általában INPUT_EMAIL
            if (field.type === 'INPUT_EMAIL') {
                recipientEmail = field.value;
            }
            // A nevet a címke alapján próbáljuk kitalálni
            if (field.label && (field.label.toLowerCase().includes('neved') || field.label.toLowerCase().includes('név'))) {
                name = field.value;
            }
        }

        if (!recipientEmail) {
            return res.status(400).json({ error: 'Nem található e-mail cím az űrlapban.' });
        }

        // Email küldő beállítása
        const transporter = nodemailer.createTransport({
            host: 'smtp.gmail.com',
            port: 465,
            secure: true,
            auth: {
                user: 'vitasteps.team@gmail.com',
                pass: process.env.SMTP_PASSWORD // Ezt a .env fájlból húzza be!
            }
        });

        const htmlTemplate = `<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VitaSteps Prédikálószék Vertical</title>
    <style>
        body { margin: 0; padding: 0; background-color: #0b0f19; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #ffffff; }
        .wrapper { width: 100%; background-color: #0b0f19; padding-bottom: 40px; }
        .main { background-color: #121824; margin: 0 auto; width: 100%; max-width: 600px; border-radius: 12px; overflow: hidden; border: 1px solid rgba(196, 255, 0, 0.15); border-collapse: collapse; }
        .header { padding: 40px 20px; text-align: center; background: linear-gradient(180deg, #161f33 0%, #121824 100%); border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
        .logo { font-size: 24px; font-weight: 900; letter-spacing: 4px; color: #ffffff; margin: 0; }
        .logo span { color: #c4ff00; }
        .content { padding: 40px 30px; }
        h1 { font-size: 24px; font-weight: 700; color: #ffffff; margin-top: 0; margin-bottom: 20px; }
        h2 { font-size: 18px; font-weight: 700; color: #c4ff00; margin-top: 30px; margin-bottom: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding-bottom: 10px; }
        p { font-size: 16px; line-height: 1.6; color: #d1d5db; margin-top: 0; margin-bottom: 20px; }
        .highlight { color: #c4ff00; font-weight: 600; }
        .btn { display: inline-block; background-color: #c4ff00; color: #000000; font-weight: 700; text-decoration: none; padding: 14px 28px; border-radius: 8px; font-size: 16px; margin-top: 10px; margin-bottom: 20px; }
        .cta-container { text-align: center; margin: 30px 0; }
        .info-card { background-color: rgba(196, 255, 0, 0.05); border-left: 4px solid #c4ff00; padding: 15px; border-radius: 0 8px 8px 0; margin-bottom: 20px; }
        .footer { padding: 30px 20px; text-align: center; background-color: #0b0f19; border-top: 1px solid rgba(255, 255, 255, 0.05); }
        .footer p { font-size: 12px; color: #6b7280; margin: 0; }
    </style>
</head>
<body>
    <center class="wrapper">
        <table class="main" width="100%">
            <tr>
                <td class="header">
                    <h1 class="logo">VITA<span>STEPS</span></h1>
                </td>
            </tr>
            <tr>
                <td class="content">
                    <h1>Kedves ${name}!</h1>
                    
                    <p>Sikeresen feldolgoztuk az igazolásodat! Gratulálunk a <span class="highlight">Prédikálószék Vertical</span> kihívás teljesítéséhez! 🎉</p>
                    
                    <p>Óriási teljesítmény, és nagyon büszkék vagyunk rád, hogy a közösségünk része vagy.</p>
                    
                    <h2>1. 📦 Szállítási adatok megadása (Nagyon Fontos!)</h2>
                    <p>Az érmek kiküldése várhatóan <strong>június 30-tól indul el</strong>.</p>
                    <p>Kérjük, hogy az alábbi gombra kattintva látogass el a szállítási oldalunkra, ahol kiválaszthatod, hogy melyik Foxpost, Packeta vagy MPL csomagpontra kéred a megérdemelt érmedet!</p>
                    
                    <div class="cta-container">
                        <a href="https://vitasteps.vercel.app/szallitas.html" class="btn" target="_blank">📦 Szállítási adatok megadása</a>
                    </div>
                    
                    <h2>2. 🚀 Érkezik a saját Felhasználói fiókod és a Ranglista!</h2>
                    <p>Gőzerővel dolgozunk a weboldalunk bővítésén! Hamarosan elindul a saját <strong>Felhasználói fiókod</strong>, ahol nyomon követheted a megszerzett kilométereidet, láthatod a közös <strong>Ranglistát</strong>, és összekötheted a profilodat a túratársaiddal is. A digitális, sorszámozott okleveledet is ezen a felületen fogod tudni letölteni.</p>
                    
                    <div class="info-card" style="border-left: 4px solid #c4ff00;">
                        <p style="margin: 0; font-size: 14px; color: #ffffff;">
                            <strong>💡 Fontos:</strong> Ha egyetlen e-mail címmel több nevezést is vásároltál (tehát a családod vagy a barátaid is veled tartottak), kérjük, hogy a fenti szállítási űrlapon feltétlenül add meg az ő e-mail címeiket is! Így nekik is saját fiókot tudunk létrehozni, hogy jóváírhassuk a kilométereiket.
                        </p>
                    </div>
                    
                    <p>Még egyszer gratulálunk, várjuk a szállítási adataidat, és hamarosan jelentkezünk! Ha bármilyen kérdésed van, csak válaszolj erre az e-mailre.</p>
                    
                    <p style="margin-top: 30px; margin-bottom: 0;">Üdvözlettel,<br><strong>A VitaSteps Csapata</strong></p>
                </td>
            </tr>
            <tr>
                <td class="footer">
                    <p>© 2026 VitaSteps. Minden jog fenntartva.<br>Kérdés esetén írj nekünk: vitasteps.team@gmail.com</p>
                </td>
            </tr>
        </table>
    </center>
</body>
</html>`;

        await transporter.sendMail({
            from: '"VitaSteps" <vitasteps.team@gmail.com>',
            to: recipientEmail,
            subject: '🏔️ VitaSteps Prédikálószék Vertical – Gratulálunk a teljesítéshez! (Szállítási adatok)',
            html: htmlTemplate
        });

        return res.status(200).json({ success: true, message: `Email elküldve neki: ${recipientEmail}` });

    } catch (error) {
        console.error('Email sending error:', error);
        return res.status(500).json({ error: 'Szerver hiba történt az email küldése közben.' });
    }
}
