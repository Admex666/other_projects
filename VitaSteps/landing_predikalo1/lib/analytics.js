const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });
require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
    process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

/**
 * Handle incoming tracking events from the client
 */
async function processAnalyticsEvent(payload) {
    const {
        visitor_id,
        session_id,
        event_name,
        event_data = {},
        url_params = {},
        metrics = {},
        landing_page,
        referrer,
        device_type,
        browser,
        timestamp
    } = payload || {};

    if (!visitor_id || !session_id || !event_name) {
        throw new Error('Hiányzó kötelező mezők: visitor_id, session_id, event_name szükséges.');
    }

    const now = new Date().toISOString();
    const eventTime = timestamp || now;

    // Extract meta IDs and parameters
    const meta_campaign_id   = url_params.meta_campaign_id || url_params.campaign_id || null;
    const meta_campaign_name = url_params.meta_campaign_name || url_params.campaign_name || null;
    const meta_adset_id      = url_params.meta_adset_id || url_params.adset_id || null;
    const meta_adset_name    = url_params.meta_adset_name || url_params.adset_name || null;
    const meta_ad_id         = url_params.meta_ad_id || url_params.ad_id || null;
    const meta_ad_name       = url_params.meta_ad_name || url_params.ad_name || null;

    const utm_source         = url_params.utm_source || null;
    const utm_medium         = url_params.utm_medium || null;
    const utm_campaign       = url_params.utm_campaign || null;
    const utm_content        = url_params.utm_content || null;
    const utm_term           = url_params.utm_term || null;
    const fbclid             = url_params.fbclid || null;

    // 1. VISITOR UPSERT (First-Touch & Last-Touch)
    try {
        const { data: existingVisitor } = await supabase
            .from('analytics_visitors')
            .select('visitor_id, total_sessions')
            .eq('visitor_id', visitor_id)
            .maybeSingle();

        if (!existingVisitor) {
            // New visitor -> First touch
            await supabase.from('analytics_visitors').insert({
                visitor_id,
                first_seen_at: eventTime,
                last_seen_at: eventTime,
                total_sessions: 1,
                total_orders: 0,
                total_revenue: 0,
                first_touch_source: utm_source,
                first_touch_medium: utm_medium,
                first_touch_campaign_id: meta_campaign_id,
                first_touch_campaign_name: meta_campaign_name || utm_campaign,
                first_touch_adset_id: meta_adset_id,
                first_touch_adset_name: meta_adset_name,
                first_touch_ad_id: meta_ad_id,
                first_touch_ad_name: meta_ad_name || utm_content,
                first_touch_content: utm_content,
                first_touch_fbclid: fbclid,
                first_touch_landing_page: landing_page,
                last_touch_source: utm_source,
                last_touch_medium: utm_medium,
                last_touch_campaign_id: meta_campaign_id,
                last_touch_campaign_name: meta_campaign_name || utm_campaign,
                last_touch_adset_id: meta_adset_id,
                last_touch_adset_name: meta_adset_name,
                last_touch_ad_id: meta_ad_id,
                last_touch_ad_name: meta_ad_name || utm_content,
                last_touch_content: utm_content,
                last_touch_fbclid: fbclid,
                last_touch_landing_page: landing_page
            });
        } else {
            // Existing visitor -> Update last touch and session counter if landing
            const updates = {
                last_seen_at: eventTime,
                updated_at: now
            };
            if (utm_source || meta_campaign_id || meta_ad_id) {
                updates.last_touch_source = utm_source;
                updates.last_touch_medium = utm_medium;
                updates.last_touch_campaign_id = meta_campaign_id;
                updates.last_touch_campaign_name = meta_campaign_name || utm_campaign;
                updates.last_touch_adset_id = meta_adset_id;
                updates.last_touch_adset_name = meta_adset_name;
                updates.last_touch_ad_id = meta_ad_id;
                updates.last_touch_ad_name = meta_ad_name || utm_content;
                updates.last_touch_content = utm_content;
                updates.last_touch_fbclid = fbclid;
                updates.last_touch_landing_page = landing_page;
            }
            if (event_name === 'landing_session') {
                updates.total_sessions = (existingVisitor.total_sessions || 1) + 1;
            }
            await supabase.from('analytics_visitors').update(updates).eq('visitor_id', visitor_id);
        }
    } catch (vErr) {
        console.warn('Analytics visitor upsert warning:', vErr.message);
    }

    // 2. SESSION UPSERT
    try {
        const time_on_page     = metrics.time_on_page !== undefined ? Math.round(Number(metrics.time_on_page)) : undefined;
        const max_scroll_depth = metrics.max_scroll_depth !== undefined ? Math.round(Number(metrics.max_scroll_depth)) : undefined;
        const offer_viewed     = metrics.offer_viewed === true || event_name === 'offer_view';
        const cta_clicked      = metrics.cta_clicked === true || event_name === 'cta_click';
        const checkout_started = metrics.checkout_started === true || event_name === 'checkout_start';

        const { data: existingSession } = await supabase
            .from('analytics_sessions')
            .select('session_id, time_on_page, max_scroll_depth, offer_viewed, cta_clicked, checkout_started')
            .eq('session_id', session_id)
            .maybeSingle();

        if (!existingSession) {
            await supabase.from('analytics_sessions').insert({
                session_id,
                visitor_id,
                created_at: eventTime,
                updated_at: now,
                meta_campaign_id,
                meta_campaign_name,
                meta_adset_id,
                meta_adset_name,
                meta_ad_id,
                meta_ad_name,
                utm_source,
                utm_medium,
                utm_campaign,
                utm_content,
                utm_term,
                fbclid,
                landing_page,
                referrer,
                device_type,
                browser,
                time_on_page: time_on_page || 0,
                max_scroll_depth: max_scroll_depth || 0,
                offer_viewed: offer_viewed || false,
                cta_clicked: cta_clicked || false,
                checkout_started: checkout_started || false,
                checkout_completed: false,
                purchase_completed: false
            });
        } else {
            const updates = { updated_at: now };
            if (time_on_page !== undefined && time_on_page > (existingSession.time_on_page || 0)) {
                updates.time_on_page = time_on_page;
            }
            if (max_scroll_depth !== undefined && max_scroll_depth > (existingSession.max_scroll_depth || 0)) {
                updates.max_scroll_depth = max_scroll_depth;
            }
            if (offer_viewed) updates.offer_viewed = true;
            if (cta_clicked) updates.cta_clicked = true;
            if (checkout_started) updates.checkout_started = true;
            if (event_name === 'checkout_complete') updates.checkout_completed = true;
            if (event_name === 'purchase') {
                updates.purchase_completed = true;
                if (event_data.order_id) updates.order_id = event_data.order_id;
                if (event_data.amount) updates.revenue = Number(event_data.amount);
            }

            await supabase.from('analytics_sessions').update(updates).eq('session_id', session_id);
        }
    } catch (sErr) {
        console.warn('Analytics session upsert warning:', sErr.message);
    }

    // 3. EVENT INSERT
    try {
        await supabase.from('analytics_events').insert({
            session_id,
            visitor_id,
            event_name,
            event_data,
            meta_campaign_id,
            meta_adset_id,
            meta_ad_id,
            created_at: eventTime
        });
    } catch (eErr) {
        console.warn('Analytics event insert warning:', eErr.message);
    }

    return { success: true, session_id, visitor_id, event_name };
}

module.exports = {
    processAnalyticsEvent
};
