# Разбор всех 16 access-control файлов

AI-assisted анализ фактических исходников и авторских тестов; не доказательства защищённости. Исторические предложения и source/test hashes — в registry.json.


## FibonacciBalance.sol

Track: unresolved; group: FibonacciBalance.sol

Защищаемый объект: Library pointer and exact Fibonacci payout

Модель полномочий: Public withdraw; fallback explicitly permits library calls; no owner role

Дефект авторского теста: Delegatecall с несогласованным storage layout и изменяемым адресом библиотеки

Существующие механизмы: require on delegatecall success; no caller restriction; mutable library pointer via mismatched fallback storage

Решение и ограничения: No resolved policy for setStart or allowed selectors; isolated computation changes shared-library workflow/storage layout. Need exact sequence and permitted fallback API before architecture comparison.


## arbitrary_location_write_simple.sol

Track: factorial; group: arbitrary_location_write_simple.sol

Защищаемый объект: owner slot1 and bounded dynamic array

Модель полномочий: Any user may push/pop/update valid index; only deployer may Destroy

Дефект авторского теста: Уменьшение длины пустого массива и последующая порча чужого storage

Существующие механизмы: Update bounds guard, Destroy owner guard

Решение и ограничения: A nonempty pre-guard; B post-result checked subtraction; V3 both. Existing update bound and Destroy owner check retained.


## incorrect_constructor_name1.sol

Track: single; group: AC_INIT_CLONE

Защищаемый объект: Owner slot0 and withdrawal authority

Модель полномочий: Deployer owns at construction; anyone may fund; only owner may withdraw

Дефект авторского теста: Публичная функция инициализации может изменить владельца/creator

Существующие механизмы: onlyowner on withdraw, payable fallback, runtime IamMissing unguarded; no constructor owner init

Решение и ограничения: Replace misnamed initializer with constructor; remove runtime selector. No post-deployment initialization requirement is inferred.


## incorrect_constructor_name2.sol

Track: single; group: AC_INIT_CLONE

Защищаемый объект: Owner slot0 and withdrawal authority

Модель полномочий: Deployer owns at construction; anyone may fund; only owner may withdraw

Дефект авторского теста: Публичная функция инициализации может изменить владельца/creator

Существующие механизмы: onlyowner on withdraw, payable fallback, runtime missing unguarded; no constructor owner init

Решение и ограничения: Replace misnamed initializer with constructor; remove runtime selector. No post-deployment initialization requirement is inferred.


## incorrect_constructor_name3.sol

Track: single; group: AC_INIT_CLONE

Защищаемый объект: Owner slot0 and withdrawal authority

Модель полномочий: Deployer owns at construction; anyone may fund; only owner may withdraw

Дефект авторского теста: Публичная функция инициализации может изменить владельца/creator

Существующие механизмы: onlyowner on withdraw, payable fallback, runtime Constructor unguarded; no constructor owner init

Решение и ограничения: Replace misnamed initializer with constructor; remove runtime selector. No post-deployment initialization requirement is inferred.


## mapping_write.sol

Track: single; group: mapping_write.sol

Защищаемый объект: owner slot0 integrity; arbitrary uint256 key/value storage

Модель полномочий: Public set/get arbitrary keys; withdraw restricted to owner, which remains zero/uninitialized

Дефект авторского теста: Индексируемый динамический массив используется как map; произвольная длина и порча storage

Существующие механизмы: withdraw msg.sender==owner; owner defaults to zero, implicit array bounds in get/set; public length growth can expose other storage

Решение и ограничения: Replace dynamic array with mapping; remove length manipulation only. No key cap or owner initialization. Artificial funding 1 wei disclosed; absent-key get now returns zero instead of possible OOB revert (interface same, behavior extension).


## multiowned_vulnerable.sol

Track: single; group: multiowned_vulnerable.sol

Защищаемый объект: Owner-parent tree and funds

Модель полномочий: Root and delegated owners may add; parent/root may revoke according to existing rule; owners may withdraw

Дефект авторского теста: newOwner не ограничивает вызывающего существующим владельцем

Существующие механизмы: onlyOwner, parent/root deletion rule

Решение и ограничения: Apply existing onlyOwner to newOwner; no new two-step grant workflow. Existing deleteOwner and withdraw guards retained.


## mycontract.sol

Track: single; group: mycontract.sol

Защищаемый объект: Owner-authorized outgoing ETH

Модель полномочий: Deployment owner may directly sendTo any receiver; intermediary does not inherit authority from tx.origin

Дефект авторского теста: Авторизация через tx.origin

Существующие механизмы: constructor sets owner, tx.origin==owner on sendTo (flawed authentication), transfer value failure propagates

Решение и ограничения: Replace tx.origin with msg.sender. Prefund future CREATE address as author test, not artificial owner initialization.


