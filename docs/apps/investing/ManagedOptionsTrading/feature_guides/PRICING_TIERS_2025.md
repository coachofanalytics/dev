# Managed Options Trading – Pricing Tiers (November 2025)

_Goal: preserve the legacy $420 sleeve for the existing client while introducing upgrade paths that justify Unusual Whales / OptionPlay spend and reward higher capital allocations._

---

## Legacy Plan (Grandfathered)

| Plan | Monthly Target | Capital Sleeve | Fees | Notes |
| --- | --- | --- | --- | --- |
| **Consultative 420** | $420 | ~\$18K Core Income | $149 management + 10% performance over 8% hurdle | Existing client only. UW Pro not included; use weekly UW pass when rebalancing. |

---

## New Public Tiers

| Plan | Monthly Target | Capital Allocation | Data Usage | Fees | Deliverables |
| --- | --- | --- | --- | --- | --- |
| **Balanced 900** | $900 | 60% Core Income · 30% Momentum · 10% Events | UW Trial weeks (2/mo), OptionPlay automation twice daily | $249 management + 12% performance (6% hurdle) | Auto-ranked portfolio preset, SMS alerts, monthly sleeve report |
| **Elite 1800** | $1,800+ | 50% Core · 30% Momentum · 20% Events (earnings-driven) | UW Pro continuous, OptionPlay automation, premium alert channel | $399 management + 18% performance (5% hurdle) | Portfolio auto-entry when broker API ready, weekly performance review, premium alerts |

### Optional Add-ons
- **Portfolio Auto Entry**: +$99/mo once Schwab execution is live.  
- **Real-time UW Desk Alerts (SMS/WhatsApp)**: +$49/mo if clients want live signal notifications.

---

## Operational Playbook

1. **Keep the legacy client on the $420 arrangement** (no pricing changes).  
2. **Pitch upgrades** using the new tiers—highlight increased income targets, additional sleeves, automation, and tighter UW access.  
3. **UW Cost Management**  
   - Balanced: activate the $50 UW weekly pass only during scheduled rebalance weeks (default: 1st & 3rd Mondays).  
   - Elite: maintain full UW Pro subscription and charge the higher management/performance fees accordingly.  
4. **Portfolio Presets**  
   - Generate “Core / Balanced / Aggressive” presets weekly.  
   - Map them to the tiers above so sales conversations align with live automation.  
5. **Reporting**  
   - Track sleeve performance separately (Core vs Momentum vs Events).  
   - Expose upgrade value in client dashboards (e.g., “Estimated income at Balanced tier: $900/mo”).  

---

## Client-Facing Narrative (Phase 3 ✅)

- **Automation proof**: the client portal now displays the same 90-day auto-approval metrics (win rate, realized P&L, execution lag) that staff sees.  
- **Upgrade CTA**: legacy clients see an inline upgrade card referencing those metrics plus the Balanced/Elite deliverables.  
- **Plan comparison table**: the tier matrix is rendered directly in the portal so “why pay more?” is answered with live data.  
- **Source of truth**: all metrics pull from `PositionRankingService.get_auto_approval_metrics()` to keep staff + client copy in sync.

---

## Next Engineering Tasks

1. Add configuration for plan-to-sleeve mapping and UW subscription cadence (currently hard-coded).  
2. Wire portfolio auto-entry once Schwab broker API access is granted (Balanced/Elite).  
3. Extend the scenario explorer to reference the new presets / automation stats.

_Document owner: Investing Engineering • Last updated: Nov 14, 2025_



