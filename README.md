# Inside Sales Smart Hub V16

**Inbound:** e-mail / WhatsApp / service-call demand is processed automatically in background and goes directly to Salesforce **Identify → Workflow**.

**Filipe Growth:** proactive outreach → customer reply → **Interaction Validation** → seller assigned by **Commercial Load Index** → human reviews full conversation → **Validate & Create Opportunity** or **Keep / Dismiss as Growth**. Only after human validation is the OPP created. The OPP preserves the full conversation, AI summary and human qualification note.

**Activity & Salesforce Sync:** moved from the middle of the Executive Dashboard to its own navigation page.

All demo data are fictitious.


## V16.1 — Cross Sell / Up Sell recommendation completion
- Suggested item, quantity and unit price now appear automatically when the Opportunity Editor opens.
- The seller can edit suggested quantity and price.
- The optional recommendation only changes the projected opportunity value and proposal after the seller checks **Add recommendation to proposal**.
- The same behavior applies in Workflow and FUP.


## V16.2 — Interaction Validation visibility
- Executive Dashboard now shows **Filipe — Interaction Validation** directly below Automatic Inbound Intake.
- The section follows the selected Owner filter.
- Example: when **Ana** is selected, only Filipe interactions assigned to Ana by Commercial Load Index are shown.
- The summary includes customer, Growth type, estimated potential, assigned validator, Commercial Load Index, received date and status.
- Selecting the interaction shows the **full Filipe ↔ customer conversation** and AI Summary.
- If the selected seller has no pending validation, no fictitious case is invented; the section shows `No interactions pending validation for this seller.`
- Final action remains governed in the dedicated **Interaction Validation** report.
