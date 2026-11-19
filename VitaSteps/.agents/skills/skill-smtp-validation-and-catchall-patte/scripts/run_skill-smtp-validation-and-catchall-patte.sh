[Kliens]  ---> HELO peerplay.local
[Szerver] <--- 250 Hello!

[Kliens]  ---> MAIL FROM:<probe@peerplay.local>
[Szerver] <--- 250 2.1.0 Sender OK

[Kliens]  ---> [1. CATCH-ALL PROBE] RCPT TO:<nonexistent_random_xyz@domain.hu>
[Szerver] <--- 550 User Unknown  (✅ Pontos szerver)  VAGY  250 OK (⚠️ Catch-All!)

[Kliens]  ---> RSET
[Kliens]  ---> MAIL FROM:<probe@peerplay.local>

[Kliens]  ---> [2. JELÖLT TESZT] RCPT TO:<keresztnev.vezeteknev@domain.hu>
[Szerver] <--- 250 Recipient OK  (✅ Létező postafiók)  VAGY  550 Recipient Rejected (❌ Lepattanó)

[Kliens]  ---> QUIT  (Kapcsolat bontása, NULLA levél kézbesítve)
