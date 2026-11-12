# AGENTS.md — SWD Banking implementation guide

## Purpose and source precedence

This file is the working implementation guide for the Django B2C retail banking project. It summarizes the current design and rules for coding agents; it is not a replacement for the assignment or the team's report.

Use evidence labels in code reviews and design decisions:

- **Assignment requirement**: mandatory only when verified against the original assignment brief.
- **Team report**: what Project Document v1.3 currently says; it may contain outdated text.
- **User-reported instructor clarification**: the user's later account of instructor decisions; it supersedes conflicting v1.3 wording.
- **Diagram/design proposal**: the current class or component design; method names and technical choices are not automatically requirements.
- **Recommendation / assumption**: implementation advice or a choice that still needs confirmation. Label it as such.

The project instructions give this precedence: original assignment for exact mandatory requirements; instructor clarifications in `Banking_Project_Knowledge_v1_3.md` over conflicting v1.3 report text; report and diagrams for remaining team design. At the time this guide was prepared, the PDF, knowledge file, and original assignment were not present in this workspace. Consult them if they are added before resolving a conflict; do not invent their contents.

## Project overview

Build a simulated Django-based retail banking system for private customers. The design covers customer and account management, cash operations, transfers (including interbank transfers), securities trading, statements and transaction history, and monthly-interval standing orders. User interaction may occur through net banking, a bank office, or a simulated ATM. Market prices come from an external API boundary. This is a software-design project: implement only the scope supported by the assignment and current clarifications.

Current workspace contents are design artifacts and diagram-generation files, not an established Django application structure. Inspect the repository before assuming app names, existing models, database, deployment setup, or API provider.

## Current design artifacts

- `Banking_Class_Diagram_Revised.drawio`: four class-diagram pages — Customers & Accounts; Transactions & Statements; Investments & Standing Orders; Services & Use Cases.
- `Banking_CD_Revised_Component_Assignment.drawio`: class diagram with class-owner annotations and a Component Responsibilities overview.
- `Banking_Diagram_Revision_Notes.md`: domain decisions, proposed method contracts, traceability, and unresolved design points. Treat proposed signatures as design guidance, not approved APIs.
- `Banking_Component_Assignment_Notes.md`: class-to-component ownership rationale.
- `Stock_Purchase_Sequence.drawio`: proposed purchase flow and concurrency/rollback behavior.
- `Withdraw_Cash_Activity_Three_Tabs.drawio`: withdrawal activity flow.

The component architecture is centered on **Transactionmanagement**. Do not restore the earlier Core/Payments component draft unless the user explicitly asks to revisit the architecture.

## Components and ownership

| Component | Primary service | Main responsibility and owned classes |
|---|---|---|
| Customers | `CustomerService` | Bank, BankBranch, Person, Employee, Customer, CustomerGroup; identity records and customer registration. |
| Account | `AccountService` | Account, CheckingAccount, SavingsAccount, CustodyAccount, PurchasedStock; account rules, ownership, balances, reference accounts and holdings. |
| Transactionmanagement | `TransactionManagementService` | PaymentOperation, PaymentKind, StockTrade, TradeType; coordinates complete financial operations and commits them atomically. |
| Statements & Transaction History | `StatementService` | Transaction and Statement; per-account postings, statement association, balances and history. |
| Stock Market | `StockMarketService` | Stock and `MarketDataGateway`; tradable stock data and quotes from the external market-data API. |
| Standing Orders / Scheduler | `StandingOrderService` | StandingOrder and StandingOrderScheduler; persist instructions, select due orders and delegate execution. |

`AuditService` is shared support grouped under Transactionmanagement because no audit component exists in the accepted component diagram. `SimulatedCashDispenser` is a simulation boundary, not ATM hardware. Django ORM and the database are persistence infrastructure, not business owners. A separate Repository layer is not required by this design.

### Collaboration flow

- `TransactionManagementService` orchestrates transfers, cash operations and stock trades; it asks `AccountService` to enforce account rules, `StockMarketService` for stock/quote data when needed, `StatementService` to create/associate local postings, and shared audit support to record outcomes.
- `StandingOrderScheduler` selects due instructions and delegates to `StandingOrderService`; execution uses `TransactionManagementService.transfer` so normal transfer rules still apply.
- `CustomerService.registerCustomer` participates in the office account-opening operation so a new persistent customer and first account are created together.

