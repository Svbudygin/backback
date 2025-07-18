The **TEAM_STATEMENT_RECEIVED** alert notifies support when a team uploads a bank statement after an appeal has been declined.

It is triggered by the `upload_team_statement` endpoint once the statement is successfully saved and the appeal contains a `reject_reason`.

The notification payload includes:
- `appeal_id`
- `transaction_id`
- `merchant_transaction_id`
- `merchant_appeal_id`
- `reject_reason`
- `file_ids` – identifiers of the uploaded files

Support receives this alert so they can review the new documents and close out the declined appeal if necessary.
