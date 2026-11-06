const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });
require('dotenv').config({ path: path.resolve(__dirname, '../../../.env') });
require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
    process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

const CSV_FILE = path.resolve(__dirname, '../../data/kitero_nps10_recipients.csv');

function parseCsv(content) {
    const lines = content.split(/\r?\n/).filter(line => line.trim().length > 0);
    if (lines.length < 2) return [];

    const headers = lines[0].split(',').map(h => h.trim());
    const rows = [];

    for (let i = 1; i < lines.length; i++) {
        const line = lines[i];
        // Handle quoted values with commas
        const values = [];
        let inQuotes = false;
        let currentValue = '';

        for (let c = 0; c < line.length; c++) {
            const char = line[c];
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                values.push(currentValue);
                currentValue = '';
            } else {
                currentValue += char;
            }
        }
        values.push(currentValue);

        const row = {};
        headers.forEach((h, idx) => {
            row[h] = values[idx] ? values[idx].trim() : '';
        });
        rows.push(row);
    }
    return rows;
}

async function getKiteroFunnelData() {
    let recipientsRaw = [];
    if (fs.existsSync(CSV_FILE)) {
        try {
            const raw = fs.readFileSync(CSV_FILE, 'utf8');
            recipientsRaw = parseCsv(raw);
        } catch (err) {
            console.error('Error reading kitero_nps10_recipients.csv:', err);
        }
    }

    // 1. Fetch relevant events from analytics_events
    // We fetch events where event_name is one of the funnel stages
    let events = [];
    try {
        const { data, error } = await supabase
            .from('analytics_events')
            .select('id, session_id, visitor_id, event_name, event_data, created_at')
            .in('event_name', [
                'email_open',
                'landing_view',
                'email_click',
                'scroll_25',
                'scroll_50',
                'scroll_75',
                'scroll_90',
                'pricing_view',
                'cta_click',
                'lead_submit'
            ])
            .order('created_at', { ascending: true });

        if (!error && data) {
            events = data;
        }
    } catch (e) {
        console.error('Error fetching analytics_events for kitero:', e);
    }

    // 2. Fetch leads from leads table
    let kiteroLeads = [];
    try {
        const { data, error } = await supabase
            .from('leads')
            .select('id, email, name, campaign, source, created_at')
            .eq('campaign', 'kitero_val_1');

        if (!error && data) {
            kiteroLeads = data;
        }
    } catch (e) {
        console.error('Error fetching kitero leads:', e);
    }

    // Build indexing structures
    // Map CID -> list of events
    const cidToEvents = {};
    // Map session_id -> cid
    const sessionToCid = {};
    // Map visitor_id -> cid
    const visitorToCid = {};

    // First pass: identify session_ids & visitor_ids that are directly linked to a CID
    events.forEach(evt => {
        const cid = evt.event_data?.cid;
        if (cid) {
            if (!cidToEvents[cid]) cidToEvents[cid] = [];
            cidToEvents[cid].push(evt);

            if (evt.session_id) sessionToCid[evt.session_id] = cid;
            if (evt.visitor_id) visitorToCid[evt.visitor_id] = cid;
        }
    });

    // Second pass: associate events that share the same session_id or visitor_id
    events.forEach(evt => {
        const directCid = evt.event_data?.cid;
        if (!directCid) {
            const inferredCid = sessionToCid[evt.session_id] || visitorToCid[evt.visitor_id];
            if (inferredCid) {
                if (!cidToEvents[inferredCid]) cidToEvents[inferredCid] = [];
                cidToEvents[inferredCid].push(evt);
            }
        }
    });

    // Map lead email -> lead record
    const leadsByEmail = {};
    const leadsBySourceCid = {};
    kiteroLeads.forEach(ld => {
        if (ld.email) leadsByEmail[ld.email.toLowerCase().trim()] = ld;
        if (ld.source && ld.source.startsWith('email_cid_')) {
            const sCid = ld.source.replace('email_cid_', '').trim();
            leadsBySourceCid[sCid] = ld;
        }
    });

    // Process each recipient
    const recipientStatuses = recipientsRaw.map(row => {
        const email = (row.email || '').toLowerCase().trim();
        const cid = (row.cid || '').trim();
        const firstName = (row.first_name || '').trim();
        const allNames = (row.all_names || '').trim();
        const isSent = String(row.sent).trim() === '1';
        const sentAt = row.sent_at || null;

        const matchedEvents = cidToEvents[cid] || [];

        // Count open events
        const openEvents = matchedEvents.filter(e => e.event_name === 'email_open');
        const openCount = openEvents.length;
        const opened = openCount > 0;
        const firstOpenAt = openEvents.length > 0 ? openEvents[0].created_at : null;

        // Clicks / Landing view
        const clickEvents = matchedEvents.filter(e => e.event_name === 'email_click' || e.event_name === 'landing_view');
        const clicked = clickEvents.length > 0;

        // Scroll 50%+
        const scroll50Events = matchedEvents.filter(e => 
            e.event_name === 'scroll_50' || 
            e.event_name === 'scroll_75' || 
            e.event_name === 'scroll_90' ||
            (e.event_data?.scroll_depth && Number(e.event_data.scroll_depth) >= 50)
        );
        const scrolled50 = scroll50Events.length > 0;

        // Pricing view
        const pricingEvents = matchedEvents.filter(e => e.event_name === 'pricing_view' || e.event_name === 'offer_view');
        const viewedPricing = pricingEvents.length > 0;

        // Lead submit
        const leadEvents = matchedEvents.filter(e => e.event_name === 'lead_submit');
        const dbLead = leadsBySourceCid[cid] || leadsByEmail[email];
        const isLead = leadEvents.length > 0 || !!dbLead;
        const leadAt = dbLead ? dbLead.created_at : (leadEvents.length > 0 ? leadEvents[0].created_at : null);

        // Display Name fallback
        let displayName = firstName;
        if (!displayName && allNames) {
            displayName = allNames.split('/')[0].trim();
        }

        return {
            email,
            name: displayName || 'Címzett',
            all_names: allNames,
            cid,
            sent: isSent,
            sent_at: sentAt,
            opened,
            open_count: openCount,
            first_opened_at: firstOpenAt,
            clicked,
            scrolled_50: scrolled50,
            viewed_pricing: viewedPricing,
            is_lead: isLead,
            lead_at: leadAt
        };
    });

    // Funnel Aggregations
    const totalRecipients = recipientStatuses.length;
    const sentRecipients = recipientStatuses.filter(r => r.sent);
    const sentCount = sentRecipients.length;

    // Use sent list as baseline if any sent, else show on total for preview
    const baselineList = sentCount > 0 ? sentRecipients : recipientStatuses;
    const denominator = baselineList.length;

    // 1. Opens
    const totalOpens = baselineList.reduce((acc, r) => acc + r.open_count, 0);
    const uniqueOpeners = baselineList.filter(r => r.opened).length;
    const openRate = denominator > 0 ? (uniqueOpeners / denominator) * 100 : 0;

    // Clicks / Landing
    const uniqueClickers = baselineList.filter(r => r.clicked).length;
    const clickRate = denominator > 0 ? (uniqueClickers / denominator) * 100 : 0;

    // 2. Scroll 50%+
    const uniqueScrollers50 = baselineList.filter(r => r.scrolled_50).length;
    const scroll50Rate = denominator > 0 ? (uniqueScrollers50 / denominator) * 100 : 0;
    const scroll50FromOpens = uniqueOpeners > 0 ? (uniqueScrollers50 / uniqueOpeners) * 100 : 0;

    // 3. Pricing View
    const uniquePricingViewers = baselineList.filter(r => r.viewed_pricing).length;
    const pricingViewRate = denominator > 0 ? (uniquePricingViewers / denominator) * 100 : 0;
    const pricingFromOpens = uniqueOpeners > 0 ? (uniquePricingViewers / uniqueOpeners) * 100 : 0;

    // 4. Lead Submits
    const uniqueLeads = baselineList.filter(r => r.is_lead).length;
    const leadRate = denominator > 0 ? (uniqueLeads / denominator) * 100 : 0;
    const leadFromOpens = uniqueOpeners > 0 ? (uniqueLeads / uniqueOpeners) * 100 : 0;
    const leadFromPricing = uniquePricingViewers > 0 ? (uniqueLeads / uniquePricingViewers) * 100 : 0;

    return {
        success: true,
        summary: {
            total_recipients: totalRecipients,
            sent_count: sentCount,
            is_live_campaign: sentCount > 0,
            total_opens: totalOpens,
            unique_openers: uniqueOpeners,
            open_rate_pct: Number(openRate.toFixed(1)),
            unique_clickers: uniqueClickers,
            click_rate_pct: Number(clickRate.toFixed(1)),
            unique_scrollers_50: uniqueScrollers50,
            scroll_50_rate_pct: Number(scroll50Rate.toFixed(1)),
            scroll_50_from_opens_pct: Number(scroll50FromOpens.toFixed(1)),
            unique_pricing_viewers: uniquePricingViewers,
            pricing_view_rate_pct: Number(pricingViewRate.toFixed(1)),
            pricing_from_opens_pct: Number(pricingFromOpens.toFixed(1)),
            unique_leads: uniqueLeads,
            lead_rate_pct: Number(leadRate.toFixed(1)),
            lead_from_opens_pct: Number(leadFromOpens.toFixed(1)),
            lead_from_pricing_pct: Number(leadFromPricing.toFixed(1))
        },
        recipients: recipientStatuses,
        last_updated: new Date().toISOString()
    };
}

module.exports = {
    getKiteroFunnelData
};