## parity_wallet_bug_2.sol

Track: single; group: parity_wallet_bug_2.sol

Защищаемый объект: First initialization authority, owner set and wallet funds

Модель полномочий: Scoped to author-tested standalone WalletLibrary: deployer initializes; existing owners act under original threshold/daily limit

Дефект авторского теста: Первый initializer доступен постороннему; only_uninitialized уже существует

Существующие механизмы: only_uninitialized on all init entrypoints, onlyowner, onlymanyowners, daily-limit overflow guard

Решение и ограничения: Single missing-authority fix on all 3 init entrypoints; existing only_uninitialized retained. Append private deploymentAuthority after original fields; no storage shift. This is not a proxy-compatible library fix or historical deployment reconstruction.


## phishable.sol

Track: single; group: phishable.sol

Защищаемый объект: Owner-authorized outgoing ETH

Модель полномочий: Constructor-designated owner may directly withdraw to arbitrary receiver; phishing intermediary unauthorized

Дефект авторского теста: Авторизация через tx.origin

Существующие механизмы: constructor sets designated owner, tx.origin==owner on withdrawAll (flawed authentication), payable fallback

Решение и ограничения: Replace tx.origin with msg.sender; payable fallback retained; no recipient allowlist.


## proxy.sol

Track: unresolved; group: proxy.sol

Защищаемый объект: Owner/storage and ETH under delegatecall

Модель полномочий: Constructor sets owner; public forwarding has no explicit target domain

Дефект авторского теста: Публичный forward допускает arbitrary delegatecall target

Существующие механизмы: owner set by constructor but unused in forward, require on delegatecall success; no caller/target policy

Решение и ограничения: No trusted target set or delegated-user policy specified; benign function in attack fixture cannot define a production trust policy. Do not invent allowlist to force A+B.


## simple_suicide.sol

Track: single; group: simple_suicide.sol

Защищаемый объект: Lifecycle code and ETH under Shanghai

Модель полномочий: Author functional test designates deployer as owner; infer deployer-only lifecycle authority for this standalone fixture

Дефект авторского теста: Неограниченное завершение контракта

Существующие механизмы: none; no owner field or lifecycle guard

Решение и ограничения: Add private deployment owner and guard. New authority is an explicit experimental model inferred from functional test, absent in source; no second lifecycle requirement. No-argument ABI used, correcting author JS extra argument only in new measurements.


## unprotected0.sol

Track: single; group: unprotected0.sol

Защищаемый объект: Owner slot0

Модель полномочий: Current owner may transfer ownership to any chosen address; outsiders may not

Дефект авторского теста: Публичный changeOwner без существующего onlyowner

Существующие механизмы: constructor sets owner, onlyowner modifier already declared but not applied to changeOwner

Решение и ограничения: Use existing onlyowner on changeOwner; no acceptance phase or zero-address restriction introduced.


## wallet_02_refund_nosub.sol

Track: single; group: wallet_02_refund_nosub.sol

Защищаемый объект: Per-user claim and ETH accounting

Модель полномочий: Any depositor may withdraw/refund own credit; creator migration remains allowed

Дефект авторского теста: Повторная выплата из-за отсутствия списания credit

Существующие механизмы: withdraw entitlement, creator-only migration, deposit assertion

Решение и ограничения: Set credit zero before refund transfer (accounting/CEI fix); allow zero refund as harmless no-effect success; sequential repeats must not pay again; no mutex/owner restriction.


## wallet_03_wrong_constructor.sol

Track: single; group: wallet_03_wrong_constructor.sol

Защищаемый объект: Creator slot0 and migration authority

Модель полномочий: Deployer is creator at construction; each depositor withdraws own credit; only creator migrates

Дефект авторского теста: Публичная функция инициализации может изменить владельца/creator

Существующие механизмы: deposit overflow assert, withdraw amount<=credit and debit, creator check on migrateTo, initWallet lacks authority/once; no constructor creator init

Решение и ограничения: Replace initWallet with constructor, remove runtime init selector. This is a lifecycle/API correction, not comparison of artificial post-deploy guards.


## wallet_04_confused_sign.sol

Track: factorial; group: wallet_04_confused_sign.sol

Защищаемый объект: Deposit credit and ETH entitlement

Модель полномочий: Each depositor may withdraw 0..credit; creator may migrate all funds

Дефект авторского теста: Неправильное направление проверки entitlement и возможный underflow

Существующие механизмы: Wrong reversed entitlement guard, Creator-only migration, Deposit overflow assertion

Решение и ограничения: A replaces reversed >= with <=; B checked debit only, preserving reversed guard. V2 inherits rejection of partial/zero-with-credit withdrawals. V3 expected to restore domain via A, not independent synergy.
