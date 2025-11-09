# Charles Schwab API Onboarding Guide

_Status: Draft – November 2025_

This runbook walks CODA staff through enabling Charles Schwab trading APIs so our managed options service can place orders automatically. Follow the steps in order and involve the Schwab relationship manager where noted.

---

## 1. Prerequisites & Contacts

| Item | Notes |
| --- | --- |
| **Account Program** | Schwab Advisor Services (Institutional) with trading authority for CODA Managed Options. |
| **Primary Contact** | Institutional relationship manager or API support desk (api@schwab.com / 877-xxx-xxxx). |
| **Authorized Signers** | Ensure the CODA principals listed on the master agreement can sign API paperwork. |
| **Technical Contact** | Automation engineering alias (devops@codanalytics.net) for webhook/IP updates. |

---

## 2. Paperwork Checklist

1. **Digital Services Agreement** – request the “Schwab Advisor Center API Addendum.”  
2. **Trading Authorization** – confirm discretionary trading authority is on file for each managed account.  
3. **Data Security Questionnaire** – Schwab may require a security profile outlining encryption, audit logging, and access controls. Prepare a short summary of our encryption (TokenEncryptionService) and least-privilege admin roles.  
4. **Callback IP Whitelisting** – compile the public IPs of our production/UAT environments if Schwab requires firewall rules.

Pro tip: keep signed PDFs in the secure compliance vault (`/Shared/Compliance/Broker Agreements/Schwab/`).

---

## 3. Obtain API Credentials

Schwab uses an OAuth 2.0 flow. After the paperwork clears:

1. Log into **Schwab Advisor Center** → _Menu_ → **Third-Party Integrations** → **API Access**.  
2. Click **Create New Application** and provide:
   - **Application Name:** `CODA Managed Trading`  
   - **Redirect URI:**  
     - UAT: `https://uat.codanalytics.net/investing/api/schwab/oauth/callback/`  
     - Production: `https://www.codanalytics.net/investing/api/schwab/oauth/callback/`  
   - **Allowed IPs:** list Heroku dyno outbound ranges if requested (Schwab sometimes allows “ANY” with auth throttling).  
3. Save the generated **Client ID** and **Client Secret**. Schwab may also provide an **App Key** for sandbox environments.

> ⚠️ Treat the secret like a password. Paste it only into our encrypted admin form (next section) and the secure credential vault.

---

## 4. Register Credentials in CODA Admin

1. Visit `https://www.codanalytics.net/admin/investing/brokerconnection/`.  
2. Add a new **Broker Connection**:
   - **Managed account:** select the client account.  
   - **Broker:** `schwab`.  
   - **API Key / Secret:** paste the Client ID and Client Secret. The form encrypts values at rest and stores the last 4 digits only.  
   - **Meta:** optionally note which Schwab rep approved the integration.  
   - Set **Is Active** = Yes and **Is Featured** if this is the primary execution venue.  
3. Click **Save**. The connection is immediately available to services that call `BrokerAPIService`.

---

## 5. OAuth Handshake Test

1. From the staff console, navigate to `Managed Accounts → Schwab Account → Actions → “Sync Broker Positions”`.  
2. You will be redirected to Schwab’s consent screen; authorize the application using advisor credentials.  
3. Confirm callback success (browser displays “Broker sync requested” message).  
4. In Heroku logs (`heroku logs --tail --app codatrainingapp`), verify we receive an access token and refresh token. Tokens are stored encrypted on the `BrokerConnection`.

If the redirect fails, double-check the redirect URI matches exactly in Schwab’s portal (case-sensitive, trailing slash required).

---

## 6. Order Placement Mapping

| CODA Field | Schwab API Field | Notes |
| --- | --- | --- |
| `OptionsPosition.symbol` | `symbol` | Use OCC format (e.g., `AAPL` for underlying). |
| `strategy` | `orderStrategyType` | `SINGLE`, `SPREAD`, `IRON_CONDOR`, etc. |
| `positions` JSON legs | `orderLegCollection` | Map each leg’s action (`BUY_TO_OPEN`, `SELL_TO_OPEN`) and quantity. |
| `premium_collected` | `price` / `orderType` | Use `NET_CREDIT` or `NET_DEBIT` orders, price in dollars. |
| `capital_required` | Validation only | Set `orderCapacity` = `AGENCY` for advisor trades. |

Implementation TODOs:

- Build `SchwabBrokerClient` inside `coda/investing/services/broker_api/schwab_client.py`.  
- Calculate spread net price and assign `duration` (`DAY` or `GOOD_TILL_CANCEL`).  
- Support pre-trade compliance checks (exposure, buying power) before sending `POST /v1/trader/orders`.  
- Capture Schwab order IDs and store them on `OptionsPosition.api_response_data`.

---

## 7. Operational Safeguards

- **Twilio Alerts:** confirm the desk receives SMS/WhatsApp when an order posts or fails.  
- **Audit Trail:** ensure each order logs a `TradingActivity` entry with Schwab order ID and timestamp.  
- **Failover:** if Schwab API is unavailable, queue orders for manual execution and notify ops.

---

## 8. Go-Live Checklist

1. ✅ Paperwork approved  
2. ✅ API credentials stored in admin  
3. ✅ OAuth token retrieved and refresh verified  
4. ✅ Test order submitted in Schwab demo environment and appears under Open Orders  
5. ✅ Twilio alerts received by trading desk  
6. ✅ Documentation signed off by compliance

Once all boxes are checked, we can flip the “Enable Auto-Entry” toggle for Schwab-connected accounts.