## Domain model from the class diagram

- `Person` is the shared identity superclass; `Customer` and `Employee` derive from it. `Bank` stores institution identity and its unique BIC. `BankBranch` is optional office-location data retained from the original model; its BIC is proposed as derived from `Bank.bic`, not as a distinct branch BIC.
- `Customer` owns one or more accounts. `Account` is abstract; `CheckingAccount`, `SavingsAccount`, and `CustodyAccount` are complete and disjoint types.
- Checking and savings accounts hold cash. Checking accounts may have a permitted overdraft. Savings transfers use only their linked reference checking account. A custody account holds `PurchasedStock` lots and a reference checking account; it has no cash balance.
- `PaymentOperation` represents the overall payment/trade-settlement operation. `Transaction` is a separate saved posting for one local account and is associated with that account's statement. One internal transfer has two postings committed together; cash operations, external transfers, and trade settlements have one local posting in this model. External counterparties are IBAN/BIC metadata, not local `Account` objects. The exact external interbank ledger boundary remains unresolved.
- `Statement` covers a date period and owns no single payment value date. Each `Transaction.valueDate` determines its statement period. `StockTrade` records immutable completed buy/sell history; `PurchasedStock` records a purchase lot and its remaining quantity.
- `StandingOrder` is a persisted instruction, not a reserved balance or completed payment. It references a checking source and an eligible target account.

## Rules and their status

The project instructions explicitly report these later instructor clarifications; treat them as authoritative over conflicting v1.3 wording: interbank transfers are included; custody accounts have no cash balance and cash settlement uses checking accounts; standing orders cannot target custody accounts and their frequency is a month interval; the ATM is simulated; market data comes from an API; and the latest reported stock rule limits successful BUYs by ISIN/day. The exact scope and day boundary of that last rule still needs the knowledge file.

Other constraints below are from the current diagrams/revision notes or are implementation recommendations, not independently verified assignment requirements. Preserve them as the current design unless an instructor clarification or source document says otherwise.

### Diagram/revision-note design: money, accounts, and transaction safety

- Use decimal money values (`Decimal` / Django `DecimalField`), never binary floating point for persisted money or prices.
- Require positive amounts for debit/credit operations. A debit must respect the account's permitted lower bound; only checking-account overdraft policy can permit a negative balance.
- Wrap each financial operation in a database transaction. Lock/check affected account balances and relevant inventory while executing, then revalidate under lock. Internal transfer debit, credit, both postings, statement updates and operation record must commit or roll back together.
- Make retries safe with a trusted request ID/idempotency key. Standing-order execution additionally needs a deduplication identity based on order and scheduled date.
- Do not use custody accounts for cash settlement. Stock settlements debit or credit the linked checking account.
- Overdraft limits are not settled by this guide. The project's proposed 300% of salary example is not an established Austrian average or an instructor-approved rule; do not hard-code it as policy.

### Clarification plus diagram design: transfers and cash

- Interbank transfers are in scope according to the user-reported clarification. Validate source ownership, account eligibility, amount and permitted funds. Store external destination IBAN/BIC as counterparty data; do not fabricate a second local account posting for an external institution. Keep the unresolved ledger boundary explicit.
- Cash withdrawals use checking accounts only and support OFFICE and ATM channels. The simulated ATM requires its selected institution BIC to match the checking account's bank. Never model a real ATM integration.
- A failed simulated cash payout must not leave a lasting debit, transaction posting, or statement change. Record an audit outcome that survives financial rollback.

### Clarification plus diagram design: securities

