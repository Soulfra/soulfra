/**
 * Cloudflare Worker - Payment Tracker for StPetePros
 *
 * Serverless backend for payment QR system
 * Handles payment confirmations, receipt generation, Stripe webhooks
 *
 * Deploy: wrangler deploy
 * Test: curl https://api.stpetepros.com/health
 *
 * Features:
 * - ✅ Payment tracking (Venmo, CashApp, Zelle, PayPal)
 * - ✅ Receipt generation
 * - ✅ Stripe webhook handling
 * - ✅ Coinbase Commerce webhooks
 * - ✅ CORS for GitHub Pages
 * - ✅ 100k requests/day FREE tier
 */

// Helper: CORS headers
const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

// Helper: JSON response
function jsonResponse(data, status = 200) {
    return new Response(JSON.stringify(data), {
        status,
        headers: {
            'Content-Type': 'application/json',
            ...corsHeaders
        }
    });
}

// Handle OPTIONS (preflight)
function handleOptions() {
    return new Response(null, {
        status: 204,
        headers: corsHeaders
    });
}

export default {
    async fetch(request, env, ctx) {
        // Handle CORS preflight
        if (request.method === 'OPTIONS') {
            return handleOptions();
        }

        const url = new URL(request.url);
        const path = url.pathname;

        // Route handling
        try {
            // Health check
            if (path === '/health') {
                return jsonResponse({
                    status: 'ok',
                    service: 'StPetePros Payment Tracker',
                    version: '1.0.0',
                    timestamp: new Date().toISOString()
                });
            }

            // Create payment
            if (path === '/api/payments' && request.method === 'POST') {
                return await handleCreatePayment(request, env);
            }

            // Get payment status
            if (path.startsWith('/api/payments/') && request.method === 'GET') {
                const paymentId = path.split('/')[3];
                return await handleGetPayment(paymentId, env);
            }

            // Confirm payment
            if (path.startsWith('/api/payments/') && path.endsWith('/confirm') && request.method === 'POST') {
                const paymentId = path.split('/')[3];
                return await handleConfirmPayment(paymentId, request, env);
            }

            // Stripe webhook
            if (path === '/webhooks/stripe' && request.method === 'POST') {
                return await handleStripeWebhook(request, env);
            }

            // Coinbase webhook
            if (path === '/webhooks/coinbase' && request.method === 'POST') {
                return await handleCoinbaseWebhook(request, env);
            }

            // List all payments (admin)
            if (path === '/api/payments' && request.method === 'GET') {
                return await handleListPayments(env);
            }

            // 404
            return jsonResponse({ error: 'Not found' }, 404);

        } catch (error) {
            console.error('Error:', error);
            return jsonResponse({
                error: 'Internal server error',
                message: error.message
            }, 500);
        }
    }
};

/**
 * Create payment
 */
async function handleCreatePayment(request, env) {
    const data = await request.json();

    const {
        payment_method,
        payment_tag,
        amount,
        description,
        professional_id
    } = data;

    // Validate
    if (!payment_method || !payment_tag || !amount) {
        return jsonResponse({ error: 'Missing required fields' }, 400);
    }

    // Generate payment ID
    const paymentId = `pay_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Payment data
    const payment = {
        id: paymentId,
        payment_method,
        payment_tag,
        amount,
        description: description || '',
        professional_id: professional_id || null,
        status: 'pending',
        created_at: new Date().toISOString(),
        confirmed_at: null
    };

    // Store in KV
    await env.PAYMENTS.put(paymentId, JSON.stringify(payment));

    return jsonResponse({
        success: true,
        payment_id: paymentId,
        payment
    });
}

/**
 * Get payment status
 */
async function handleGetPayment(paymentId, env) {
    const paymentJson = await env.PAYMENTS.get(paymentId);

    if (!paymentJson) {
        return jsonResponse({ error: 'Payment not found' }, 404);
    }

    const payment = JSON.parse(paymentJson);

    return jsonResponse({
        success: true,
        payment
    });
}

/**
 * Confirm payment received
 */
async function handleConfirmPayment(paymentId, request, env) {
    const paymentJson = await env.PAYMENTS.get(paymentId);

    if (!paymentJson) {
        return jsonResponse({ error: 'Payment not found' }, 404);
    }

    const payment = JSON.parse(paymentJson);

    if (payment.status === 'confirmed') {
        return jsonResponse({ error: 'Payment already confirmed' }, 400);
    }

    // Update payment
    payment.status = 'confirmed';
    payment.confirmed_at = new Date().toISOString();

    // Generate receipt
    const receiptId = `rcpt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const receipt = {
        id: receiptId,
        payment_id: paymentId,
        amount: payment.amount,
        payment_method: payment.payment_method,
        description: payment.description,
        created_at: new Date().toISOString()
    };

    // Store receipt
    await env.RECEIPTS.put(receiptId, JSON.stringify(receipt));

    // Update payment
    await env.PAYMENTS.put(paymentId, JSON.stringify(payment));

    return jsonResponse({
        success: true,
        payment,
        receipt
    });
}

/**
 * List all payments (admin)
 */
async function handleListPayments(env) {
    const list = await env.PAYMENTS.list();

    const payments = [];

    for (const key of list.keys) {
        const paymentJson = await env.PAYMENTS.get(key.name);
        if (paymentJson) {
            payments.push(JSON.parse(paymentJson));
        }
    }

    return jsonResponse({
        success: true,
        count: payments.length,
        payments
    });
}

/**
 * Handle Stripe webhook
 */
async function handleStripeWebhook(request, env) {
    const payload = await request.text();
    const sig = request.headers.get('stripe-signature');

    // Verify signature (in production, use Stripe library)
    // For now, just parse the event

    const event = JSON.parse(payload);

    // Handle different event types
    switch (event.type) {
        case 'payment_intent.succeeded':
            const paymentIntent = event.data.object;
            console.log('Payment succeeded:', paymentIntent.id);

            // Find payment by metadata
            const paymentId = paymentIntent.metadata?.payment_id;

            if (paymentId) {
                // Confirm payment automatically
                const paymentJson = await env.PAYMENTS.get(paymentId);
                if (paymentJson) {
                    const payment = JSON.parse(paymentJson);
                    payment.status = 'confirmed';
                    payment.confirmed_at = new Date().toISOString();
                    payment.stripe_payment_intent = paymentIntent.id;
                    await env.PAYMENTS.put(paymentId, JSON.stringify(payment));
                }
            }
            break;

        case 'payment_intent.payment_failed':
            console.log('Payment failed:', event.data.object.id);
            break;

        default:
            console.log('Unhandled event type:', event.type);
    }

    return jsonResponse({ received: true });
}

/**
 * Handle Coinbase Commerce webhook
 */
async function handleCoinbaseWebhook(request, env) {
    const event = await request.json();

    console.log('Coinbase webhook:', event);

    // Handle charge events
    if (event.type === 'charge:confirmed') {
        const charge = event.data;
        const paymentId = charge.metadata?.payment_id;

        if (paymentId) {
            const paymentJson = await env.PAYMENTS.get(paymentId);
            if (paymentJson) {
                const payment = JSON.parse(paymentJson);
                payment.status = 'confirmed';
                payment.confirmed_at = new Date().toISOString();
                payment.coinbase_charge_id = charge.id;
                await env.PAYMENTS.put(paymentId, JSON.stringify(payment));
            }
        }
    }

    return jsonResponse({ received: true });
}
