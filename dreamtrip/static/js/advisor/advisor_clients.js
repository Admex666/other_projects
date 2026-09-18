/**
 * Optivoya Advisor Workspace — Client Profile & Preference Manager
 * Allows inspecting and updating persistent client DNA (airline, hotel, vibe preferences).
 */

(function () {
    'use strict';

    class AdvisorClientsManager {
        constructor() { }

        openClientDrawer(clientId) {
            const client = window.AdvisorState.state.clients.find(c => c.id === clientId);
            if (!client) return;

            const modal = document.getElementById('clientDetailModal');
            if (!modal) {
                this.createModal();
            }

            this.populateClientData(client);
            document.getElementById('clientDetailModal').style.display = 'flex';
        }

        createModal() {
            const modal = document.createElement('div');
            modal.id = 'clientDetailModal';
            modal.className = 'modal-overlay';
            modal.onclick = (e) => { if (e.target === modal) modal.style.display = 'none'; };

            modal.innerHTML = `
                <div class="modal-card" style="max-width: 680px;">
                    <div style="padding: 18px 24px; border-bottom: 1px solid var(--b2b-border); display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-weight: 800; font-size: 16px;" id="clientModalTitle">👤 Ügyfél Adatlap & Tartós Preferenciák</div>
                        <button type="button" onclick="document.getElementById('clientDetailModal').style.display='none'" style="background:none; border:none; color:#64748b; font-size:20px; cursor:pointer;">✕</button>
                    </div>

                    <form id="clientDetailForm" onsubmit="window.AdvisorClients.saveClientProfile(event)" style="padding: 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px;">
                        <input type="hidden" id="editClientId">

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                            <div>
                                <label class="form-label" style="font-size: 11.5px; font-weight: 700; color: #94a3b8;">Név *</label>
                                <input type="text" id="editClientName" required class="form-control" style="width:100%; background:var(--b2b-card); border-color:var(--b2b-border); color:#fff; padding:8px 12px; border-radius:8px;">
                            </div>
                            <div>
                                <label class="form-label" style="font-size: 11.5px; font-weight: 700; color: #94a3b8;">E-mail *</label>
                                <input type="email" id="editClientEmail" required class="form-control" style="width:100%; background:var(--b2b-card); border-color:var(--b2b-border); color:#fff; padding:8px 12px; border-radius:8px;">
                            </div>
                        </div>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                            <div>
                                <label class="form-label" style="font-size: 11.5px; font-weight: 700; color: #94a3b8;">Telefonszám</label>
                                <input type="tel" id="editClientPhone" class="form-control" style="width:100%; background:var(--b2b-card); border-color:var(--b2b-border); color:#fff; padding:8px 12px; border-radius:8px;">
                            </div>
                            <div>
                                <label class="form-label" style="font-size: 11.5px; font-weight: 700; color: #94a3b8;">Címkék (vesszővel elválasztva)</label>
                                <input type="text" id="editClientTags" class="form-control" style="width:100%; background:var(--b2b-card); border-color:var(--b2b-border); color:#fff; padding:8px 12px; border-radius:8px;">
                            </div>
                        </div>

                        <!-- Tartós Utazási Preferenciák (Travel DNA) -->
                        <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 16px; margin-top: 6px;">
                            <div style="font-weight: 800; font-size: 13px; color: var(--b2b-accent); margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                                <span class="material-symbols-outlined" style="font-size: 18px;">tune</span>
                                Tartós Utazási Preferenciák (Automatikusan öröklődik új ügyekre)
                            </div>

                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                                <div>
                                    <label class="form-label" style="font-size: 11px; font-weight: 700; color: #94a3b8;">Min. Hotel Csillag</label>
                                    <select id="editClientMinStars" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:8px; border-radius:8px;">
                                        <option value="0">Bármilyen</option>
                                        <option value="3">3★ vagy jobb</option>
                                        <option value="4">4★ vagy jobb</option>
                                        <option value="5">5★ (Luxus)</option>
                                    </select>
                                </div>
                                <div>
                                    <div style="display: flex; justify-content: space-between;">
                                        <label class="form-label" style="font-size: 11px; font-weight: 700; color: #94a3b8;">Min. Értékelés:</label>
                                        <strong id="editClientRatingDisp" style="color: var(--b2b-accent); font-family: 'JetBrains Mono', monospace; font-size: 12px;">8.0+</strong>
                                    </div>
                                    <input type="range" id="editClientMinRating" min="7.0" max="9.5" step="0.1" value="8.0" style="width:100%;" oninput="document.getElementById('editClientRatingDisp').innerText = this.value + '+';">
                                </div>
                            </div>

                            <div style="display: flex; gap: 16px; align-items: center; margin-top: 8px;">
                                <label style="font-size: 12px; color: #cbd5e1; display: flex; align-items: center; gap: 6px; cursor: pointer;">
                                    <input type="checkbox" id="editClientDirectOnly">
                                    <span>Csak közvetlen járatok preferáltak</span>
                                </label>
                            </div>
                        </div>

                        <div>
                            <label class="form-label" style="font-size: 11.5px; font-weight: 700; color: #94a3b8;">Általános Jegyzetek</label>
                            <textarea id="editClientNotes" rows="2" class="form-control" style="width:100%; background:var(--b2b-card); border-color:var(--b2b-border); color:#fff; padding:8px 12px; border-radius:8px;"></textarea>
                        </div>

                        <div style="padding-top: 10px; display: flex; justify-content: flex-end; gap: 10px;">
                            <button type="button" onclick="document.getElementById('clientDetailModal').style.display='none'" class="btn btn-secondary">Mégse</button>
                            <button type="submit" class="btn btn-primary" style="background: #0284c7;">Mentés</button>
                        </div>
                    </form>
                </div>
            `;
            document.body.appendChild(modal);
        }

        populateClientData(client) {
            document.getElementById('editClientId').value = client.id;
            document.getElementById('editClientName').value = client.name;
            document.getElementById('editClientEmail').value = client.email;
            document.getElementById('editClientPhone').value = client.phone || '';
            document.getElementById('editClientTags').value = (client.tags || []).join(', ');
            document.getElementById('editClientNotes').value = client.notes || '';

            const prefs = client.preferences || {};
            document.getElementById('editClientMinStars').value = prefs.hotel_min_stars || 3;
            document.getElementById('editClientMinRating').value = prefs.hotel_min_rating || 8.0;
            document.getElementById('editClientRatingDisp').innerText = (prefs.hotel_min_rating || 8.0) + '+';
            document.getElementById('editClientDirectOnly').checked = !!prefs.direct_flights_only;
        }

        async saveClientProfile(e) {
            e.preventDefault();
            const clientId = document.getElementById('editClientId').value;
            const name = document.getElementById('editClientName').value;
            const email = document.getElementById('editClientEmail').value;
            const phone = document.getElementById('editClientPhone').value;
            const tags = document.getElementById('editClientTags').value.split(',').map(s => s.trim()).filter(Boolean);
            const notes = document.getElementById('editClientNotes').value;
            const minStars = parseInt(document.getElementById('editClientMinStars').value, 10);
            const minRating = parseFloat(document.getElementById('editClientMinRating').value);
            const directOnly = document.getElementById('editClientDirectOnly').checked;

            try {
                const res = await window.AdvisorAPI.request(`/clients/${clientId}`, {
                    method: 'PUT',
                    body: JSON.stringify({
                        name,
                        email,
                        phone,
                        tags,
                        notes,
                        preferences: {
                            hotel_min_stars: minStars,
                            hotel_min_rating: minRating,
                            direct_flights_only: directOnly
                        }
                    })
                });

                if (res.status === 'success') {
                    document.getElementById('clientDetailModal').style.display = 'none';
                    await window.AdvisorState.refreshClients();
                    alert(`✅ Ügyfélprofil sikeresen frissítve: "${name}"`);
                }
            } catch (err) {
                alert(`Hiba a mentéskor: ${err.message}`);
            }
        }
    }

    window.AdvisorClients = new AdvisorClientsManager();
})();