- Retrieve quotes through `MarketDataGateway`; keep provider-specific response parsing outside domain logic. An adapter that maps API payloads to domain quote/stock values is a recommendation, not a selected provider or mandated pattern. No API provider has been confirmed here.
- Before purchase, check positive quantity, stock availability, checking funds, customer confirmation against the displayed price, and the latest reported successful-BUY-per-ISIN/day rule. The exact uniqueness scope/day boundary should be verified from the knowledge file; do not silently broaden it to all customers or narrow it to one account.
- Recheck funds, stock quantity and the daily rule while locks are held. Commit the checking debit, stock inventory change, `PurchasedStock` lot, immutable `StockTrade`, `PaymentOperation`, local `Transaction`, statement update and audit outcome consistently. A failed attempt must not leave financial or holdings changes.
- A partial sale reduces `PurchasedStock.remainingQuantity`; never rewrite its original `purchaseQuantity`. Record a new SELL `StockTrade` with the sold quantity and execution price, credit the linked checking account and write the corresponding posting atomically.
- Local stock quantity/inventory is a diagram proposal. Stock replenishment, lot-allocation policy, quote freshness, fees/tax, fractional shares and custody reporting details remain open unless the source documents settle them.

### Diagram/revision-note design: statements and transaction history

- Each posting belongs to exactly one local account and one statement. An internal transfer therefore creates two separate `Transaction` records, not one multi-account posting.
- Associate postings with the account's single open statement whose inclusive date range contains `Transaction.valueDate`; prevent duplicate inclusion and update credit/debit counts, totals and closing balance consistently.
- Closing a statement validates/finalizes its balance and freezes it. Keep predecessor/opening/closing balance continuity. Custody is reported as securities/holdings, not a cash statement unless the project decisions explicitly add that design.

### Clarification plus diagram design: standing orders and onboarding

- `frequency` means an integer number of months, at least one. Do not reinterpret it as days or a calendar enum.
- A standing-order source must be a checking account. A target may be an eligible same-bank checking or savings account; savings must reference the source checking. Custody accounts are never valid targets.
- Creating or editing an order does not move or reserve money. At execution, check active/due/end-date state, lock/deduplicate the scheduled run, and execute an ordinary transfer. Advance the next date only after success. Month-end, missed-run and retry/calendar policies remain unresolved; do not invent a policy.
- Account opening is an OFFICE action. If opening a new customer, customer registration and the first account must succeed or roll back together. Checking/savings start at zero; custody starts with no cash and no lots. Required reference checking rules must be enforced.

## Django implementation guidance

These are implementation recommendations consistent with the diagrams:

- Keep HTTP views/API endpoints thin. Put use-case orchestration in services named for the component responsibilities above; put local invariants on account/statement/lot domain methods where appropriate.
- Use `transaction.atomic()` and row-level locking (`select_for_update`) for balance, stock inventory, statement and standing-order execution paths. Add database constraints for uniqueness and idempotency where practical; application checks alone are insufficient under concurrency.
- Treat API input as untrusted. Resolve the authenticated actor, ownership, channel and request ID in trusted middleware/service context; callers must not choose their own authorization identity. Authorize customer self-service versus staff-only OFFICE actions at the service boundary.
- Audit every persisted write and rejected financial attempt. Keep failed-attempt audit records outside the transaction that rolls back financial changes. Never log PINs, passwords, tokens or other credentials.
- Prefer stateless Django services; do not introduce Singleton patterns for service classes by default. Run scheduled work through an explicit scheduler/management command or configured worker, with execution locking and idempotency. This is a recommendation, not a change to the component design.
- Add focused tests for account invariants, atomic rollback, concurrency/idempotency, statements, market-data mapping and due-order execution when implementing the corresponding feature. Do not claim a design proposal is instructor-approved solely because it appears in a diagram.

## Unresolved decisions — keep visible

Verify these against `Banking_Project_Knowledge_v1_3.md` or ask before choosing a policy: exact interbank ledger/settlement boundary; scope and day boundary of the ISIN/day purchase restriction; standing-order month-end/missed-run/retry rules; quote freshness/provider; fees/taxes/fractional-share support; stock inventory replenishment; custody statement/report format; overdraft policy; and any exact external settlement states. Branch-specific BICs are not specified; do not invent them.

## Guidance for future agents

Before changing a model or use case, inspect the relevant class/component diagram and `Banking_Diagram_Revision_Notes.md`. Preserve the accepted Transactionmanagement-centered architecture. State whether a claim comes from the assignment, team report, user-reported instructor clarification, diagram proposal, external evidence, or assumption. If a diagram conflicts with a later confirmed rule, follow the confirmed rule and document the proposed diagram correction; do not silently reintroduce old Core/Payments wording or unsupported requirements.
