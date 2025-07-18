update user_balance_change_model
set id=txid_current() - 1
where user_balance_change_model.id > txid_current()
